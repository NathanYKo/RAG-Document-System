#!/usr/bin/env python3
"""
Manual Frontend Test Guide for Enterprise RAG System
This script provides step-by-step instructions for manually testing the system.
"""

import requests
import webbrowser
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"

def check_services():
    """Check if both services are running"""
    print("🔍 Checking Services Status")
    print("=" * 50)
    
    # Check backend
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend: Running (Status: {health_data['status']})")
            print(f"   📊 Vector DB: {health_data['vector_database']['document_count']} documents")
        else:
            print(f"❌ Backend: Error (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Backend: Not accessible ({e})")
        return False
    
    # Check frontend
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Frontend: Running")
        else:
            print(f"❌ Frontend: Error (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Frontend: Not accessible ({e})")
        return False
    
    return True

def create_test_user():
    """Create a test user for manual testing"""
    print("\n🔍 Creating Test User")
    print("=" * 50)
    
    timestamp = int(time.time())
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 201:
            user_info = response.json()
            print(f"✅ Test user created successfully!")
            print(f"   👤 Username: {user_data['username']}")
            print(f"   🔐 Password: {user_data['password']}")
            print(f"   📧 Email: {user_data['email']}")
            return user_data
        else:
            print(f"❌ Failed to create test user: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

def print_manual_test_guide(user_data=None):
    """Print comprehensive manual testing guide"""
    print("\n" + "=" * 70)
    print("🧪 MANUAL TESTING GUIDE - Enterprise RAG System")
    print("=" * 70)
    
    print("\n📋 TEST CHECKLIST:")
    print("=" * 30)
    
    test_steps = [
        "✅ Backend Health Check",
        "✅ Frontend Accessibility", 
        "⬜ User Registration/Login",
        "⬜ Document Upload", 
        "⬜ Document Processing",
        "⬜ Query Functionality",
        "⬜ Response Quality",
        "⬜ Source Attribution",
        "⬜ User Interface",
        "⬜ Error Handling"
    ]
    
    for step in test_steps:
        print(f"  {step}")
    
    print(f"\n🌐 SYSTEM URLS:")
    print("=" * 30)
    print(f"  📋 Backend API Docs: {BACKEND_URL}/docs")
    print(f"  🖥️  Frontend Application: {FRONTEND_URL}")
    print(f"  ⚡ Health Check: {BACKEND_URL}/health")
    
    if user_data:
        print(f"\n👤 TEST USER CREDENTIALS:")
        print("=" * 30)
        print(f"  Username: {user_data['username']}")
        print(f"  Password: {user_data['password']}")
        print(f"  Email: {user_data['email']}")
    
    print(f"\n📝 TESTING INSTRUCTIONS:")
    print("=" * 30)
    
    instructions = [
        "1. Open the frontend URL in your web browser",
        "2. Test user registration with the provided credentials",
        "3. Test user login functionality", 
        "4. Upload a sample document (PDF, DOCX, or TXT)",
        "5. Wait for document processing to complete",
        "6. Test various queries related to your document",
        "7. Verify that responses include source attribution",
        "8. Test the feedback submission feature",
        "9. Check the analytics/dashboard if available",
        "10. Test error scenarios (invalid files, etc.)"
    ]
    
    for instruction in instructions:
        print(f"  {instruction}")
    
    print(f"\n📄 SAMPLE TEST DOCUMENTS:")
    print("=" * 30)
    print("  Create test files with the following content:")
    print("\n  📄 sample_company_policy.txt:")
    print("  ---")
    print("  Our company offers flexible working hours from 9 AM to 6 PM.")
    print("  All employees are entitled to 25 days of annual leave.")
    print("  Remote work is allowed up to 3 days per week.")
    print("  Health insurance is provided for all full-time employees.")
    print("  ---")
    
    print("\n  📄 sample_product_info.txt:")
    print("  ---")
    print("  Our flagship product is the SmartWidget 3000.")
    print("  It features AI-powered automation and cloud connectivity.")
    print("  The device supports WiFi, Bluetooth, and Ethernet connections.")
    print("  Battery life is up to 72 hours on a single charge.")
    print("  Price starts at $299 for the basic model.")
    print("  ---")
    
    print(f"\n🧪 SAMPLE TEST QUERIES:")
    print("=" * 30)
    queries = [
        "What are the working hours?",
        "How many vacation days do employees get?",
        "What is the price of SmartWidget 3000?",
        "What connectivity options are available?",
        "What is the battery life?",
        "Can I work remotely?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    
    print(f"\n✅ SUCCESS CRITERIA:")
    print("=" * 30)
    criteria = [
        "User can register and login successfully",
        "Documents upload and process without errors",
        "Queries return relevant responses",
        "Sources are properly attributed",
        "Interface is responsive and intuitive",
        "Error messages are clear and helpful"
    ]
    
    for criterion in criteria:
        print(f"  ✓ {criterion}")
    
    print(f"\n🚨 TROUBLESHOOTING:")
    print("=" * 30)
    troubleshooting = [
        "If upload fails: Check file type (PDF, DOCX, TXT only)",
        "If queries return no results: Wait for processing to complete",
        "If login fails: Check username/password spelling",
        "If frontend won't load: Verify Streamlit is running on port 8501",
        "If backend errors: Check the terminal logs for details"
    ]
    
    for tip in troubleshooting:
        print(f"  ⚠️  {tip}")

def open_browser():
    """Open the frontend in the default browser"""
    print(f"\n🌐 Opening frontend in browser...")
    try:
        webbrowser.open(FRONTEND_URL)
        print(f"✅ Browser opened to {FRONTEND_URL}")
        return True
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"   Please manually navigate to: {FRONTEND_URL}")
        return False

def main():
    """Main test function"""
    print("🚀 Enterprise RAG System - Manual Testing Setup")
    print("=" * 60)
    print(f"⏰ Test initiated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check services
    if not check_services():
        print("\n❌ Services are not running properly!")
        print("Please ensure both backend and frontend are started:")
        print(f"  Backend: source rag-env/bin/activate && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")
        print(f"  Frontend: cd frontend && source ../rag-env/bin/activate && streamlit run app.py --server.port 8501")
        return
    
    # Create test user
    user_data = create_test_user()
    
    # Print manual testing guide
    print_manual_test_guide(user_data)
    
    # Open browser
    print("\n" + "=" * 60)
    user_input = input("🌐 Would you like to open the frontend in your browser? (y/n): ")
    if user_input.lower() in ['y', 'yes']:
        open_browser()
    
    print(f"\n🎯 NEXT STEPS:")
    print("=" * 30)
    print("1. Follow the testing instructions above")
    print("2. Test each functionality thoroughly")
    print("3. Note any issues or unexpected behavior")
    print("4. Verify the system meets your requirements")
    
    print(f"\n✨ Happy Testing! ✨")

if __name__ == "__main__":
    main() 