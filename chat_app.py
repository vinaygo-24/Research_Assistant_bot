import google.generativeai as genai
from pinecone import Pinecone
import os
import re
import asyncio

async def get_response(query, pc_key, idx_name, gemini_key):
    genai.configure(api_key=gemini_key)
    pc = Pinecone(api_key=pc_key)
    index = pc.Index(idx_name)

    # --- 1. Dynamic Search Strategy ---
    search_query = query
    retrieval_limit = 25 # Default for normal Q&A
    
    # If asking about References, expand query and increase limit
    if "how many" in query.lower() and "ref" in query.lower():
        retrieval_limit = 80 # Deep scan for bibliography
        search_query += " references bibliography list [25] [30] [35] [40] author title year"

    # --- 2. Retrieve ---
    # Embed
    q_emb = genai.embed_content(
        model="models/embedding-001", 
        content=search_query, 
        task_type="retrieval_query"
    )['embedding']

    # Query Pinecone
    results = index.query(vector=q_emb, top_k=retrieval_limit, include_metadata=True)
    
    context_text = ""
    candidate_images = {} 
    
    for match in results['matches']:
        meta = match['metadata']
        text = meta.get('text', '')
        m_type = meta.get('type', 'text')
        page = meta.get('page', 'N/A')
        
        if m_type == 'image':
            path = meta.get('image_path')
            if path:
                filename = os.path.basename(path)
                candidate_images[filename] = path
                context_text += f"\n[IMAGE AVAILABLE]: ID={filename} (Description: {text})\n"
        elif m_type == 'table':
            # Label strictly as CSV for the Smart Fill logic
            context_text += f"\n[TABLE DATA (CSV) - Page {page}]:\n{text}\n"
        else:
            context_text += f"\n[TEXT Page {page}]: {text}\n"

    # --- 3. Generate Answer (The "Perfect" Prompt) ---
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are a precise Research Assistant. Answer using ONLY the context provided.
    
    Context:
    {context_text}

    User Question: {query}
    
    --- STRICT GUIDELINES ---
    1. **TABLES (Dataframe Style):**
       - If you encounter '[TABLE DATA (CSV)]', convert it into a **Markdown Table**.
       - **SMART FILL:** Many PDFs merge cells. If a cell is empty but clearly belongs to the group above it, **FILL IN the value**. Do not leave it blank. 
       - Make it look like a dense Pandas DataFrame.
       
    2. **REFERENCES (Validation):**
       - If asked for a count, **DO NOT** count lines or guess.
       - Scan for the pattern: `[n] Author Name`.
       - Find the **HIGHEST VALID NUMBER** matching that pattern.
       - Ignore isolated numbers like `[40]` if they are not citations.
       
    3. **IMAGES:**
       - **Rule:** Do NOT show images for simple text questions.
       - **Trigger:** Only if the user asks (e.g., "Show diagram", "Visuals") or if critical for explanation.
       - Syntax: <<SHOW_IMAGES>>filename.png<</SHOW_IMAGES>>
       
    4. **CITATIONS:**
       - Always end sentences with [Source: Page X] when relevant.
    """
    
    # Async generation to prevent timeout
    response = await model.generate_content_async(prompt)
    raw_answer = response.text
    
    # --- 4. Post-Process Image Triggers ---
    images_to_show = []
    clean_answer = raw_answer

    tag_match = re.search(r"<<SHOW_IMAGES>>(.*?)<</SHOW_IMAGES>>", raw_answer, re.DOTALL)
    
    if tag_match:
        file_string = tag_match.group(1)
        requested_files = [f.strip() for f in file_string.split(',')]
        for fname in requested_files:
            if fname in candidate_images:
                images_to_show.append(candidate_images[fname])
        clean_answer = raw_answer.replace(tag_match.group(0), "").strip()

    return clean_answer, images_to_show