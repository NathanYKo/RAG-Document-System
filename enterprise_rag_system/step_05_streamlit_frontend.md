# Streamlit Frontend Implementation

**Generated:** 2025-06-07T21:01:05.177690

Here is a complete implementation of a Streamlit frontend with the requested features, integrated with the FastAPI backend from the previous step:

1. Code Files:

app.py:
```python
import streamlit as st
import requests
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder
import altair as alt
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")

def api_request(method, endpoint, data=None, files=None, headers=None):
    url = f"{API_URL}{endpoint}"
    if files:
        response = requests.request(method, url, files=files, headers=headers)
    else:
        response = requests.request(method, url, json=data, headers=headers)
    
    if response.status_code == 401:
        st.error("Unauthorized. Please login.")
    elif response.status_code == 200:
        return response.json()
    else:
        st.error(f"Request failed with status {response.status_code}")

def login(username, password):
    data = MultipartEncoder(fields={"username": username, "password": password})
    headers = {"Content-Type": data.content_type}
    response = api_request("POST", "/token", files=data, headers=headers)
    if response:
        token = response["access_token"]
        st.session_state["token"] = token

def signup(username, password):
    data = {"username": username, "password": password}
    response = api_request("POST", "/signup", data=data)
    if response:
        st.success("User created successfully. Please login.")

def upload_document(file):
    data = MultipartEncoder(fields={"file": file.read()})
    headers = {"Authorization": f"Bearer {st.session_state.token}", "Content-Type": data.content_type}
    response = api_request("POST", "/upload", files=data, headers=headers)
    if response:
        st.success("Document uploaded successfully.")

def query_documents(query):
    data = {"query": query}
    headers = {"Authorization": f"Bearer {st.session_state.token}"}  
    response = api_request("POST", "/query", data=data, headers=headers)
    if response:
        st.markdown(f"**Result:**\n\n{response['result']}")
        
        # Highlight sources
        sources = response["result"].split("Sources:")[1].strip()
        st.markdown(f"**Sources:** {sources}")

def get_user_documents():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = api_request("GET", "/documents", headers=headers)
    if response:
        return response

def create_feedback(query, result, score):
    data = {"query": query, "result": result, "score": score}
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    api_request("POST", "/feedback", data=data, headers=headers)

def main():
    st.set_page_config(page_title="RAG Frontend", layout="wide")

    if "token" not in st.session_state:
        st.session_state.token = None

    # Authentication
    if not st.session_state.token:
        st.write("## Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)

        st.write("## Sign Up")
        new_username = st.text_input("New Username") 
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            signup(new_username, new_password)
    else:
        st.write(f"Welcome, {st.session_state.username}!")
        
        # Document upload
        st.write("## Upload Document")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx"])
        if uploaded_file is not None:
            upload_document(uploaded_file)

        # Query interface  
        st.write("## Query")
        query = st.text_area("Enter your query")
        if st.button("Submit Query"):
            query_documents(query)

            score = st.slider("How relevant was the result?", 1, 5)
            if st.button("Submit Feedback"):
                create_feedback(query, st.session_state.result, score)
                st.success("Feedback submitted. Thank you!")

        # Analytics dashboard
        st.write("## Analytics")
        documents = get_user_documents()
        if documents:
            df = pd.DataFrame(documents)
            chart = alt.Chart(df).mark_bar().encode(
                x='name',
                y='chunk_count'
            ).properties(
                width=600,
                height=400
            )
            st.altair_chart(chart)

if __name__ == "__main__":
    main()
```

utils.py:
```python
import streamlit as st
from streamlit.components.v1 import html

def st_webpage(html_file, width=1000, height=800):
    """Display a local HTML file in a Streamlit app."""
    with open(html_file, "r") as f:
        source_code = f.read() 
    html(source_code, width=width, height=height, scrolling=True)
```

2. Setup Instructions:

- Follow the setup from previous steps for the FastAPI backend
- Install Streamlit and other dependencies (see next section)
- Set the `API_URL` environment variable to the URL of your FastAPI backend
- Create an `analytics.html` file with your analytics dashboard HTML (optional)
- Run the Streamlit app with `streamlit run app.py`

3. Dependencies:

```
streamlit==1.21.0
requests==2.28.2
requests-toolbelt==0.10.1
altair==4.2.2
pandas==1.5.3
```

Install with:
```
pip install streamlit requests requests-toolbelt altair pandas
```

4. Configuration:
- Set the `API_URL` environment variable to the URL of your FastAPI backend. Defaults to `http://localhost:8000` if not set.

5. Testing:

test_app.py:
```python
from unittest.mock import Mock, patch
import streamlit as st
from app import login, signup, upload_document, query_documents, get_user_documents, create_feedback

def test_login(monkeypatch):
    monkeypatch.setattr(st, "error", Mock())
    monkeypatch.setattr(st, "session_state", {"token": None})
    
    with patch("app.api_request") as mock_request:
        mock_request.return_value = {"access_token": "test_token"}
        login("testuser", "testpass")
        assert st.session_state.token == "test_token"

def test_signup(monkeypatch):
    monkeypatch.setattr(st, "success", Mock())

    with patch("app.api_request") as mock_request:  
        signup("newuser", "newpass")
        mock_request.assert_called_with("POST", "/signup", data={"username": "newuser", "password": "newpass"})
        st.success.assert_called_with("User created successfully. Please login.")

# Add more tests for other functions...
```

Run tests with:
```
pytest test_app.py
```

6. Integration:

- The frontend uses the `api_request` helper function to make requests to the FastAPI backend. Ensure the `API_URL` environment variable is set correctly.
- User authentication is handled by the `/token` and `/signup` endpoints in the backend. The frontend stores the access token in `st.session_state`.
- Document upload uses the `/upload` endpoint, passing the file as `multipart/form-data`.
- Queries are sent to the `/query` endpoint, and the results are displayed with source highlighting.
- User documents are retrieved from the `/documents` endpoint for the analytics dashboard.
- Feedback is submitted to the `/feedback` endpoint.
- The `st_webpage` utility function in `utils.py` can be used to embed an external HTML file, such as for the analytics dashboard. Create an `analytics.html` file with your dashboard code.

This Streamlit app provides a complete frontend for the RAG system, integrating with the FastAPI backend. It includes interfaces for document upload, querying, user authentication, feedback, and an analytics dashboard.

Let me know if you have any other questions! Follow the setup instructions to run the frontend and connect it to your backend.