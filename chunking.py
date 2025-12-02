import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
import io

def extract_text_chunks(pdf_bytes):
    doc = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    all_chunks = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if len(text) < 50: continue
            
        chunks = splitter.split_text(text)
        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "type": "text",
                "page": page_num + 1, # Humans like 1-based indexing
                "image_path": ""
            })
            
    return all_chunks