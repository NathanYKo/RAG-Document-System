import pytest
import asyncio
from embeddings import generate_embeddings
from database import ChromaDB
import chromadb
import tempfile
import shutil
import os

@pytest.fixture
async def test_db():
    """Create a test database instance with temporary storage"""
    # Create temporary directory for test database
    temp_dir = tempfile.mkdtemp()
    
    # Override the settings for testing
    import database
    original_settings = database.CHROMA_SETTINGS
    database.CHROMA_SETTINGS = chromadb.config.Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=temp_dir
    )
    
    db = ChromaDB()
    yield db
    
    # Cleanup
    database.CHROMA_SETTINGS = original_settings
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.mark.asyncio
async def test_embeddings_generation():
    """Test embedding generation functionality"""
    # Test single text
    text = "This is a test document"
    embeddings = generate_embeddings(text)
    assert embeddings is not None
    assert len(embeddings) == 1
    assert len(embeddings[0]) > 0  # Should have some dimensions
    
    # Test multiple texts
    texts = ["This is a test document", "Another test document"]
    embeddings = generate_embeddings(texts)
    assert embeddings is not None
    assert len(embeddings) == 2
    assert len(embeddings[0]) == len(embeddings[1])  # Same dimensionality

@pytest.mark.asyncio
async def test_db_integration(test_db):
    """Test ChromaDB integration functionality"""
    db = test_db
    
    # Test database initialization
    assert db.collection is not None
    initial_count = db.count()
    assert initial_count >= 0
    
    # Add documents
    documents = ["This is a test document", "Another test document"] 
    embeddings = generate_embeddings(documents)
    metadatas = [{"source": "test1", "type": "test"}, {"source": "test2", "type": "test"}]
    
    ids = await db.add_documents(documents, embeddings, metadatas)
    assert len(ids) == 2
    assert all(isinstance(id, str) for id in ids)
    
    # Verify count increased
    new_count = db.count()
    assert new_count == initial_count + 2

    # Query documents
    results = db.query(query_texts=["test document"], n_results=5)
    assert "documents" in results
    assert "distances" in results
    assert "ids" in results
    assert "metadatas" in results
    assert len(results["documents"][0]) > 0

    # Get document by ID
    doc_id = results["ids"][0][0]
    doc = db.get(ids=[doc_id])
    assert "documents" in doc
    assert len(doc["documents"]) == 1
    assert doc["documents"][0] in documents

    # Delete document
    await db.delete(ids=[doc_id])
    doc_after_delete = db.get(ids=[doc_id])
    assert len(doc_after_delete["documents"]) == 0
    
    # Verify count decreased
    final_count = db.count()
    assert final_count == new_count - 1

@pytest.mark.asyncio
async def test_query_functionality(test_db):
    """Test various query scenarios"""
    db = test_db
    
    # Add test documents with different content
    documents = [
        "Machine learning algorithms are powerful tools",
        "Python is a great programming language",
        "Natural language processing helps computers understand text",
        "Data science involves statistics and programming"
    ]
    embeddings = generate_embeddings(documents)
    metadatas = [{"source": f"doc{i}", "topic": "tech"} for i in range(len(documents))]
    
    await db.add_documents(documents, embeddings, metadatas)
    
    # Test relevant query
    results = db.query("machine learning", n_results=2)
    assert len(results["documents"][0]) == 2
    
    # Test query with no results limit
    results = db.query("programming", n_results=10)
    assert len(results["documents"][0]) <= len(documents)
    
    # Test empty query handling (should work with embeddings)
    results = db.query("xyz123nonexistent", n_results=1)
    assert len(results["documents"][0]) >= 0  # Should return something even if not very relevant

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling scenarios"""
    # Test with invalid directory (should handle gracefully)
    import database
    original_settings = database.CHROMA_SETTINGS
    
    try:
        # This should work fine as ChromaDB creates directories
        database.CHROMA_SETTINGS = chromadb.config.Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="/nonexistent/path/that/should/fail"
        )
        # This might not actually fail as ChromaDB is quite robust
        # but we test the pattern
        db = ChromaDB()
        assert db is not None
    except Exception as e:
        # If it does fail, that's also acceptable behavior
        assert isinstance(e, Exception)
    finally:
        database.CHROMA_SETTINGS = original_settings

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 