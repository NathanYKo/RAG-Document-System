#!/usr/bin/env python3
"""
Simple API Test for Enterprise RAG System Backend
Tests core API functionality without complex workflows.
"""

import requests
import json
import tempfile
import os
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   OpenAI: {data['openai']}")
            print(f"   Vector DB Documents: {data['vector_database']['document_count']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n🔍 Testing Root Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint working")
            print(f"   Message: {data['message']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_admin_login():
    """Test admin user login"""
    print("\n🔍 Testing Admin Login...")
    try:
        login_data = {
            "username": "admin",
            "password": "Admin123!"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Admin login successful")
            print(f"   Token type: {token_data['token_type']}")
            print(f"   Expires in: {token_data['expires_in']} seconds")
            return token_data["access_token"]
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None

def test_user_profile(token):
    """Test getting user profile"""
    print("\n🔍 Testing User Profile...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BACKEND_URL}/users/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User profile retrieved")
            print(f"   Username: {user_data['username']}")
            print(f"   Is Admin: {user_data['is_admin']}")
            print(f"   Total Documents: {user_data.get('total_documents', 'N/A')}")
            return True
        else:
            print(f"❌ User profile failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User profile error: {e}")
        return False

def test_documents_list(token):
    """Test listing documents"""
    print("\n🔍 Testing Documents List...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BACKEND_URL}/documents",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Documents list retrieved")
            print(f"   Document count: {len(documents)}")
            for doc in documents[:3]:  # Show first 3 documents
                print(f"   📄 {doc['filename']} ({doc['file_type']}) - {doc['total_chunks']} chunks")
            return True
        else:
            print(f"❌ Documents list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Documents list error: {e}")
        return False

def test_simple_query(token):
    """Test a simple query"""
    print("\n🔍 Testing Simple Query...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        query_data = {
            "query": "What information is available?",
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
            print(f"✅ Query executed successfully")
            print(f"   Query: {result['query']}")
            print(f"   Answer length: {len(result['answer'])} characters")
            print(f"   Sources found: {len(result.get('sources', []))}")
            print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            if result.get('sources'):
                print(f"   First source preview: {result['sources'][0]['content_preview'][:100]}...")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def test_api_docs():
    """Test API documentation endpoint"""
    print("\n🔍 Testing API Documentation...")
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ API docs accessible")
            print(f"   Content length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Simple API Test - Enterprise RAG System Backend")
    print("=" * 65)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Backend URL: {BACKEND_URL}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("API Documentation", test_api_docs()))
    
    # Login and get token
    token = test_admin_login()
    results.append(("Admin Login", token is not None))
    
    if token:
        results.append(("User Profile", test_user_profile(token)))
        results.append(("Documents List", test_documents_list(token)))
        results.append(("Simple Query", test_simple_query(token)))
    
    # Print summary
    print("\n" + "=" * 65)
    print("📊 TEST SUMMARY")
    print("=" * 65)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results:
        status = "PASS" if passed_test else "FAIL"
        emoji = "✅" if passed_test else "❌"
        print(f"{emoji} {test_name:<20} {status}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All API tests passed! Backend is working correctly.")
    elif passed > total * 0.7:
        print("⚠️  Most tests passed. Minor issues detected.")
    else:
        print("❌ Multiple test failures. Please check backend configuration.")
    
    print(f"\n🔗 Useful URLs:")
    print(f"   📋 API Documentation: {BACKEND_URL}/docs")
    print(f"   ⚡ Health Check: {BACKEND_URL}/health")
    print(f"   🔍 OpenAPI Spec: {BACKEND_URL}/openapi.json")
    
    print(f"\n✅ API testing completed!")

if __name__ == "__main__":
    main() 