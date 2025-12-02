import google.generativeai as genai
import time

def generate_embeddings(text_list, api_key):
    genai.configure(api_key=api_key)
    embeddings = []
    batch_size = 10
    
    print(f"[embedding] Embedding {len(text_list)} items...")
    
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i+batch_size]
        try:
            resp = genai.embed_content(
                model="models/embedding-001",
                content=batch,
                task_type="retrieval_document"
            )
            embeddings.extend(resp['embedding'])
            time.sleep(0.5)
        except Exception as e:
            print(f"Embedding error: {e}")
            # Pad with zeros if fail to keep alignment (simplified)
            embeddings.extend([[0.0]*768] * len(batch)) 
            
    return embeddings