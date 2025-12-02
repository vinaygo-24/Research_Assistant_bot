import time
from pinecone import Pinecone, ServerlessSpec

def upload_to_pinecone(data_objects, embeddings, api_key, index_name):
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    vectors_to_upsert = []
    print(f"[Pinecone] Batching {len(data_objects)} items...")

    for i, (obj, vector) in enumerate(zip(data_objects, embeddings)):
        chunk_id = f"{obj['type']}_{i}_{int(time.time())}"
        
        # Clean metadata
        metadata = {
            "text": obj["text"],
            "type": obj["type"],
            "page": str(obj.get("page", "N/A")),
            "image_path": obj.get("image_path", "")
        }

        vectors_to_upsert.append((chunk_id, vector, metadata))

        if len(vectors_to_upsert) >= 50:
            index.upsert(vectors=vectors_to_upsert)
            vectors_to_upsert = []
    
    if vectors_to_upsert:
        index.upsert(vectors=vectors_to_upsert)
    
    print("[Pinecone] Upload Success!")