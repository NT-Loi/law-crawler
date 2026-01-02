import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY present: {bool(api_key)}")
    
    if api_key:
        print("Using GeminiService (Placeholder in current code)")
    else:
        print("Using OllamaService")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen3:4b")
        print(f"Connecting to Ollama at {base_url} with model {model}")
        
        try:
            # Check if model exists
            print("Checking Ollama tags...")
            resp = requests.get(f"{base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m['name'] for m in resp.json()['models']]
                print(f"Available models: {models}")
                if model not in models and f"{model}:latest" not in models:
                    print(f"WARNING: Model {model} not found in Ollama!")
            
            # Simple generation test
            print("Testing generation...")
            resp = requests.post(f"{base_url}/api/generate", json={
                "model": model,
                "prompt": "Hello",
                "stream": False
            }, timeout=30)
            print(f"Generation successful: {resp.status_code}")
            print(resp.json().get('response', '')[:50])
            
        except Exception as e:
            print(f"Ollama connection error: {e}")

if __name__ == "__main__":
    check_llm()
