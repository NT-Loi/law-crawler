import asyncio
import os
from rag import RAGEngine
from database import engine

async def test_rag():
    print("Initializing RAGEngine...")
    try:
        rag = RAGEngine()
        print("RAGEngine initialized.")
    except Exception as e:
        print(f"Error initializing RAGEngine: {e}")
        return

    query = "quy định về hợp đồng"
    print(f"Testing retrieval for query: '{query}'")
    
    try:
        # Test tokenization
        print("Segmenting text...")
        segmented = rag.segment_text(query)
        print(f"Segmented: {segmented}")
        
        # Test encoding
        print("Encoding text...")
        dense_vec = rag.model.encode(segmented).tolist()
        print(f"Encoded vector length: {len(dense_vec)}")
        
        # Test Qdrant search
        print("Searching Qdrant...")
        results = await rag.retrieve(query)
        print(f"Retrieval successful. Found {len(results)} results.")
        for res in results:
            print(f"- {res['title']} (ID: {res['id']})")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag())
