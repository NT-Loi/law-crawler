from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool
from pydantic import BaseModel

from rag import RAG

import json
from typing import List, Optional, Any, AsyncGenerator
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    mode: str = "chain"  # "agent" or "chain"

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]

chat_model = os.getenv("CHAT_MODEL")
base_url = os.getenv("URL")
api_key = os.getenv("API_KEY")

class ChainChat:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=chat_model,
            temperature=0.2,
            max_tokens=2048,
            streaming=True
        )
        logging.info(f"Initialized ChainChat with {chat_model} at {base_url}")

    async def chat(self, message: str, history: List[dict], rag_engine: RAG) -> AsyncGenerator[str, None]:
        """
        Classic RAG flow: 
        1. Retrieve Documents (Deterministic)
        2. Build Context
        3. Stream Answer
        """
        try:
            query = message
            sources = rag_engine.retrieve(query)
            # reranked_sources = rag_engine.rerank(query, sources)
            
            yield json.dumps({"type": "sources", "data": sources}, ensure_ascii=False) + "\n"

            docs_text = "\n\n".join([f"Document {i+1}:\n{doc['content']}" for i, doc in enumerate(sources)])
            
            system_prompt = (
                "Bạn là trợ lý pháp luật. Trả lời câu hỏi dựa trên các văn bản pháp luật được cung cấp dưới đây.\n"
                "Nếu thông tin không có trong văn bản, hãy nói là bạn không biết.\n\n"
                f"--- VĂN BẢN PHÁP LUẬT ---\n{docs_text}"
            )
            
            messages = [SystemMessage(content=system_prompt)]
            
            for h in history[-2:]:
                role = h.get("role")
                content = h.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
            
            messages.append(HumanMessage(content=message))

            try:
                async for chunk in self.llm.astream(messages):
                    if chunk.content:
                        yield json.dumps({"type": "content", "delta": chunk.content}, ensure_ascii=False) + "\n"
            except Exception as e:
                # Fallback if max_tokens exceeds context limit
                if "max_tokens" in str(e) and "too large" in str(e):
                    logging.warning(f"Token limit exceeded. Sending warning and retrying with SAFE MODE (max_tokens=512).")
                    
                    # 1. Notify Frontend
                    yield json.dumps({
                        "type": "warning", 
                        "message": "Hội thoại đã đạt giới hạn bộ nhớ. Đang chuyển sang chế độ trả lời ngắn gọn. Vui lòng tạo hội thoại mới để tiếp tục tốt hơn."
                    }, ensure_ascii=False) + "\n"

                    # 2. Retry with minimal tokens
                    try:
                        async for chunk in self.llm.bind(max_tokens=512).astream(messages):
                            if chunk.content:
                                yield json.dumps({"type": "content", "delta": chunk.content}, ensure_ascii=False) + "\n"
                    except Exception as inner_e:
                        logging.error(f"Safe mode also failed: {inner_e}")
                        yield json.dumps({
                            "type": "content", 
                            "delta": "\n\n[Hệ thống: Không thể tạo câu trả lời vì văn bản quá dài. Vui lòng làm mới trang hoặc tạo hội thoại mới.]"
                        }, ensure_ascii=False) + "\n"
                else:
                    raise e

        except Exception as e:
            logging.error(f"Error in chain chat: {e}")
            yield json.dumps({"type": "content", "delta": f"Error: {str(e)}"}, ensure_ascii=False) + "\n"


class ChatAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=chat_model,
            temperature=0.2,
            max_tokens=2048,
            streaming=True
        )
        logging.info(f"Initialized ChatAgent with {chat_model} at {base_url}")

    async def chat(self, message: str, history: List[dict], rag_engine: RAG) -> AsyncGenerator[str, None]:
        """
        Agentic chat flow that yields NDJSON events.
        Decides dynamically whether to search or just chat using a Router step.
        (Replaces native tool usage to avoid 'auto' tool choice errors on vLLM without flags)
        """
        try:
            # Step 1: Router - Decide if we need to search
            router_messages = self._build_router_messages(message, history)
            
            # Non-streaming call for routing
            route_response = await self.llm.ainvoke(router_messages)
            route_content = route_response.content.strip()
            
            logging.info(f"Router decision: {route_content}")
            
            search_query = None
            if "SEARCH:" in route_content:
                parts = route_content.split("SEARCH:", 1)
                if len(parts) > 1:
                    search_query = parts[1].strip()

            # Step 2: Execute Tool if needed
            context_text = ""
            if search_query:
                logging.info(f"Agent executing search for query: {search_query}")
                sources = rag_engine.retrieve(search_query)
                yield json.dumps({"type": "sources", "data": sources}, ensure_ascii=False) + "\n"
                
                if sources:
                    context_text = "\n\n".join([f"Document {i+1}:\n{doc['content']}" for i, doc in enumerate(sources)])
            
            # Step 3: Final Response
            final_messages = self._build_final_messages(message, history, context_text)
            
            try:
                async for chunk in self.llm.astream(final_messages):
                    if chunk.content:
                        yield json.dumps({"type": "content", "delta": chunk.content}, ensure_ascii=False) + "\n"
            except Exception as e:
                # Fallback if max_tokens exceeds context limit
                if "max_tokens" in str(e) and "too large" in str(e):
                    logging.warning(f"Token limit exceeded. Sending warning and retrying with SAFE MODE (max_tokens=512).")
                    
                    # 1. Notify Frontend
                    yield json.dumps({
                        "type": "warning", 
                        "message": "Hội thoại đã đạt giới hạn bộ nhớ. Đang chuyển sang chế độ trả lời ngắn gọn. Vui lòng tạo hội thoại mới để tiếp tục tốt hơn."
                    }, ensure_ascii=False) + "\n"

                    # 2. Retry with minimal tokens
                    try:
                        async for chunk in self.llm.bind(max_tokens=512).astream(final_messages):
                            if chunk.content:
                                yield json.dumps({"type": "content", "delta": chunk.content}, ensure_ascii=False) + "\n"
                    except Exception as inner_e:
                        logging.error(f"Safe mode also failed: {inner_e}")
                        yield json.dumps({
                            "type": "content", 
                            "delta": "\n\n[Hệ thống: Không thể tạo câu trả lời vì văn bản quá dài. Vui lòng làm mới trang hoặc tạo hội thoại mới.]"
                        }, ensure_ascii=False) + "\n"
                else:
                    raise e

        except Exception as e:
            logging.error(f"Error in chat agent: {e}")
            yield json.dumps({"type": "content", "delta": f"Error: {str(e)}"}, ensure_ascii=False) + "\n"

    def _build_router_messages(self, query: str, history: List[dict]) -> List[BaseMessage]:
        system_prompt = (
            "Bạn là một bộ định tuyến thông minh (Router) cho trợ lý pháp luật.\n"
            "Nhiệm vụ: Phân tích câu hỏi của người dùng và lịch sử trò chuyện để quyết định xem có cần QUYỀN TRA CỨU thông tin pháp luật hay không.\n"
            "Chỉ trả lời theo định dạng sau:\n"
            "- Nếu cần tìm kiếm: `SEARCH: <từ khóa tìm kiếm ngắn gọn>`\n"
            "- Nếu không cần tìm kiếm (chào hỏi, chat xã giao, hoặc đã có đủ thông tin): `NO_SEARCH`\n"
            "Ví dụ:\n"
            "User: Xin chào\n"
            "Output: NO_SEARCH\n"
            "User: Nghĩa vụ quân sự là gì?\n"
            "Output: SEARCH: Nghĩa vụ quân sự\n"
        )
        msgs = [SystemMessage(content=system_prompt)]
        # We limit history for router to avoid noise, just last interaction
        if history:
            last_msg = history[-1]
            role = last_msg.get("role")
            content = last_msg.get("content", "")
            if role == "user":
                msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                msgs.append(AIMessage(content=content))
        
        msgs.append(HumanMessage(content=query))
        return msgs

    def _build_final_messages(self, query: str, history: List[dict], context: str = "") -> List[BaseMessage]:
        system_prompt = (
            "Bạn là trợ lý pháp luật AI chuyên nghiệp.\n"
        )
        
        if context:
            system_prompt += (
                "Dưới đây là các thông tin pháp luật tìm được:\n"
                f"--- VĂN BẢN PHÁP LUẬT ---\n{context}\n\n"
                "Hãy trả lời câu hỏi dựa trên các thông tin trên. Nếu không đủ thông tin, hãy nói rõ."
            )
        else:
            system_prompt += (
                "Hãy trả lời câu hỏi của người dùng một cách tự nhiên. "
                "Nếu câu hỏi yêu cầu kiến thức pháp luật cụ thể mà bạn không biết, hãy xin lỗi."
            )

        msgs = [SystemMessage(content=system_prompt)]
        
        for h in history[-2:]:
            role = h.get("role")
            content = h.get("content", "")
            if role == "user":
                msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                msgs.append(AIMessage(content=content))
        
        msgs.append(HumanMessage(content=query))
        return msgs