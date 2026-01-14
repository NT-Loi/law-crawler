import json
import os
import sys
import logging
import time
from tqdm import tqdm
import torch

# Add current directory to path so we can import rag
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag import RAG

# Configure logging
# Suppress info logs from imported libraries
logging.getLogger().setLevel(logging.WARNING)

# Create a custom logger for this script
logger = logging.getLogger("evaluator")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def normalize_text(text):
    """Normalize text for matching."""
    if not text:
        return ""
    return text.lower().strip().replace('\n', ' ').replace('  ', ' ')

def evaluate_retrieval(dataset_path, k_values=[1, 3, 5, 10]):
    """Evaluate RAG retrieval performance."""
    
    # Load dataset
    logger.info(f"Loading dataset from {dataset_path}")
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file not found: {dataset_path}")
        return

    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Initialize RAG
    try:
        logger.info("Initializing RAG engine (this may take a moment)...")
        rag = RAG()
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")
        return

    # Metrics storage
    metrics = {k: {'precision': [], 'recall': []} for k in k_values}
    
    max_k = max(k_values)
    
    logger.info(f"Evaluating on {len(dataset)} samples...")
    
    # Use tqdm for progress bar
    for item in tqdm(dataset, desc="Evaluating"):
        query = item.get('question')
        ground_truth_refs = item.get('reference', [])
        
        if not query or not ground_truth_refs:
            continue
            
        # Normalize refs
        norm_refs = [normalize_text(ref) for ref in ground_truth_refs]
        
        # Retrieve docs
        try:
            # We retrieve max_k docs to calculate all metrics
            retrieved_docs = rag.retrieve(query, top_k=max_k)
        except Exception as e:
            logger.error(f"Error retrieving for query '{query}': {e}")
            retrieved_docs = []
            
        # Calculate metrics for each k
        for k in k_values:
            top_k_docs = retrieved_docs[:k]
            
            # 1. Citation Precision@K: Fraction of docs that contain at least one GT ref
            relevant_docs_count = 0
            found_refs = set()
            
            for doc in top_k_docs:
                content = normalize_text(doc.get('content', ''))
                is_relevant = False
                for ref in norm_refs:
                    if ref in content:
                        is_relevant = True
                        found_refs.add(ref)
                
                if is_relevant:
                    relevant_docs_count += 1
            
            precision = relevant_docs_count / k if k > 0 else 0
            
            # 2. Citation Recall@K: Fraction of GT refs found in ANY of the top K docs
            recall = len(found_refs) / len(norm_refs) if norm_refs else 0
            
            metrics[k]['precision'].append(precision)
            metrics[k]['recall'].append(recall)

    # Compute averages
    print("\n" + "="*40)
    print(" EVALUATION RESULTS ")
    print("="*40)
    
    for k in sorted(k_values):
        precisions = metrics[k]['precision']
        recalls = metrics[k]['recall']
        
        avg_precision = sum(precisions) / len(precisions) if precisions else 0
        avg_recall = sum(recalls) / len(recalls) if recalls else 0
        
        print(f"K={k:<2} | Precision: {avg_precision:.4f} | Recall: {avg_recall:.4f}")
    
    print("="*40)
    
    # Close RAG resources if needed
    if hasattr(rag, 'close'):
        rag.close()

if __name__ == "__main__":
    # Path to dataset
    dataset_file = "/home/nt-loi/law-chatbot/du_lieu_luat_dataset.json"
    
    # Check if dataset exists
    if not os.path.exists(dataset_file):
        print(f"Error: Dataset file not found at {dataset_file}")
        sys.exit(1)
        
    evaluate_retrieval(dataset_file)
