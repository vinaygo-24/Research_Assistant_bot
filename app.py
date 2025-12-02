import os
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import dotenv

import chat_app
from main import run_ingestion

dotenv.load_dotenv()

system_status = {"ready": False, "message": "System is initializing..."}

def background_ingestion_task():
    global system_status
    print("\n[Auto-Start] 🚀 Starting Ingestion Pipeline...")
    try:
        # Run ingestion (it will self-cancel if DB is full, thanks to the fix in main.py)
        run_ingestion()
        system_status["ready"] = True
        system_status["message"] = "System Online"
        print("[Auto-Start] ✅ System Ready.")
    except Exception as e:
        print(f"[Auto-Start] ❌ Error: {e}")
        system_status["message"] = f"Startup Error: {str(e)}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=background_ingestion_task)
    thread.daemon = True
    thread.start()
    yield
    print("[System] Shutting down...")

app = FastAPI(lifespan=lifespan)

os.makedirs("output_images", exist_ok=True)
app.mount("/images", StaticFiles(directory="output_images"), name="images")

class ChatRequest(BaseModel):
    query: str

@app.get("/")
async def get_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/status")
async def get_status():
    return system_status

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, req: Request):
    global system_status
    
    if not system_status["ready"]:
        return {
            "answer": f"⚠️ **Please wait.** \n\n{system_status['message']}",
            "images": [],
            "sources": []
        }

    try:
        # Await the async response
        answer, img_paths = await chat_app.get_response(
            request.query, 
            os.getenv("PINECONE_API_KEY"),
            os.getenv("PINECONE_INDEX_NAME"),
            os.getenv("Gemini_Api")
        )
        
        web_images = []
        base_url = str(req.base_url).rstrip('/')
        for path in img_paths:
            filename = os.path.basename(path)
            web_images.append(f"{base_url}/images/{filename}")

        return {
            "answer": answer,
            "images": web_images,
            "sources": [] 
        }

    except Exception as e:
        print(f"Chat Error: {e}")
        return {
            "answer": f"**Error:** {str(e)}",
            "images": [],
            "sources": []
        }

if __name__ == "__main__":
    # Increased timeout to 180s (3 mins) to be safe with large PDF analysis
    uvicorn.run(app, host="127.0.0.1", port=8000, timeout_keep_alive=180)