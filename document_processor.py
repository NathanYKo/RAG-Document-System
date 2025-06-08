import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import PyPDF2
import docx
import asyncio
import logging
import io
from typing import Optional, Dict, Any, List
import threading
try:
    from embeddings import generate_embeddings
except ImportError:
    # Fallback to simple embeddings for testing
    from embeddings_simple import generate_embeddings 
from database import ChromaDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe singleton pattern for ChromaDB instance
class DatabaseSingleton:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> ChromaDB:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    try:
                        # Ensure db directory exists
                        os.makedirs("./db", exist_ok=True)
                        cls._instance = ChromaDB()
                    except Exception as e:
                        logger.error(f"Failed to initialize ChromaDB: {str(e)}")
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to initialize database"
                        )
        return cls._instance

def get_db() -> ChromaDB:
    """Get or create ChromaDB instance"""
    return DatabaseSingleton.get_instance()

class ChunkConfig(BaseModel):
    size: int = 1000
    overlap: int = 200

app = FastAPI(title="Document Processing Pipeline", version="1.0.0")

def process_pdf(file_content: bytes) -> str:
    """Process PDF file and extract text"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def process_docx(file_content: bytes) -> str:
    """Process DOCX file and extract text"""
    try:
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        text = " ".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error processing DOCX: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing DOCX: {str(e)}")

def process_txt(file_content: bytes) -> str:
    """Process TXT file and extract text"""
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_content.decode("latin-1")
        except Exception as e:
            logger.error(f"Error processing TXT: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing TXT: {str(e)}")

def clean_text(text: str) -> str:
    """Perform text cleaning and normalization"""
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Remove extra whitespace at beginning and end
    text = text.strip()
    
    return text

def create_chunks(text: str, config: ChunkConfig) -> list:
    """Create text chunks with specified size and overlap"""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + config.size, text_length)
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)
        
        # Move to next chunk position
        if end >= text_length:
            break
            
        start += config.size - config.overlap
        
        # Prevent infinite loop if overlap >= size
        if config.overlap >= config.size:
            start = end
    
    return chunks

async def process_chunks(chunks: List[str], metadata: Dict[str, Any]) -> List[str]:
    """Process chunks by generating embeddings and storing in vector database"""
    try:
        # Generate embeddings for chunks
        embeddings = generate_embeddings(chunks)

        # Add chunks and metadata to vector DB
        db = get_db()
        # ChromaDB expects a list of metadatas, one for each document.
        metadatas = [metadata for _ in chunks]
        ids = await db.add_documents(chunks, embeddings, metadatas)
        
        logger.info(f"Processed {len(chunks)} chunks for document: {metadata['source']}")
        return ids
    except Exception as e:
        logger.error(f"Error processing chunks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document chunks: {str(e)}"
        )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Document Processing Pipeline is running"}

@app.post("/process_document")
async def process_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    """Process document and return text chunks"""
    logger.info(f"Processing file: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Create chunk config
    config = ChunkConfig(size=chunk_size, overlap=chunk_overlap)
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process based on file type
        if file.filename.lower().endswith(".pdf"):
            text = process_pdf(file_content)
        elif file.filename.lower().endswith(".docx"):
            text = process_docx(file_content)
        elif file.filename.lower().endswith(".txt"):
            text = process_txt(file_content)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.filename}. Supported types: PDF, DOCX, TXT"
            )

        # Clean and chunk text
        cleaned_text = clean_text(text)
        chunks = create_chunks(cleaned_text, config)

        # Process chunks and store in vector database
        metadata = {"source": file.filename, "file_type": file.filename.split('.')[-1].lower()}
        chunk_ids = await process_chunks(chunks, metadata)
        
        return {
            "filename": file.filename,
            "total_chunks": len(chunks),
            "chunk_size": config.size,
            "chunk_overlap": config.overlap,
            "original_text_length": len(text),
            "cleaned_text_length": len(cleaned_text),
            "chunks": chunks,
            "chunk_ids": chunk_ids,
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing file: {file.filename}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/process_document_json")
async def process_document_json(file: UploadFile = File(...), config: ChunkConfig = None):
    """Alternative endpoint accepting JSON config in request body"""
    if config is None:
        config = ChunkConfig()
    
    return await process_document(
        file=file,
        chunk_size=config.size,
        chunk_overlap=config.overlap
    )

@app.post("/query")
async def query_documents(query: str = Form(...), n_results: int = Form(5)):
    """Query the vector database for similar documents"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        db = get_db()
        results = db.query(query_texts=[query], n_results=n_results)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results.get("documents", [[]])[0]) if results.get("documents") else 0
        }
    except Exception as e:
        logger.exception(f"Error querying documents with query: {query}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/database/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        db = get_db()
        count = db.count()
        return {
            "total_documents": count,
            "status": "healthy"
        }
    except Exception as e:
        logger.exception("Error getting database stats")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 