
import requests
import streamlit as st

# Simple configuration
API_URL = "http://backend:8000"

st.set_page_config(page_title="RAG Document Upload Test", page_icon="📄", layout="wide")


def upload_document(file_data, filename):
    """Simple document upload function"""
    try:
        files = {"file": (filename, file_data, "application/octet-stream")}
        data = {"chunk_size": 1000, "chunk_overlap": 200}

        response = requests.post(
            f"{API_URL}/documents/upload", files=files, data=data, timeout=60
        )

        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None


def query_documents(query):
    """Simple query function"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query, "max_results": 5},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Query failed: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Query error: {str(e)}")
        return None


def get_documents():
    """Get documents list"""
    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.error(f"Error getting documents: {str(e)}")
        return []


# Main app
st.title("📄 RAG System - Document Upload Test")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Choose a page", ["Upload Documents", "Query Documents", "View Documents"]
)

if page == "Upload Documents":
    st.header("📤 Upload Documents")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("Upload Files", type="primary"):
            for file in uploaded_files:
                st.info(f"Uploading: {file.name}")

                # Read file data
                file_data = file.read()
                file.seek(0)

                # Upload
                result = upload_document(file_data, file.name)

                if result:
                    st.success(f"✅ {file.name} uploaded successfully!")
                    st.json(result)

elif page == "Query Documents":
    st.header("🔍 Query Documents")

    query = st.text_input("Enter your question:")

    if query and st.button("Search", type="primary"):
        with st.spinner("Searching..."):
            result = query_documents(query)

            if result:
                st.write("**Answer:**")
                st.write(result.get("answer", "No answer found"))

                st.write("**Confidence:**", result.get("confidence_score", 0))
                st.write(
                    "**Processing Time:**",
                    f"{result.get('processing_time', 0):.2f} seconds",
                )

                if result.get("sources"):
                    st.write("**Sources:**")
                    for i, source in enumerate(result["sources"], 1):
                        st.write(f"{i}. {source}")

elif page == "View Documents":
    st.header("📚 Document Library")

    documents = get_documents()

    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc['filename']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {doc['file_type']}")
                    st.write(f"**Chunks:** {doc.get('total_chunks', 'N/A')}")
                with col2:
                    st.write(f"**Status:** {doc['processing_status']}")
                    st.write(f"**ID:** {doc['id']}")
    else:
        st.info("No documents found. Upload some documents first!")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("🧪 Testing Mode - No Authentication Required")
