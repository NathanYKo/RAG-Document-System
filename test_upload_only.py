#!/usr/bin/env python3
"""
Simple test script to debug document upload issue
"""

import requests
import tempfile
import os
import time

BACKEND_URL = "http://127.0.0.1:8000"

def create_simple_test_file():
    """Create a simple test file"""
    content = "This is a simple test document. It contains basic information to test the upload functionality."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        return f.name

def get_admin_token():
    """Get admin token"""
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
        return token_data["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_upload_simple():
    """Test simple document upload"""
    print("Testing simple document upload...")
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("Failed to get admin token")
        return False
    
    # Create test file
    test_file = create_simple_test_file()
    print(f"Created test file: {test_file}")
    
    try:
        # Upload with minimal data
        with open(test_file, 'rb') as f:
            files = {'file': ('simple_test.txt', f, 'text/plain')}
            headers = {'Authorization': f'Bearer {token}'}
            
            print("Making upload request...")
            response = requests.post(
                f"{BACKEND_URL}/documents/upload",
                files=files,
                headers=headers,
                timeout=60
            )
            
            print(f"Upload response status: {response.status_code}")
            if response.status_code != 201:
                print(f"Upload failed: {response.text}")
                return False
            else:
                result = response.json()
                print(f"Upload successful: {result}")
                return True
                
    except Exception as e:
        print(f"Upload error: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(test_file)
        except:
            pass

if __name__ == "__main__":
    success = test_upload_simple()
    print(f"Upload test: {'PASSED' if success else 'FAILED'}") 