# from qdrant_client import QdrantClient
# from qdrant_client.http.models import PointStruct
# from tqdm import tqdm
# from dotenv import load_dotenv
# import re
# import hashlib
# import os
# load_dotenv()

# def slugify_model_name(model_name: str) -> str:
#     """Converts model name to a slug suitable for collection names."""
#     slug = model_name.split("/")[-1] # Take the name after the org
#     slug = re.sub(r'[^a-zA-Z0-9]', '_', slug).lower()
#     return slug.strip("_")

# def get_collection_name(source: str, model_name: str) -> str:
#     """Generates a collection name based on source and model."""
#     return f"{source}_{slugify_model_name(model_name)}"

# def get_point_id(doc_id: str, hierarchy_path: str) -> str:
#     """
#     Tạo ID duy nhất (MD5 Hash) cho point dựa trên ID văn bản và vị trí điều khoản.
#     Output ví dụ: 'a1b2c3d4e5f6...' (32 ký tự, an toàn cho URL/Frontend key)
#     """
#     # Xử lý trường hợp null
#     safe_doc_id = str(doc_id) if doc_id else "unknown_doc"
#     safe_path = str(hierarchy_path) if hierarchy_path else "general"

#     # Tạo chuỗi kết hợp (Raw String)
#     raw_combination = f"{safe_doc_id}_{safe_path}"

#     # Hash MD5 để tạo chuỗi ID cố định, không trùng lặp và an toàn
#     return hashlib.md5(raw_combination.encode('utf-8')).hexdigest()

# client = QdrantClient(url="http://localhost:6333")

# BATCH_SIZE = 128
# offset = None
# model_name = os.getenv("EMBEDDING_MODEL")
# vb_collection = get_collection_name("vbqppl", model_name)
# pbar = tqdm(desc="Updating payloads", unit="points")

# while True:
#     points, offset = client.scroll(
#         collection_name=vb_collection,
#         limit=BATCH_SIZE,
#         offset=offset,
#         with_payload=True,
#         with_vectors=False
#     )

#     if not points:
#         break

#     for p in points:
#         meta_id = p.payload.get("id")
#         hierarchy = p.payload.get("hierarchy_path", "")

#         client.set_payload(
#             collection_name=vb_collection,
#             payload={
#                 "id": get_point_id(meta_id, hierarchy),
#                 "doc_id": meta_id
#             },
#             points=[p.id]
#         )

#         pbar.update(1)

#     if offset is None:
#         break

# pbar.close()

from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os
import hashlib
import re
from tqdm import tqdm
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

client = QdrantClient(url="http://localhost:6333")

BATCH_SIZE = 256
model_name = os.getenv("EMBEDDING_MODEL")
pd_collection = get_collection_name("vbqppl", model_name)
offset = None

points, offset = client.scroll(
        collection_name=pd_collection,
        limit=BATCH_SIZE,
        offset=offset,
        with_payload=True,
        with_vectors=False
)

for p in points[:10]:
    print(p.payload)