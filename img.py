import fitz  # PyMuPDF
import io
import os
import time
import PIL.Image
import google.generativeai as genai

def extract_images_and_caption(pdf_bytes, api_key, output_folder="output_images"):
    if not pdf_bytes: return [], []
    
    os.makedirs(output_folder, exist_ok=True)
    pdf_stream = io.BytesIO(pdf_bytes)
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    
    image_data_list = [] # Stores {text: caption, type: image, path: path}

    # 1. Extract Images
    for page_idx, page in enumerate(doc):
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base = doc.extract_image(xref)
            if len(base["image"]) < 5120: continue # Skip tiny icons

            filename = f"p{page_idx}_img{img_idx}.{base['ext']}"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, "wb") as f:
                f.write(base["image"])
            
            image_data_list.append({"path": filepath, "page": page_idx})

    # 2. Generate Captions (The "AI" part)
    print(f"[img] Captioning {len(image_data_list)} images...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    processed_data = []
    
    for img in image_data_list:
        try:
            pil_img = PIL.Image.open(img["path"])
            prompt = "Analyze this image from a technical document. Describe the diagram, chart, or architecture in detail for search indexing."
            response = model.generate_content([prompt, pil_img])
            
            processed_data.append({
                "text": f"Image Description (Page {img['page']}): {response.text}",
                "type": "image",
                "image_path": img["path"], # Important for UI display
                "page": img["page"]
            })
            time.sleep(1.5) # Rate limit handling
        except Exception as e:
            print(f"Caption error: {e}")

    return processed_data