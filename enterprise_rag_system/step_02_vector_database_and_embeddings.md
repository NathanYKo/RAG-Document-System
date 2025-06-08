# Vector Database & Embeddings Implementation

**Generated:** 2025-06-07T20:56:54.177691

Here is a complete implementation of a vector database using ChromaDB and sentence-transformers, integrated with the document processing pipeline from the previous step:

1. Code Files:

embeddings.py:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(texts):
    return model.encode(texts)
```

database.py:
```python
import chromadb
from chromadb.config import Settings
import asyncio
from embeddings import generate_embeddings

CHROMA_SETTINGS = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./db"
)

class ChromaDB:
    def __init__(self):
        self.client = chromadb.Client(CHROMA_SETTINGS)
        self.collection = self.client.get_or_create_collection("documents")

    async def add_documents(self, documents, embeddings, metadatas):
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        await self.persist()

    async def persist(self):
        await asyncio.to_thread(self.client.persist)

    def query(self, query_texts, n_results=5):
        query_embeddings = generate_embeddings(query_texts)
        return self.collection.query(
            query_embeddings=query_embeddings, 
            n_results=n_results
        )
    
    def get(self, ids):
        return self.collection.get(ids)

    async def delete(self, ids):
        self.collection.delete(ids)
        await self.persist()
```

document_processor.py (updated):
```python
# ...previous code...
from embeddings import generate_embeddings 
from database import ChromaDB

# ...previous code...

async def process_chunks(chunks, metadata):
    # Generate embeddings for chunks
    embeddings = generate_embeddings(chunks)

    # Add chunks and metadata to vector DB
    # NOTE: In a production app, the ChromaDB client should be a singleton
    # and not re-initialized on every call.
    db = ChromaDB()
    # ChromaDB expects a list of metadatas, one for each document.
    metadatas = [metadata for _ in chunks]
    await db.add_documents(chunks, embeddings, metadatas)
    
    logger.info(f"Processed {len(chunks)} chunks for document: {metadata['source']}")

@app.post("/process_document")
async def process_document(config: ChunkConfig, file: UploadFile = File(...)):
    # ...previous code...
    metadata = {"source": file.filename}
    chunks = create_chunks(text, config)

    await process_chunks(chunks, metadata)

    return {"status": "success"}

@app.post("/query")
async def query_documents(query: str):
    # NOTE: In a production app, the ChromaDB client should be a singleton
    # and not re-initialized on every call.
    db = ChromaDB()
    results = db.query(query_texts=[query])
    return {"results": results}
```

2. Setup Instructions:

- Follow setup from previous step for the document processor
- Install additional dependencies (see next section) 
- Save the new `embeddings.py` and `database.py` files
- Create a `./db` directory for the ChromaDB storage
- Run the FastAPI server with `uvicorn document_processor:app --reload`

3. Additional Dependencies:

```
chromadb==0.3.1
sentence-transformers==2.2.2
```

Install with:
```
pip install chromadb sentence-transformers
```

4. Configuration:
- ChromaDB settings are defined in `database.py`, specifying the DuckDB backend and persistence directory.

5. Testing:

test_database.py:
```python
import pytest
from embeddings import generate_embeddings
from database import ChromaDB

@pytest.mark.asyncio
async def test_db_integration():
    db = ChromaDB()
    db.client.reset() # Reset database before test to ensure isolation
    
    # Add documents
    documents = ["This is a test document", "Another test document"] 
    embeddings = generate_embeddings(documents)
    metadatas = [{"source": "test1"}, {"source": "test2"}]
    await db.add_documents(documents, embeddings, metadatas)

    # Query documents
    results = db.query(query_texts=["test document"])
    assert len(results["documents"][0]) > 0

    # Get document by ID
    doc_id = results["ids"][0][0]
    doc = db.get(ids=[doc_id])
    assert doc["documents"][0] in documents

    # Delete document
    await db.delete(ids=[doc_id])
    doc = db.get(ids=[doc_id])
    assert len(doc["documents"]) == 0
```

Run tests with: `pytest test_database.py`

6. Integration:

- The document processor now calls `process_chunks` after chunking the text
- `process_chunks` generates embeddings and adds the chunks and metadata to ChromaDB
- A new `/query` endpoint allows querying the vector DB by text similarity
- Metadata like the source filename is included when ingesting into ChromaDB
- The `ChromaDB` class provides utilities for adding, querying, getting and deleting documents

The vector database can now be queried after documents are processed through the pipeline. The ChromaDB setup is fully integrated with the document processor.

Let me know if you have any other questions! The code should be ready to run following the updated setup steps.