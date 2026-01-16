
import json
import asyncio
import aiohttp
import os
from tqdm.asyncio import tqdm
import logging
from datetime import datetime

# Configuration
API_URL = "http://localhost:8888/chat"
INPUT_FILE = "../data/du_lieu_luat_dataset.json"
OUTPUT_FILE = "../data/evaluation_results.json"
# With CONCURRENCY_LIMIT=1, we can use a simple loop. 
# If > 1, the progress bar description for "current question" becomes erratic (race condition on display),
# so we stick to sequential for clear "Current Question" tracking as requested.
CONCURRENCY_LIMIT = 1 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='evaluate.log')

async def process_question(session, item):
    question = item.get("question")
    if not question:
        return None

    payload = {
        "message": question,
        "history": [],
        "mode": "auto",
        "stream": False
    }

    model_answer = ""
    used_docs = []
    
    try:
        # Increase timeout for full generation
        timeout = aiohttp.ClientTimeout(total=400)
        async with session.post(API_URL, json=payload, timeout=timeout) as response:
            if response.status != 200:
                logging.error(f"Error processing question '{question[:30]}...': Status {response.status}")
                return {
                    **item,
                    "model_response": f"ERROR: API returned non-200 status ({response.status})",
                    "used_docs_metadata": []
                }

            try:
                # Read full JSON response directly
                resp_json = await response.json()
                model_answer = resp_json.get("response", "")
                used_docs = resp_json.get("used_docs", [])
                
            except Exception as e:
                logging.error(f"Error parsing JSON response for '{question[:30]}...': {e}")
                model_answer = f"ERROR: Failed to parse response: {e}"

            # Remove <think>...</think> blocks if any remains
            import re
            model_answer = re.sub(r'<think>.*?</think>', '', model_answer, flags=re.DOTALL).strip()

                    
    except Exception as e:
        logging.error(f"Exception for question '{question[:30]}...': {e}")
        model_answer = f"ERROR: {str(e)}"

    return {
        "question": question,
        "expected_answer": item.get("answer", ""),
        "expected_references": item.get("reference", []),
        "model_response": model_answer,
        "used_docs_metadata": used_docs
    }

async def main():
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Test with subset if needed
    dataset = dataset[:5] 

    results = []
    
    print(f"Starting evaluation of {len(dataset)} questions...")
    print(f"Logs are written to 'evaluate.log'")

    async with aiohttp.ClientSession() as session:
        # Use tqdm to wrap the iterator for progress bar
        # We process sequentially to allow updating the description with the current question
        pbar = tqdm(dataset, desc="Evaluating", unit="q")
        
        for item in pbar:
            q_text = item.get("question", "")
            # Update description to show current question (truncated)
            pbar.set_description(f"Eval: {q_text[:40]:<40}")
            
            result = await process_question(session, item)
            if result:
                results.append(result)

    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\nProcessing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
