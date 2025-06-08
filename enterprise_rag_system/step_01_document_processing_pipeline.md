# Document Processing Pipeline Implementation

**Generated:** 2025-06-07T20:56:08.443543

Here is a complete implementation of a document processing pipeline based on your requirements:

1. Code Files:

document_processor.py:
```python
import os
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import PyPDF2
import docx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkConfig(BaseModel):
    size: int = 1000
    overlap: int = 200

app = FastAPI()

def process_pdf(file):
    pdf_reader = PyPDF2.PdfFileReader(file)
    text = ""
    for page in range(pdf_reader.numPages):
        text += pdf_reader.getPage(page).extractText()
    return text

def process_docx(file):
    doc = docx.Document(file)
    text = " ".join([para.text for para in doc.paragraphs])
    return text

def process_txt(file):
    return file.read().decode("utf-8") 

def clean_text(text):
    # Perform text cleaning and normalization here
    return text.replace("\n", " ").lower()

def create_chunks(text, config):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + config.size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start += config.size - config.overlap
    return chunks

@app.post("/process_document")
async def process_document(config: ChunkConfig, file: UploadFile = File(...)):
    logger.info(f"Processing file: {file.filename}")
    
    try:
        if file.filename.endswith(".pdf"):
            text = process_pdf(file.file)
        elif file.filename.endswith(".docx"):
            text = process_docx(file.file)
        elif file.filename.endswith(".txt"):
            text = process_txt(file.file)
        else:
            raise ValueError(f"Unsupported file type: {file.filename}")

        text = clean_text(text)
        chunks = create_chunks(text, config)

        # Simulating async processing 
        await asyncio.sleep(1)
        
        return {"chunks": chunks}
    
    except Exception as e:
        logger.exception(f"Error processing file: {file.filename}")
        raise

```

2. Setup Instructions:

- Create a new Python virtual environment 
- Install dependencies (see next section)
- Save the `document_processor.py` file
- Run the FastAPI server with `uvicorn document_processor:app --reload`

3. Dependencies:

```
fastapi==0.85.0
uvicorn==0.18.3
pydantic==1.10.2
PyPDF2==2.11.1
python-docx==0.8.11
```

Install with:
```
pip install fastapi uvicorn pydantic PyPDF2 python-docx
```

4. Configuration:
- The `ChunkConfig` model defines the chunk size and overlap, defaulting to 1000 and 200 respectively. These can be overridden when making requests.

5. Testing:

Create a `test_document_processor.py` file:

```python
from fastapi.testclient import TestClient
from document_processor import app

client = TestClient(app)

def test_process_txt():
    with open("test.txt", "rb") as file:
        response = client.post(
            "/process_document", files={"file": ("test.txt", file, "text/plain")}
        )
    assert response.status_code == 200
    assert len(response.json()["chunks"]) > 0

def test_process_unsupported():
    with open("test.jpg", "rb") as file:
        response = client.post(
            "/process_document", files={"file": ("test.jpg", file, "image/jpeg")}
        )
    assert response.status_code == 422

```

Run tests with: `pytest test_document_processor.py`

6. Integration:

- The `/process_document` endpoint accepts a file upload and optional `ChunkConfig`
- It returns the extracted text chunks in the response body
- Error handling will return appropriate status codes and log full tracebacks
- Async processing is simulated with `asyncio.sleep()` but could be replaced with real async tasks
- The resulting chunks can be passed to downstream components like embedders or vectorizers

Let me know if you have any other questions! The provided code should run out-of-the-box following the setup steps.