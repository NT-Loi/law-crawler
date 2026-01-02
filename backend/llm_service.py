from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, AsyncGenerator
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class LLMService(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, context: str) -> str:
        pass

    @abstractmethod
    async def stream_response(self, prompt: str, context: str) -> AsyncGenerator[str, None]:
        pass


class GeminiService(LLMService):
    """Implementation for Google Gemini API."""
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

    async def generate_response(self, prompt: str, context: str) -> str:
        # Placeholder for Gemini async implementation
        return "Gemini response placeholder (Async)"

    async def stream_response(self, prompt: str, context: str) -> AsyncGenerator[str, None]:
        yield "Streaming from Gemini..."


class OllamaService(LLMService):
    """Implementation for local Ollama."""
    def __init__(
        self, 
        base_url: str = None, 
        model: str = None
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")

    async def generate_response(self, prompt: str, context: str) -> str:
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                print(f"Connecting to Ollama at {self.base_url} with model {self.model}...")
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"Context:\n{context}\n\nQuestion: {prompt}",
                        "stream": False
                    }
                )
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Ollama generation error: {repr(e)}")
                return f"Xin lỗi, tôi gặp khó khăn khi kết nối với mô hình AI: {str(e)}"

    async def stream_response(self, prompt: str, context: str) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"Context:\n{context}\n\nQuestion: {prompt}",
                    "stream": True
                }
            ) as response:
                thinking_active = False
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            chunk = json.loads(line)
                            
                            # Handle reasoning content
                            val_think = chunk.get("thinking", "")
                            if val_think:
                                if not thinking_active:
                                    yield "<think>"
                                    thinking_active = True
                                yield val_think
                            
                            # Handle actual response
                            val_response = chunk.get("response", "")
                            if val_response:
                                if thinking_active:
                                    yield "</think>"
                                    thinking_active = False
                                yield val_response
                                
                            if chunk.get("done"):
                                if thinking_active:
                                    yield "</think>"
                                break
                        except Exception as e:
                            print(f"Error parsing chunk: {e}")
                            pass
