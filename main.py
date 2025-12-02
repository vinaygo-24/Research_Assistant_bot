import os
import dotenv
from pinecone import Pinecone, ServerlessSpec
from Read_data import download_blob_data
from img import extract_images_and_caption
from table import extract_tables_to_text
from chunking import extract_text_chunks
from formulas import extract_formulas_and_clean
from embedding import generate_embeddings
from vector_store import upload_to_pinecone

dotenv.load_dotenv()

def validate_config():
    """Checks if all required .env variables are set."""
    required_keys = [
        "PINECONE_API_KEY", 
        "PINECONE_INDEX_NAME", 
        "Gemini_Api", 
        "AZURE_CONN_STRING", 
        "AZURE_CONTAINER", 
        "AZURE_BLOB_NAME"
    ]
    
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"❌ CRITICAL ERROR: Missing Environment Variables in .env file: {missing}")
        return False
    return True

def run_ingestion():
    # 1. Validate Keys First
    if not validate_config():
        raise ValueError("Missing API Keys. Check terminal output for details.")

    print("--- 🚀 Checking Vector Database Status ---")
    
    # 2. Safe Pinecone Init
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME")
    except Exception as e:
        print(f"❌ Pinecone Connection Error: {e}")
        return

    # 3. Create Index if not exists
    existing_indexes = [i.name for i in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"[Pinecone] Creating new index: {index_name}")
        try:
            pc.create_index(
                name=index_name,
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        except Exception as e:
            print(f"❌ Failed to create index: {e}")
            return
    
    # 4. Check Stats (Skip if full)
    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    
    if stats.total_vector_count > 0:
        print(f"✅ Database already contains {stats.total_vector_count} vectors.")
        print("⏭️  Skipping Ingestion to save storage/time.")
        return 
    
    print("📉 Database is empty. Starting Ingestion Pipeline...")

    # 5. Get Data
    pdf_bytes = download_blob_data()
    if not pdf_bytes: 
        print("❌ Failed to download PDF. check Azure credentials.")
        return

    # 6. Pipeline Execution
    print("--- 📸 Pipeline: Images ---")
    image_objs = extract_images_and_caption(pdf_bytes, os.getenv("Gemini_Api"))
    
    print("--- 📊 Pipeline: Tables ---")
    table_objs = extract_tables_to_text(pdf_bytes)
    
    print("--- 📝 Pipeline: Text & Formulas ---")
    # Ensure chunking returns dicts!
    text_objs = extract_text_chunks(pdf_bytes) 
    final_text_objs = extract_formulas_and_clean(text_objs)
    
    # 7. Merge & Embed
    all_content_objects = image_objs + table_objs + final_text_objs
    print(f"--- 📦 Pipeline: Total Items to Embed: {len(all_content_objects)} ---")
    
    if not all_content_objects:
        print("⚠️ Warning: No content extracted from PDF.")
        return

    texts_to_embed = [obj["text"] for obj in all_content_objects]
    vectors = generate_embeddings(texts_to_embed, os.getenv("Gemini_Api"))
    
    # 8. Store
    upload_to_pinecone(
        all_content_objects, 
        vectors, 
        os.getenv("PINECONE_API_KEY"), 
        index_name
    )
    print("--- ✅ Ingestion Complete ---")

if __name__ == "__main__":
    run_ingestion()