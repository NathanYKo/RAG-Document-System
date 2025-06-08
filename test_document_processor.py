import pytest
import io
from fastapi.testclient import TestClient
from document_processor import app

client = TestClient(app)

def create_test_txt_file():
    """Create a test text file in memory"""
    content = "This is a test document. It contains multiple sentences. We will use this to test the document processing pipeline functionality."
    return io.BytesIO(content.encode('utf-8'))

def create_test_pdf_content():
    """Create a simple PDF content for testing"""
    # This is a minimal PDF content - in real testing, you'd want actual PDF files
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n196\n%%EOF"

def test_root_endpoint():
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Document Processing Pipeline is running"

def test_process_txt_file():
    """Test processing a text file"""
    test_file = create_test_txt_file()
    
    response = client.post(
        "/process_document",
        files={"file": ("test.txt", test_file, "text/plain")},
        data={"chunk_size": 50, "chunk_overlap": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "chunks" in data
    assert "filename" in data
    assert "total_chunks" in data
    assert data["filename"] == "test.txt"
    assert data["total_chunks"] > 0
    assert len(data["chunks"]) > 0

def test_process_txt_with_default_params():
    """Test processing a text file with default parameters"""
    test_file = create_test_txt_file()
    
    response = client.post(
        "/process_document",
        files={"file": ("test.txt", test_file, "text/plain")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["chunk_size"] == 1000
    assert data["chunk_overlap"] == 200

def test_process_unsupported_file():
    """Test processing an unsupported file type"""
    fake_image = io.BytesIO(b"fake image content")
    
    response = client.post(
        "/process_document",
        files={"file": ("test.jpg", fake_image, "image/jpeg")}
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_process_empty_filename():
    """Test processing with no filename"""
    test_file = create_test_txt_file()
    
    response = client.post(
        "/process_document",
        files={"file": ("", test_file, "text/plain")}
    )
    
    # FastAPI returns 422 for validation errors, not 400
    assert response.status_code == 422

def test_chunk_creation_edge_cases():
    """Test chunk creation with edge cases"""
    from document_processor import create_chunks, ChunkConfig
    
    # Test empty text
    config = ChunkConfig(size=10, overlap=2)
    chunks = create_chunks("", config)
    assert chunks == []
    
    # Test text shorter than chunk size
    short_text = "Short"
    chunks = create_chunks(short_text, config)
    assert len(chunks) == 1
    assert chunks[0] == "Short"
    
    # Test overlap larger than chunk size
    config_bad = ChunkConfig(size=5, overlap=10)
    text = "This is a test text for chunking"
    chunks = create_chunks(text, config_bad)
    assert len(chunks) > 0  # Should still work without infinite loop

def test_text_cleaning():
    """Test text cleaning functionality"""
    from document_processor import clean_text
    
    # Test multiple whitespace
    dirty_text = "This   has    multiple\n\n\nspaces   and   newlines\t\t"
    cleaned = clean_text(dirty_text)
    assert cleaned == "This has multiple spaces and newlines"
    
    # Test empty text
    assert clean_text("") == ""
    assert clean_text("   ") == ""

if __name__ == "__main__":
    pytest.main([__file__]) 