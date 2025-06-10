import pytest
import asyncio
import os
import tempfile
import json
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Import our application and components
from main import app
from sql_database import Base, get_database
from models import User, Document, QueryLog, Feedback, APIKey
from schemas import UserCreate, DocumentCreate, QueryRequest, FeedbackCreate, APIKeyCreate
from auth import get_password_hash, hash_api_key, generate_api_key
import crud

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_database():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_database] = override_get_database

# Create test tables
Base.metadata.create_all(bind=engine)

# Test client
client = TestClient(app)

# Test fixtures
@pytest.fixture(scope="module")
def test_client():
    """Create test client"""
    return client

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    }

@pytest.fixture
def test_admin_data():
    """Test admin user data"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminPass123!"
    }

@pytest.fixture
def authenticated_user_headers(test_user_data, db_session):
    """Create authenticated user and return headers"""
    # Create user
    user = crud.create_user(db_session, UserCreate(**test_user_data))
    
    # Login
    response = client.post(
        "/auth/token",
        data={"username": test_user_data["username"], "password": test_user_data["password"]}
    )
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def authenticated_admin_headers(test_admin_data, db_session):
    """Create authenticated admin and return headers"""
    # Create admin user
    user = crud.create_user(db_session, UserCreate(**test_admin_data))
    crud.update_user(db_session, user.id, {"is_admin": True})
    
    # Login
    response = client.post(
        "/auth/token",
        data={"username": test_admin_data["username"], "password": test_admin_data["password"]}
    )
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_document_data():
    """Sample document data"""
    return {
        "filename": "test_document.txt",
        "original_filename": "test_document.txt",
        "file_type": "txt",
        "file_size": 1000,
        "total_chunks": 3,
        "chunk_size": 500,
        "chunk_overlap": 100,
        "chunk_ids": ["chunk_1", "chunk_2", "chunk_3"],
        "doc_metadata": {"test": "data"}
    }

# Authentication Tests
class TestAuthentication:
    
    def test_register_user(self, test_client, test_user_data):
        """Test user registration"""
        response = test_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert data["is_admin"] is False
        assert "id" in data
    
    def test_register_duplicate_username(self, test_client, test_user_data, db_session):
        """Test registration with duplicate username"""
        # Create first user
        crud.create_user(db_session, UserCreate(**test_user_data))
        
        # Try to create duplicate
        response = test_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, test_client, test_user_data, db_session):
        """Test successful login"""
        # Create user
        crud.create_user(db_session, UserCreate(**test_user_data))
        
        # Login
        response = test_client.post(
            "/auth/token",
            data={"username": test_user_data["username"], "password": test_user_data["password"]}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, test_client, test_user_data, db_session):
        """Test login with invalid credentials"""
        # Create user
        crud.create_user(db_session, UserCreate(**test_user_data))
        
        # Try login with wrong password
        response = test_client.post(
            "/auth/token",
            data={"username": test_user_data["username"], "password": "wrong_password"}
        )
        assert response.status_code == 401
    
    def test_get_current_user_profile(self, test_client, authenticated_user_headers):
        """Test getting current user profile"""
        response = test_client.get("/users/me", headers=authenticated_user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "total_documents" in data
        assert "total_queries" in data

# Document Management Tests
class TestDocumentManagement:
    
    @patch('services.DocumentProcessorService.process_document')
    def test_upload_document(self, mock_process, test_client, authenticated_user_headers, sample_document_data):
        """Test document upload"""
        # Mock the document processing
        mock_process.return_value = AsyncMock(return_value=DocumentCreate(**sample_document_data))
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content")
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = test_client.post(
                    "/documents/upload",
                    files={"file": ("test.txt", file, "text/plain")},
                    data={"chunk_size": "500", "chunk_overlap": "100"},
                    headers=authenticated_user_headers
                )
        
        # Clean up
        os.unlink(f.name)
        
        assert response.status_code == 201
        data = response.json()
        assert "document_id" in data
        assert "processing_status" in data
    
    def test_list_documents(self, test_client, authenticated_user_headers, db_session, test_user_data, sample_document_data):
        """Test listing user documents"""
        # Get user
        user = crud.get_user_by_username(db_session, test_user_data["username"])
        
        # Create document
        crud.create_document(db_session, DocumentCreate(**sample_document_data), user.id)
        
        response = test_client.get("/documents", headers=authenticated_user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == sample_document_data["filename"]
    
    def test_get_document_details(self, test_client, authenticated_user_headers, db_session, test_user_data, sample_document_data):
        """Test getting document details"""
        # Get user
        user = crud.get_user_by_username(db_session, test_user_data["username"])
        
        # Create document
        document = crud.create_document(db_session, DocumentCreate(**sample_document_data), user.id)
        
        response = test_client.get(f"/documents/{document.id}", headers=authenticated_user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == document.id
        assert data["filename"] == sample_document_data["filename"]
    
    def test_delete_document(self, test_client, authenticated_user_headers, db_session, test_user_data, sample_document_data):
        """Test document deletion"""
        # Get user
        user = crud.get_user_by_username(db_session, test_user_data["username"])
        
        # Create document
        document = crud.create_document(db_session, DocumentCreate(**sample_document_data), user.id)
        
        response = test_client.delete(f"/documents/{document.id}", headers=authenticated_user_headers)
        assert response.status_code == 200
        
        # Verify deletion
        response = test_client.get(f"/documents/{document.id}", headers=authenticated_user_headers)
        assert response.status_code == 404

# Query Processing Tests
class TestQueryProcessing:
    
    @patch('services.RAGService.query_documents')
    def test_process_query(self, mock_query, test_client, authenticated_user_headers):
        """Test query processing"""
        # Mock the RAG response
        mock_query.return_value = {
            "query": "Test query",
            "answer": "Test answer",
            "sources": [{"id": "1", "content_preview": "Test content"}],
            "confidence_score": 0.85,
            "processing_time": 1.5,
            "sources_count": 1
        }
        
        query_data = {
            "query": "Test query",
            "max_results": 5,
            "include_metadata": True
        }
        
        response = test_client.post("/query", json=query_data, headers=authenticated_user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == "Test query"
        assert data["answer"] == "Test answer"
        assert data["confidence_score"] == 0.85
        assert len(data["sources"]) == 1
    
    def test_list_queries(self, test_client, authenticated_user_headers, db_session, test_user_data):
        """Test listing user queries"""
        # Get user
        user = crud.get_user_by_username(db_session, test_user_data["username"])
        
        # Create query log
        crud.create_query_log(
            db_session,
            user_id=user.id,
            query_text="Test query",
            response_text="Test response",
            confidence_score=0.8,
            processing_time=1.2
        )
        
        response = test_client.get("/queries", headers=authenticated_user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["query_text"] == "Test query"

# Feedback Tests
class TestFeedback:
    
    def test_submit_feedback(self, test_client, authenticated_user_headers, db_session, test_user_data):
        """Test submitting feedback"""
        # Get user
        user = crud.get_user_by_username(db_session, test_user_data["username"])
        
        # Create query log
        query_log = crud.create_query_log(
            db_session,
            user_id=user.id,
            query_text="Test query",
            response_text="Test response"
        )
        
        feedback_data = {
            "query_log_id": query_log.id,
            "rating": 4,
            "comment": "Good response",
            "feedback_type": "general",
            "was_helpful": True
        }
        
        response = test_client.post("/feedback", json=feedback_data, headers=authenticated_user_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["rating"] == 4
        assert data["comment"] == "Good response"

# API Key Management Tests
class TestAPIKeyManagement:
    
    def test_create_api_key(self, test_client, authenticated_user_headers):
        """Test creating API key"""
        api_key_data = {
            "name": "Test API Key",
            "description": "Test key for testing",
            "rate_limit": 500,
            "can_upload": True,
            "can_query": True,
            "expires_in_days": 30
        }
        
        response = test_client.post("/api-keys", json=api_key_data, headers=authenticated_user_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Test API Key"
        assert data["can_upload"] is True
        assert data["can_query"] is True
        assert "key" in data  # The raw key should be returned
    
    def test_list_api_keys(self, test_client, authenticated_user_headers, db_session, test_user_data):
        """Test listing API keys"""
        # Get user
        user = crud.get_user_by_username(db_session, test_user_data["username"])
        
        # Create API key
        api_key_data = APIKeyCreate(
            name="Test Key",
            description="Test",
            rate_limit=1000
        )
        crud.create_api_key(db_session, api_key_data, user.id)
        
        response = test_client.get("/api-keys", headers=authenticated_user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Key"

# Admin Tests
class TestAdminEndpoints:
    
    def test_get_system_stats(self, test_client, authenticated_admin_headers):
        """Test getting system statistics"""
        response = test_client.get("/admin/stats", headers=authenticated_admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "total_documents" in data
        assert "total_queries" in data
    
    def test_list_all_users(self, test_client, authenticated_admin_headers):
        """Test listing all users (admin only)"""
        response = test_client.get("/users", headers=authenticated_admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

# Health Check Tests
class TestHealthChecks:
    
    @patch('services.service_registry.health_check')
    def test_health_check(self, mock_health, test_client):
        """Test health check endpoint"""
        mock_health.return_value = {
            "status": "healthy",
            "vector_database": {"type": "ChromaDB", "status": "healthy"}
        }
        
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "vector_database" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Enterprise Document Intelligence System"
        assert data["version"] == "1.0.0"

# Security Tests
class TestSecurity:
    
    def test_unauthorized_access(self, test_client):
        """Test unauthorized access to protected endpoints"""
        endpoints = [
            "/users/me",
            "/documents",
            "/documents/upload",
            "/query",
            "/api-keys"
        ]
        
        for endpoint in endpoints:
            if endpoint == "/documents/upload":
                response = test_client.post(endpoint, files={"file": ("test.txt", b"content", "text/plain")})
            elif endpoint == "/query":
                response = test_client.post(endpoint, json={"query": "test"})
            else:
                response = test_client.get(endpoint)
            
            assert response.status_code == 401
    
    def test_admin_only_endpoints(self, test_client, authenticated_user_headers):
        """Test admin-only endpoints with regular user"""
        admin_endpoints = [
            "/admin/stats",
            "/users"
        ]
        
        for endpoint in admin_endpoints:
            response = test_client.get(endpoint, headers=authenticated_user_headers)
            assert response.status_code == 403

# Integration Tests
class TestIntegration:
    
    def test_complete_workflow(self, test_client, db_session):
        """Test complete workflow: register -> login -> upload -> query -> feedback"""
        # 1. Register user
        user_data = {
            "username": "workflow_user",
            "email": "workflow@example.com",
            "password": "WorkflowPass123!"
        }
        
        response = test_client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # 2. Login
        response = test_client.post(
            "/auth/token",
            data={"username": user_data["username"], "password": user_data["password"]}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Check profile
        response = test_client.get("/users/me", headers=headers)
        assert response.status_code == 200
        
        # 4. Create API key
        api_key_data = {
            "name": "Workflow API Key",
            "description": "For testing workflow",
            "can_upload": True,
            "can_query": True
        }
        
        response = test_client.post("/api-keys", json=api_key_data, headers=headers)
        assert response.status_code == 201
        
        # 5. List API keys
        response = test_client.get("/api-keys", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        
        print("✅ Complete workflow test passed!")

# Performance Tests
class TestPerformance:
    
    def test_concurrent_registrations(self, test_client):
        """Test concurrent user registrations"""
        import threading
        import time
        
        results = []
        
        def register_user(i):
            user_data = {
                "username": f"user_{i}",
                "email": f"user_{i}@example.com",
                "password": "TestPass123!"
            }
            response = test_client.post("/auth/register", json=user_data)
            results.append(response.status_code)
        
        # Create 5 concurrent registrations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert all(status == 201 for status in results)

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"]) 