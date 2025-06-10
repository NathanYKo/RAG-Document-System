#!/usr/bin/env python3
"""
Integration test script for the Enterprise RAG System
Tests both backend API and frontend functionality.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"

def test_backend_health():
    """Test backend health endpoint"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend health: {health_data['status']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_frontend_health():
    """Test frontend accessibility"""
    print("🔍 Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend accessibility failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("🔍 Testing user registration...")
    try:
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 201:
            user_info = response.json()
            print(f"✅ User registered successfully: {user_info['username']}")
            return user_data
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ User registration error: {e}")
        return None

def test_user_login(user_data: Dict[str, str]):
    """Test user login"""
    print("🔍 Testing user login...")
    try:
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
            print(f"✅ User login successful")
            return token_data["access_token"]
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ User login error: {e}")
        return None

def test_protected_endpoint(token: str):
    """Test accessing protected endpoint"""
    print("🔍 Testing protected endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BACKEND_URL}/users/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Protected endpoint access successful: {user_info['username']}")
            return True
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Integration Tests for Enterprise RAG System")
    print("=" * 60)
    
    # Track test results
    results = []
    
    # Test backend health
    results.append(("Backend Health", test_backend_health()))
    
    # Test frontend health
    results.append(("Frontend Health", test_frontend_health()))
    
    # Test user registration
    user_data = test_user_registration()
    results.append(("User Registration", user_data is not None))
    
    if user_data:
        # Test user login
        token = test_user_login(user_data)
        results.append(("User Login", token is not None))
        
        if token:
            # Test protected endpoint
            results.append(("Protected Endpoint", test_protected_endpoint(token)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
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
        print("🎉 All tests passed! Backend and frontend are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the logs above.")
    
    print("\n🌐 Access URLs:")
    print(f"   Backend API: {BACKEND_URL}/docs")
    print(f"   Frontend UI: {FRONTEND_URL}")

if __name__ == "__main__":
    main() 