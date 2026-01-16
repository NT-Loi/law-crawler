from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams, PointStruct
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from fastembed import SparseTextEmbedding
import uuid
from tqdm import tqdm
import json
import torch
import re
import hashlib
load_dotenv()

def slugify_model_name(model_name: str) -> str:
    """Converts model name to a slug suitable for collection names."""
    slug = model_name.split("/")[-1] # Take the name after the org
    slug = re.sub(r'[^a-zA-Z0-9]', '_', slug).lower()
    return slug.strip("_")

def get_collection_name(source: str, model_name: str) -> str:
    """Generates a collection name based on source and model."""
    return f"{source}_{slugify_model_name(model_name)}"

def get_point_id(doc_id: str, hierarchy_path: str) -> str:
    """
    Tạo ID duy nhất (MD5 Hash) cho point dựa trên ID văn bản và vị trí điều khoản.
    Output ví dụ: 'a1b2c3d4e5f6...' (32 ký tự, an toàn cho URL/Frontend key)
    """
    # Xử lý trường hợp null
    safe_doc_id = str(doc_id) if doc_id else "unknown_doc"
    safe_path = str(hierarchy_path) if hierarchy_path else "general"

    # Tạo chuỗi kết hợp (Raw String)
    raw_combination = f"{safe_doc_id}_{safe_path}"

    # Hash MD5 để tạo chuỗi ID cố định, không trùng lặp và an toàn
    return hashlib.md5(raw_combination.encode('utf-8')).hexdigest()

batch_size = 128
model_name = os.getenv("EMBEDDING_MODEL")
model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
encode_kwargs = {"convert_to_numpy": True, 
                "normalize_embeddings": True}
embedding = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
embedding._client.max_seq_length = int(os.getenv("MAX_SEQ_LENGTH"))
sparse_embedding = SparseTextEmbedding(model_name="Qdrant/bm25")

# client = QdrantClient(path="./qdrant_data")
client = QdrantClient(host=os.getenv("QDRANT_HOST"), port=os.getenv("QDRANT_PORT"))
pd_collection = get_collection_name("phapdien", model_name)
vb_collection = get_collection_name("vbqppl", model_name)
vector_size = os.getenv("VECTOR_SIZE")

if client.collection_exists(pd_collection):
    client.delete_collection(pd_collection)

if client.collection_exists(vb_collection):
    client.delete_collection(vb_collection)

client.create_collection(
    collection_name=pd_collection,
    vectors_config={"dense": VectorParams(size=vector_size, distance=Distance.COSINE)},
    sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))}
)
print(f"Created collection: {pd_collection} (Dim: {vector_size})")

with open(os.getenv("PHAPDIEN_DIR") + "/Dieu.json", "r", encoding="utf-8") as f:
    data = json.load(f)

points = []
for i in tqdm(range(0, len(data), batch_size), desc="Indexing Phap Dien"):
    batch_data = data[i:i + batch_size]
    batch_texts = [f"{item['TEN']}\n{item['NoiDung']}" for item in batch_data]
    batch_dense_vectors = embedding.embed_documents(batch_texts)
    batch_sparse_vectors = list(sparse_embedding.embed(batch_texts))
    
    for item, dense_vec, sparse_vec in zip(batch_data, batch_dense_vectors, batch_sparse_vectors):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_vec,
                    "sparse": {
                        "indices": sparse_vec.indices,
                        "values": sparse_vec.values
                    }
                },
                payload={
                    "id": item["ID"],
                    "source": "phapdien",
                    "title": f"Pháp điển {item['TEN']}",
                    "content": item['NoiDung'],
                    "embed_content": f"{item['TEN']}\n{item['NoiDung']}",
                    "url": "https://phapdien.moj.gov.vn/TraCuuPhapDien/MainBoPD.aspx"
                }
            )
        )
        if len(points) >= batch_size:
            client.upsert(collection_name=pd_collection, points=points)
            points = []

if points:
    client.upsert(collection_name=pd_collection, points=points)

print("Indexed Phap Dien nodes into", pd_collection)

client.create_collection(
    collection_name=vb_collection,
    vectors_config={"dense": VectorParams(size=vector_size, distance=Distance.COSINE)},
    sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))}
)
print(f"Created collection: {vb_collection} (Dim: {vector_size})")

with open(os.getenv("VBQPPL"), "r", encoding="utf-8") as f:
    data = json.load(f)

points = []
batch_texts = []
batch_metas = []

for item in tqdm(data, desc="Indexing VBQPPL"):
    id = item.get("id")
    title = item.get("title")
    if title == "Unknown Title":
        title = ""
    url = item.get("url")

    chunks = item.get("sections", [])
    for chunk in chunks:
        hierarchy_path = chunk.get("hierarchy_path", "")
        content = f"{chunk.get('content')}"
        embed_content = f"{title}\n{hierarchy_path}\n{content}"
        batch_texts.append(embed_content)
        batch_metas.append({
            "id": id,
            "title": title,
            "url": url,
            "hierarchy_path": hierarchy_path,
            "content": content,
            "embed_content": embed_content
        })
        
        if len(batch_texts) >= batch_size:
            batch_dense_vectors = embedding.embed_documents(batch_texts)
            batch_sparse_vectors = list(sparse_embedding.embed(batch_texts))
            
            for text, meta, dense_vec, sparse_vec in zip(batch_texts, batch_metas, batch_dense_vectors, batch_sparse_vectors):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector={
                            "dense": dense_vec,
                            "sparse": {
                                "indices": sparse_vec.indices,
                                "values": sparse_vec.values
                            }
                        },
                        payload={
                            "id": get_point_id(meta["id"], meta.get("hierarchy_path", "")),
                            "doc_id": meta["id"],   
                            "url": meta.get("url", ""),
                            "source": "vbqppl",
                            "title": meta.get("title", ""),
                            "hierarchy_path": meta.get("hierarchy_path", ""),
                            "content": meta.get("content", ""),
                            "embed_content": text
                        }
                    )
                )
            
            client.upsert(collection_name=vb_collection, points=points)
            points = []
            batch_texts = []
            batch_metas = []

# Process remaining items
if batch_texts:
    batch_dense_vectors = embedding.embed_documents(batch_texts)
    batch_sparse_vectors = list(sparse_embedding.embed(batch_texts))
    
    for text, meta, dense_vec, sparse_vec in zip(batch_texts, batch_metas, batch_dense_vectors, batch_sparse_vectors):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_vec,
                    "sparse": {
                        "indices": sparse_vec.indices,
                        "values": sparse_vec.values
                    }
                },
                payload={
                    "id": get_point_id(meta["id"], meta.get("hierarchy_path", "")),
                    "doc_id": meta["id"],
                    "url": meta.get("url", ""),
                    "source": "vbqppl",
                    "title": meta.get("title", ""),
                    "hierarchy_path": meta.get("hierarchy_path", ""),
                    "content": meta.get("content", ""),
                    "embed_content": text
                }
            )
        )
    client.upsert(collection_name=vb_collection, points=points)

print("Indexed VBQPPL nodes into", vb_collection)

client.close()