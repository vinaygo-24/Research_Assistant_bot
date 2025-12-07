**Research_Assistant_bot**

End-to-End Pipeline: Ingestion → Extraction → Embedding → Vector DB → Chat Retrieval

This project is a complete production-style **RAG system** designed to process large PDFs (technical reports, research papers, etc.), extract text, tables, images, and formulas, embed everything using Gemini Embeddings, store it in Pinecone, and provide an interactive FastAPI chat interface that answers questions with context-aware retrieval.

**Features**

**✔ Automatic PDF ingestion at server startup**

**✔ Extracts all useful content types**
  - Text chunking (Recursive splitter)
  - Table extraction using Camelot
  - Image extraction + AI captioning (Gemini)
  - Formula detection via regex
  
**✔ Smart embedding pipeline**
  - Embedding batching, error-handling, fallbacks
  - Uploaded into Pinecone with metadata

**✔ Azure Blob Storage integration**
  - Automatic download of source PDFs from Azure storage

**✔ FastAPI chat interface with rich response handling**
  - Dynamically decides when to show images
  - Converts table-text into Markdown tables
  - Returns web-hosted images
