from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse
import json
import os
from contextlib import asynccontextmanager

from database import engine, get_async_session
from rag import RAGEngine
from llm_service import GeminiService, OllamaService

# --- Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize components
    app.state.rag = RAGEngine()
    # Choose LLM based on env
    if os.getenv("GEMINI_API_KEY"):
        app.state.llm = GeminiService()
    else:
        app.state.llm = OllamaService()
    yield

app = FastAPI(title="Vietnamese Law RAG Chatbot", lifespan=lifespan)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "ok", "message": "Law RAG API is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    # 1. Retrieve context
    context_nodes = await app.state.rag.retrieve(request.message)
    context_text = app.state.rag.format_context(context_nodes)
    
    async def response_generator():
        # Send sources immediately
        yield json.dumps({"type": "sources", "data": context_nodes}, ensure_ascii=False) + "\n"
        
        # Stream LLM response
        async for chunk in app.state.llm.stream_response(request.message, context_text):
            yield json.dumps({"type": "content", "delta": chunk}, ensure_ascii=False) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")

@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    # Fetch full document structure from PostgreSQL
    from sqlalchemy import text
    with engine.connect() as conn:
        # 1. Try VBQPPL Doc
        doc = conn.execute(text("SELECT * FROM vbqppl_docs WHERE id = :id"), {"id": doc_id}).fetchone()
        if doc:
            nodes = conn.execute(text("SELECT * FROM vbqppl_nodes WHERE doc_id = :id ORDER BY id"), {"id": doc_id}).fetchall()
            return {
                "metadata": dict(doc._mapping),
                "content": [dict(n._mapping) for n in nodes]
            }
            
        # 2. Try Phap Dien Node
        pd_node = conn.execute(text("SELECT * FROM phapdien_nodes WHERE id = :id"), {"id": doc_id}).fetchone()
        if pd_node:
            return {
                "metadata": {
                    "id": pd_node.id,
                    "title": pd_node.title,
                    "url": "#"
                },
                "content": [{
                    "id": 1,
                    "title": pd_node.title,
                    "content": pd_node.text_content,
                    "type": "article",
                    "anchor": "",
                    "is_structure": False,
                    "doc_id": pd_node.id
                }]
            }
            
        raise HTTPException(status_code=404, detail="Document not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
