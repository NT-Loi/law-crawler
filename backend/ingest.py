"""
Data Ingestion Script for Law Chatbot - Optimized for Large Datasets

Uses raw SQL inserts to handle PostgreSQL parameter limits.
"""
import json
import os
import re
from typing import List, Optional, Dict, Any

from sqlalchemy import text
from sqlmodel import Session, select
from tqdm import tqdm
from underthesea import word_tokenize
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    SparseVector, SparseVectorParams, SparseIndexParams,
)
from collections import Counter

from database import (
    PhapDienNode, VBQPPLDoc, VBQPPLNode, PhapDienReference, PhapDienRelation,
    engine, init_db
)

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHAP_DIEN_DIEU_PATH = os.path.join(BASE_DIR, "phap_dien/Dieu.json")
PHAP_DIEN_LIENQUAN_PATH = os.path.join(BASE_DIR, "phap_dien/LienQuan.json")
CRAWLED_DOCS_DIR = os.path.join(BASE_DIR, "crawled_docs")

# --- Qdrant Config ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
EMBEDDING_DIM = 768


def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_embedding_model():
    return SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')


def segment_text(text_str: str) -> str:
    return word_tokenize(text_str, format="text")


def compute_sparse_vector(text_str: str) -> SparseVector:
    """Compute sparse vector with unique indices (handles hash collisions)."""
    tokens = text_str.lower().split()
    token_counts = Counter(tokens)
    
    # Use dict to aggregate values for same hash index (collision handling)
    idx_to_value = {}
    for token, count in token_counts.items():
        idx = abs(hash(token)) % 100000
        idx_to_value[idx] = idx_to_value.get(idx, 0.0) + float(count)
    
    indices = list(idx_to_value.keys())
    values = list(idx_to_value.values())
    return SparseVector(indices=indices, values=values)


def extract_item_id_from_url(url: str) -> Optional[str]:
    match = re.search(r"ItemID=(\d+)", url)
    return match.group(1) if match else None


def extract_anchor_from_url(url: str) -> Optional[str]:
    return url.split("#")[1] if "#" in url else None


def setup_qdrant_collections(client: QdrantClient):
    for name in ["phapdien", "vbqppl"]:
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config={"dense": VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)},
                sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))}
            )
            print(f"Created collection: {name}")


def ingest_vbqppl_docs():
    """Ingests all VBQPPL documents from crawled_docs using batch inserts."""
    print("Ingesting VBQPPL documents...")
    crawled_files = [f for f in os.listdir(CRAWLED_DOCS_DIR) if f.endswith(".json")]
    
    with engine.connect() as conn:
        # Get already crawled doc IDs
        result = conn.execute(text("SELECT id FROM vbqppl_docs WHERE is_crawled = TRUE"))
        processed_ids = {row[0] for row in result}
        
        for filename in tqdm(crawled_files):
            doc_id = filename.replace(".json", "")
            if doc_id in processed_ids:
                continue
                
            filepath = os.path.join(CRAWLED_DOCS_DIR, filename)
            # ... rest of the logic ...
            
            # Batch insert nodes for this document
            sections = data.get("sections", [])
            if sections:
                node_data = [{
                    "doc_id": doc_id,
                    "anchor": s.get("anchor", "")[:255],
                    "type": s.get("type", "unknown")[:100],
                    "title": s.get("title", "")[:500],
                    "content": s.get("content", ""),
                    "is_structure": s.get("type") != "fallback"
                } for s in sections]
                
                conn.execute(text("""
                    INSERT INTO vbqppl_nodes (doc_id, anchor, type, title, content, is_structure)
                    VALUES (:doc_id, :anchor, :type, :title, :content, :is_structure)
                """), node_data)
            
            conn.commit()
    
    print(f"Ingested {len(crawled_files)} VBQPPL documents.")


def ingest_phapdien_nodes():
    """Ingests Phap Dien articles efficiently."""
    print("Ingesting Phap Dien nodes...")
    
    with open(PHAP_DIEN_DIEU_PATH, "r", encoding="utf-8") as f:
        dieu_data = json.load(f)
    print(f"Loaded {len(dieu_data)} records")
    
    with engine.connect() as conn:
        # Get existing VBQPPL doc IDs
        result = conn.execute(text("SELECT id FROM vbqppl_docs"))
        existing_vbqppl_ids = {row[0] for row in result}
        
        # Phase 1: Batch Insert PhapDienNodes
        print("  Phase 1: Inserting PhapDienNodes...")
        batch_size = 1000
        for i in tqdm(range(0, len(dieu_data), batch_size)):
            batch = dieu_data[i:i+batch_size]
            items = [{
                "id": item.get("MAPC"),
                "text_content": item.get("NoiDung", ""),
                "title": item.get("TEN", "")[:500],
                "demuc_id": item.get("DeMucID"),
                "label": item.get("TEN", "")[:500]
            } for item in batch if item.get("MAPC")]
            
            if items:
                conn.execute(text("""
                    INSERT INTO phapdien_nodes (id, text_content, title, demuc_id, label)
                    VALUES (:id, :text_content, :title, :demuc_id, :label)
                    ON CONFLICT (id) DO NOTHING
                """), items)
                conn.commit()
        
        # Phase 2: Insert references with placeholder handling
        print("  Phase 2: Inserting references...")
        added_placeholder_ids = set()
        for i in tqdm(range(0, len(dieu_data), batch_size)):
            batch = dieu_data[i:i+batch_size]
            refs_to_insert = []
            
            for item in batch:
                mapc = item.get("MAPC")
                if not mapc: continue
                
                for ref in item.get("VBQPPL", []):
                    link = ref.get("link", "")
                    doc_id = extract_item_id_from_url(link)
                    if not doc_id: continue
                    
                    # Placeholder check
                    if doc_id not in existing_vbqppl_ids and doc_id not in added_placeholder_ids:
                        conn.execute(text("""
                            INSERT INTO vbqppl_docs (id, title, url, is_crawled)
                            VALUES (:id, :title, :url, FALSE)
                            ON CONFLICT (id) DO NOTHING
                        """), {
                            "id": doc_id,
                            "title": (ref.get("name", "") or "Unknown")[:500],
                            "url": link
                        })
                        added_placeholder_ids.add(doc_id)
                    
                    refs_to_insert.append({
                        "phapdien_id": mapc,
                        "vbqppl_doc_id": doc_id,
                        "vbqppl_anchor": extract_anchor_from_url(link)[:255] if link and "#" in link else None,
                        "details": (ref.get("name", "") or "")[:1000]
                    })
            
            if refs_to_insert:
                conn.execute(text("""
                    INSERT INTO phapdien_references (phapdien_id, vbqppl_doc_id, vbqppl_anchor, details)
                    VALUES (:phapdien_id, :vbqppl_doc_id, :vbqppl_anchor, :details)
                """), refs_to_insert)
                conn.commit()


def ingest_phapdien_relations():
    """Ingests Phap Dien cross-references efficiently."""
    print("Ingesting Phap Dien relations...")
    
    with open(PHAP_DIEN_LIENQUAN_PATH, "r", encoding="utf-8") as f:
        lienquan_data = json.load(f)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM phapdien_nodes"))
        existing_ids = {row[0] for row in result}
    
    print(f"  Filtering {len(lienquan_data)} relations...")
    batch_size = 2000
    for i in tqdm(range(0, len(lienquan_data), batch_size)):
        batch = lienquan_data[i:i+batch_size]
        relations = [{
            "source_id": r.get("source_MAPC"),
            "target_id": r.get("target_MAPC")
        } for r in batch if r.get("source_MAPC") in existing_ids and r.get("target_MAPC") in existing_ids]
        
        if relations:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO phapdien_relations (source_id, target_id)
                    VALUES (:source_id, :target_id)
                    ON CONFLICT DO NOTHING
                """), relations)
                conn.commit()


def build_vector_index():
    """Builds Qdrant index for Phap Dien and VBQPPL nodes."""
    print("Building Vector Index...")
    
    client = get_qdrant_client()
    model = get_embedding_model()
    
    setup_qdrant_collections(client)
    
    # Index Phap Dien Nodes
    print("Indexing Phap Dien nodes...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, text_content, title, demuc_id FROM phapdien_nodes WHERE text_content IS NOT NULL AND text_content != ''"))
        rows = result.fetchall()
    
    batch_size = 50
    points = []
    
    for row in tqdm(rows):
        node_id, text_content, title, demuc_id = row
        segmented = segment_text(text_content)
        dense_vector = model.encode(segmented).tolist()
        sparse_vector = compute_sparse_vector(segmented)
        
        points.append(PointStruct(
            id=abs(hash(node_id)) % (2**63),
            vector={"dense": dense_vector, "sparse": sparse_vector},
            payload={"mapc": node_id, "title": title or "", "demuc_id": demuc_id or "", "source": "phapdien"}
        ))
        
        if len(points) >= batch_size:
            client.upsert(collection_name="phapdien", points=points)
            points = []
    
    if points:
        client.upsert(collection_name="phapdien", points=points)
    
    print(f"Indexed {len(rows)} Phap Dien nodes.")
    
    # Index VBQPPL Nodes
    print("Indexing VBQPPL nodes...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, doc_id, anchor, type, content FROM vbqppl_nodes WHERE content IS NOT NULL AND content != '' LIMIT 100000"))
        rows = result.fetchall()
    
    points = []
    for row in tqdm(rows):
        node_id, doc_id, anchor, node_type, content = row
        segmented = segment_text(content[:5000])  # Limit content length
        dense_vector = model.encode(segmented).tolist()
        sparse_vector = compute_sparse_vector(segmented)
        
        points.append(PointStruct(
            id=node_id,
            vector={"dense": dense_vector, "sparse": sparse_vector},
            payload={"doc_id": doc_id, "anchor": anchor or "", "type": node_type, "source": "vbqppl"}
        ))
        
        if len(points) >= batch_size:
            client.upsert(collection_name="vbqppl", points=points)
            points = []
    
    if points:
        client.upsert(collection_name="vbqppl", points=points)
    
    print(f"Indexed {len(rows)} VBQPPL nodes.")


def main():
    print("Initializing Database...")
    init_db()
    
    ingest_vbqppl_docs()
    ingest_phapdien_nodes()
    ingest_phapdien_relations()
    build_vector_index()
    
    print("Data Ingestion Complete!")


if __name__ == "__main__":
    main()
