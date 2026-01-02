from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, SearchRequest, Filter, FieldCondition, MatchValue
)
from sentence_transformers import SentenceTransformer
from underthesea import word_tokenize
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, PhapDienNode, VBQPPLDoc, VBQPPLNode, PhapDienReference
import os
from collections import Counter

class RAGEngine:
    def __init__(self):
        self.qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=6333)
        self.model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')
        self.embedding_dim = 768

    def segment_text(self, text_str: str) -> str:
        return word_tokenize(text_str, format="text")

    def compute_sparse_vector(self, text_str: str) -> Dict[str, Any]:
        tokens = text_str.lower().split()
        token_counts = Counter(tokens)
        indices = []
        values = []
        for token, count in token_counts.items():
            idx = abs(hash(token)) % 100000
            indices.append(idx)
            values.append(float(count))
        return {"indices": indices, "values": values}

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hyper-retrieval: 1. Hybrid Search in Phap Dien -> 2. Relation Expansion -> 3. Scoped VBQPPL Search
        """
        segmented_query = self.segment_text(query)
        dense_vec = self.model.encode(segmented_query).tolist()
        sparse_vec = self.compute_sparse_vector(segmented_query)

        # 1. Vector Search on Phap Dien using dense vectors
        try:
            pd_results = self.qdrant.query_points(
                collection_name="phapdien",
                query=dense_vec,
                using="dense",
                limit=top_k
            ).points
        except Exception as e:
            print(f"Qdrant search error: {e}")
            pd_results = []


        context_nodes = []
        for hit in pd_results:
            mapc = hit.payload.get("mapc")
            
            # 2. Get full content and references from PostgreSQL
            with engine.connect() as conn:
                # Get the Article content
                node_res = conn.execute(text("SELECT title, text_content FROM phapdien_nodes WHERE id = :id"), {"id": mapc}).fetchone()
                
                # Get related VBQPPL references
                ref_res = conn.execute(text("""
                    SELECT r.details, d.title as doc_title, d.url, r.vbqppl_doc_id, r.vbqppl_anchor 
                    FROM phapdien_references r
                    JOIN vbqppl_docs d ON r.vbqppl_doc_id = d.id
                    WHERE r.phapdien_id = :id
                """), {"id": mapc}).fetchall()

                # Get related Phap Dien articles (internal relations)
                rel_res = conn.execute(text("""
                    SELECT n.title, n.id 
                    FROM phapdien_relations r
                    JOIN phapdien_nodes n ON r.target_id = n.id
                    WHERE r.source_id = :id
                """), {"id": mapc}).fetchall()

                context_nodes.append({
                    "source": "phapdien",
                    "id": mapc,
                    "title": node_res[0] if node_res else "Unknown",
                    "content": node_res[1] if node_res else "",
                    "references": [dict(r._mapping) for r in ref_res],
                    "related_pd": [dict(r._mapping) for r in rel_res]
                })

        # 3. Expansion: If we need more VBQPPL context, we could do scoped searches here.
        # For now, we return the Phap Dien results + their direct links.
        return context_nodes

    def format_context(self, nodes: List[Dict[str, Any]]) -> str:
        context_parts = []
        for node in nodes:
            part = f"### {node['title']} (Pháp Điển)\n{node['content']}\n"
            if node['references']:
                part += "Nguồn dẫn chiếu:\n"
                for ref in node['references']:
                    part += f"- {ref['details']} (Link: {ref['url']})\n"
            context_parts.append(part)
        return "\n---\n".join(context_parts)
