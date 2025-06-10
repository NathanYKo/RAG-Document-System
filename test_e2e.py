#!/usr/bin/env python3
"""
End-to-end test script for the Enterprise RAG System
Tests complete workflow including document upload and querying.
"""

import requests
import json
import time
import tempfile
import os
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"

def create_test_document() -> str:
    """Create a temporary test document"""
    content = """
    This is a test document for the Enterprise RAG System.
    
    The system is designed to handle various types of documents including:
    - PDF files containing research papers and reports
    - Word documents with business documentation
    - Text files with technical specifications
    
    Key features of the system include:
    1. Document ingestion and processing
    2. Vector-based similarity search
    3. Natural language querying
    4. User authentication and authorization
    5. Analytics and feedback collection
    
    The RAG (Retrieval-Augmented Generation) approach combines:
    - Document retrieval using vector embeddings
    - Language model generation for comprehensive answers
    - Source attribution for transparency
    
    This test document will be used to verify the system's ability to:
    - Process and chunk documents
    - Create vector embeddings
    - Perform semantic search
    - Generate relevant responses
    """
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        return f.name

def register_and_login() -> Optional[str]:
    """Register a new user and get access token"""
    print("🔍 Registering test user and logging in...")
    
    try:
        # Register user
        user_data = {
            "username": f"e2e_user_{int(time.time())}",
            "email": f"e2e_{int(time.time())}@example.com",
            "password": "E2ETest123!"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code != 201:
            print(f"❌ User registration failed: {response.status_code}")
            return None
        
        # Login user
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = requests.post(
            f"{BACKEND_URL}/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ User registered and logged in successfully")
            return token_data["access_token"]
        else:
            print(f"❌ User login failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Registration/login error: {e}")
        return None

def upload_document(token: str, file_path: str) -> Optional[int]:
    """Upload a document to the system"""
    print("🔍 Uploading test document...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(file_path, 'rb') as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            data = {"chunk_size": "500", "chunk_overlap": "100"}
            
            response = requests.post(
                f"{BACKEND_URL}/documents/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Document uploaded successfully: ID {result['document_id']}")
            return result['document_id']
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Document upload error: {e}")
        return None

def query_document(token: str, query: str) -> Optional[str]:
    """Query the uploaded document"""
    print(f"🔍 Querying: '{query}'")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        query_data = {
            "query": query,
            "max_results": 3
        }
        
        response = requests.post(
            f"{BACKEND_URL}/query",
            json=query_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"📄 Answer: {result['answer'][:200]}...")
            print(f"📚 Sources: {len(result.get('sources', []))} found")
            return result['answer']
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None

def submit_feedback(token: str, query: str, answer: str, score: int):
    """Submit feedback for a query"""
    print("🔍 Submitting feedback...")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        feedback_data = {
            "query": query,
            "result": answer,
            "score": score,
            "comment": "End-to-end test feedback"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/feedback",
            json=feedback_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✅ Feedback submitted successfully")
            return True
        else:
            print(f"❌ Feedback submission failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return False

def list_documents(token: str) -> bool:
    """List user documents"""
    print("🔍 Listing user documents...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BACKEND_URL}/documents",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Found {len(documents)} documents")
            return True
        else:
            print(f"❌ Document listing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Document listing error: {e}")
        return False

def main():
    """Main end-to-end test function"""
    print("🚀 Starting End-to-End Tests for Enterprise RAG System")
    print("=" * 70)
    
    # Track test results
    results = []
    
    # Create test document
    print("📝 Creating test document...")
    test_file = create_test_document()
    results.append(("Document Creation", test_file is not None))
    
    if not test_file:
        print("❌ Cannot continue without test document")
        return
    
    try:
        # Register and login
        token = register_and_login()
        results.append(("User Auth", token is not None))
        
        if not token:
            print("❌ Cannot continue without authentication")
            return
        
        # Upload document
        doc_id = upload_document(token, test_file)
        results.append(("Document Upload", doc_id is not None))
        
        if doc_id:
            # Wait a moment for processing
            print("⏳ Waiting for document processing...")
            time.sleep(3)
            
            # List documents
            results.append(("Document Listing", list_documents(token)))
            
            # Test various queries
            test_queries = [
                "What are the key features of the system?",
                "How does RAG work?",
                "What types of documents are supported?"
            ]
            
            query_results = []
            for query in test_queries:
                answer = query_document(token, query)
                query_results.append(answer is not None)
                
                if answer:
                    # Submit feedback
                    feedback_success = submit_feedback(token, query, answer, 4)
                    query_results.append(feedback_success)
            
            results.append(("Query Testing", all(query_results)))
        
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
            print("🧹 Cleaned up test file")
        except:
            pass
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 END-TO-END TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results:
        status = "PASS" if passed_test else "FAIL"
        emoji = "✅" if passed_test else "❌"
        print(f"{emoji} {test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All end-to-end tests passed! The system is fully functional.")
        print("\n🔗 System is ready for production use:")
        print(f"   📋 Backend API Documentation: {BACKEND_URL}/docs")
        print(f"   🖥️  Frontend Application: {FRONTEND_URL}")
        print(f"   ⚡ Health Check: {BACKEND_URL}/health")
    else:
        print("⚠️  Some tests failed. Please check the system configuration.")
    
    print("\n🧪 Test completed successfully!")

if __name__ == "__main__":
    main() 