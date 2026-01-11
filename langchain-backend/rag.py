from qdrant_client import QdrantClient
from qdrant_client.models import Prefetch, SparseVector, Fusion, FusionQuery, Filter, FieldCondition, MatchValue

from langchain_huggingface import HuggingFaceEmbeddings
from fastembed import SparseTextEmbedding
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import torch
from typing import Any
from utils import get_collection_name

import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

class RAG:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Device: {self.device}")

        # self.model = init_chat_model("google_genai:gemini-2.0-flash")
        # logging.info(f"Initialize LLM: {self.model}")
        
        # self.qdrant_client = QdrantClient(path=os.getenv("QDRANT_PATH"))
        self.qdrant_client = QdrantClient(host=os.getenv("QDRANT_HOST"), port=os.getenv("QDRANT_PORT"))
        logging.info(f"Initialize Qdrant client: {self.qdrant_client}")
        
        embedding_name = os.getenv("EMBEDDING_MODEL")
        model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
        encode_kwargs = {"convert_to_numpy": True, 
                        "normalize_embeddings": True}
        self.embedding = HuggingFaceEmbeddings(model_name=embedding_name, 
                                                model_kwargs=model_kwargs, 
                                                encode_kwargs=encode_kwargs)
        self.embedding._client.max_seq_length = int(os.getenv("MAX_SEQ_LENGTH"))
        logging.info(f"Initialize embedding: {embedding_name}")
        
        self.sparse_embedding = SparseTextEmbedding(model_name="Qdrant/bm25")
        logging.info(f"Initialize sparse embedding: {self.sparse_embedding}")
        
        self.pd_collection_name = get_collection_name("phapdien", embedding_name)

        rerank_model_name = os.getenv("RERANKING_MODEL")
        self.rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_model_name)
        self.rerank_model = AutoModelForSequenceClassification.from_pretrained(rerank_model_name)
        self.rerank_model.to(self.device)
        self.rerank_model.eval()
        logging.info(f"Initialize reranker: {rerank_model_name}")
        
    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        logging.info(f"Retrieve documents for query: {query}")
        dense_vec = self.embedding.embed_query(query)
        sparse_emb = next(self.sparse_embedding.embed([query]))
        sparse_vec = SparseVector(
            indices=sparse_emb.indices.tolist(),
            values=sparse_emb.values.tolist(),
        )
        results = self.qdrant_client.query_points(
            collection_name=self.pd_collection_name,
            prefetch=[
                Prefetch(query=dense_vec, using="dense", limit=top_k * 20),
                Prefetch(query=sparse_vec, using="sparse", limit=top_k * 20)
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k * 10 # Retrieve more for reranking
        ).points

        sources = []
        for i, result in enumerate(results):
            payload = result.payload
            source_id = payload.get("id")
            content = payload.get("content")
                    
            sources.append({"id": source_id, "content": content})
        
        return self.rerank(query, sources, top_k=top_k)

    def rerank(self, query: str, sources: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        logging.info(f"Rerank documents for query: {query}")
        
        if not sources:
            return []

        pairs = [[query, doc["content"]] for doc in sources]
        
        MAX_LENGTH = 2304 # 256 for query and 2048 for passages
        
        with torch.no_grad():
            inputs = self.rerank_tokenizer(
                pairs, 
                padding=True, 
                truncation=True, 
                return_tensors='pt', 
                max_length=MAX_LENGTH
            ).to(self.device)
            
            scores = self.rerank_model(**inputs, return_dict=True).logits.view(-1, ).float()
            
        scored_sources = []
        for i, score in enumerate(scores):
            doc = sources[i].copy()
            doc["score"] = score.item()
            scored_sources.append(doc)
            
        scored_sources.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_sources[:top_k]

    def close(self):
        self.qdrant_client.close()