# Document Processing Pipeline

A FastAPI-based document processing pipeline that can parse PDF, DOCX, and TXT files, extract text, and create configurable text chunks for RAG (Retrieval-Augmented Generation) systems.

## Features

- **Multi-format Support**: Process PDF, DOCX, and TXT files
- **Configurable Chunking**: Customizable chunk size and overlap
- **Text Cleaning**: Automatic text normalization and cleaning
- **Async Processing**: Non-blocking file processing
- **Error Handling**: Comprehensive error handling and logging
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Testing Suite**: Complete test coverage with pytest

## Quick Start

### 1. Setup

```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn document_processor:app --reload
```

The server will start on `http://localhost:8000`

### 3. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Health Check
```
GET /
```
Returns server status.

### Process Document
```
POST /process_document
```

**Parameters:**
- `file`: Document file (PDF, DOCX, or TXT)
- `chunk_size`: Size of text chunks (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/process_document" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf" \
     -F "chunk_size=500" \
     -F "chunk_overlap=50"
```

**Response:**
```json
{
  "filename": "document.pdf",
  "total_chunks": 5,
  "chunk_size": 500,
  "chunk_overlap": 50,
  "original_text_length": 2458,
  "cleaned_text_length": 2401,
  "chunks": [
    "First chunk of text...",
    "Second chunk of text...",
    "..."
  ]
}
```

### Alternative JSON Endpoint
```
POST /process_document_json
```
Accepts JSON configuration in request body instead of form parameters.

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_document_processor.py -v

# Run with coverage
pytest test_document_processor.py --cov=document_processor
```

## Configuration

### ChunkConfig Model

```python
class ChunkConfig(BaseModel):
    size: int = 1000        # Characters per chunk
    overlap: int = 200      # Characters of overlap between chunks
```

### Environment Variables

No environment variables required for basic operation.

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid file type, missing filename, etc.)
- `500`: Internal server error

All errors include descriptive messages in the response.

## Supported File Types

- **PDF**: `.pdf` files using PyPDF2
- **DOCX**: `.docx` files using python-docx
- **TXT**: `.txt` files with UTF-8 or Latin-1 encoding

## Dependencies

- FastAPI: Web framework
- PyPDF2: PDF processing
- python-docx: DOCX processing
- Uvicorn: ASGI server
- Pydantic: Data validation
- pytest: Testing framework

## Integration

This pipeline is designed to integrate with downstream RAG components:

1. **Vector Database**: Processed chunks can be embedded and stored
2. **Search System**: Clean text enables better search results
3. **LLM Processing**: Structured chunks work well with language models

## Development

### Project Structure
```
├── document_processor.py      # Main application
├── test_document_processor.py # Test suite
├── requirements.txt           # Dependencies
├── setup.sh                  # Setup script
└── README.md                 # Documentation
```

### Adding New File Types

To add support for new file types:

1. Create a new processing function:
```python
def process_new_format(file_content: bytes) -> str:
    # Processing logic here
    return extracted_text
```

2. Add the file type check in the main endpoint:
```python
elif file.filename.lower().endswith(".new_ext"):
    text = process_new_format(file_content)
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
