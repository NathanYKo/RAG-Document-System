import time
from datetime import datetime
from typing import Dict, List, Optional

import altair as alt
import pandas as pd
import requests
import streamlit as st
from config import Config
from requests.exceptions import RequestException, Timeout
from utils import (
    SessionManager,
    apply_custom_css,
    format_file_size,
    format_timestamp,
    highlight_text,
    validate_email,
    validate_password,
)

# Configure page
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state="expanded",
)


class APIClient:
    """Enhanced API client with proper error handling and correct endpoints"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if include_auth and st.session_state.get("token"):
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Optional[Dict]:
        """Handle API response with proper error messages"""
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        elif response.status_code == 401:
            st.session_state.token = None
            st.session_state.user_data = None
            st.error("🔐 Session expired. Please login again.")
            st.rerun()
        elif response.status_code == 403:
            st.error("🚫 Access denied. Insufficient permissions.")
        elif response.status_code == 404:
            st.error("🔍 Resource not found.")
        elif response.status_code == 422:
            error_data = response.json()
            if "detail" in error_data:
                if isinstance(error_data["detail"], list):
                    errors = [
                        f"• {err.get('msg', str(err))}" for err in error_data["detail"]
                    ]
                    st.error("❌ Validation errors:\n" + "\n".join(errors))
                else:
                    st.error(f"❌ {error_data['detail']}")
        elif response.status_code == 429:
            st.error("⏱️ Rate limit exceeded. Please wait and try again.")
        else:
            try:
                error_data = response.json()
                st.error(
                    f"❌ API Error ({response.status_code}): {error_data.get('detail', 'Unknown error')}"
                )
            except:
                st.error(f"❌ HTTP Error {response.status_code}: {response.text}")
        return None

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return token data - FIXED ENDPOINT"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/token",  # CORRECTED ENDPOINT
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=Config.API_TIMEOUT,
            )
            return self._handle_response(response)
        except RequestException as e:
            st.error(f"🔌 Connection error: {str(e)}")
            return None

    def register(self, username: str, email: str, password: str) -> Optional[Dict]:
        """Register new user - FIXED ENDPOINT"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",  # CORRECTED ENDPOINT
                json={"username": username, "email": email, "password": password},
                timeout=Config.API_TIMEOUT,
            )
            return self._handle_response(response)
        except RequestException as e:
            st.error(f"🔌 Connection error: {str(e)}")
            return None

    def get_user_profile(self) -> Optional[Dict]:
        """Get current user profile"""
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self._get_headers(),
                timeout=Config.API_TIMEOUT,
            )
            return self._handle_response(response)
        except RequestException as e:
            st.error(f"🔌 Connection error: {str(e)}")
            return None

    def upload_document(
        self,
        file_data: bytes,
        filename: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Optional[Dict]:
        """Upload document with progress tracking - NO AUTH REQUIRED"""
        try:
            files = {"file": (filename, file_data, "application/octet-stream")}
            data = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
            # Removed authentication headers for testing

            response = requests.post(
                f"{self.base_url}/documents/upload",  # CORRECTED ENDPOINT
                files=files,
                data=data,
                timeout=Config.UPLOAD_TIMEOUT,
            )
            return self._handle_response(response)
        except Timeout:
            st.error("⏰ Upload timeout. Please try with a smaller file.")
            return None
        except RequestException as e:
            st.error(f"🔌 Upload error: {str(e)}")
            return None

    def query_documents(self, query: str, max_results: int = 5) -> Optional[Dict]:
        """Query documents with enhanced response handling - NO AUTH REQUIRED"""
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={
                    "query": query,
                    "max_results": max_results,
                    "include_metadata": True,
                },
                headers={"Content-Type": "application/json"},  # Removed auth headers
                timeout=Config.API_TIMEOUT,
            )
            return self._handle_response(response)
        except Timeout:
            st.error("⏰ Query timeout. Please try a simpler question.")
            return None
        except RequestException as e:
            st.error(f"🔌 Query error: {str(e)}")
            return None

    def get_documents(self) -> Optional[List[Dict]]:
        """Get user documents - NO AUTH REQUIRED"""
        try:
            response = requests.get(
                f"{self.base_url}/documents",
                headers={"Content-Type": "application/json"},  # Removed auth headers
                timeout=Config.API_TIMEOUT,
            )
            return self._handle_response(response)
        except RequestException as e:
            st.error(f"🔌 Connection error: {str(e)}")
            return None

    def submit_feedback(
        self,
        query_log_id: int,
        rating: int,
        comment: str = "",
        feedback_type: str = "general",
    ) -> Optional[Dict]:
        """Submit user feedback"""
        try:
            response = requests.post(
                f"{self.base_url}/feedback",
                json={
                    "query_log_id": query_log_id,
                    "rating": rating,
                    "comment": comment,
                    "feedback_type": feedback_type,
                },
                headers=self._get_headers(),
                timeout=Config.API_TIMEOUT,
            )
            return self._handle_response(response)
        except RequestException as e:
            st.error(f"🔌 Connection error: {str(e)}")
            return None


def render_sidebar():
    """Render navigation sidebar"""
    with st.sidebar:
        st.title("📚 Enterprise RAG")

        if SessionManager.is_authenticated():
            user_data = st.session_state.user_data or {}
            st.success(f"✅ Welcome, {user_data.get('username', 'User')}!")

            # User stats
            with st.expander("👤 Profile Stats", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Documents", user_data.get("total_documents", 0))
                with col2:
                    st.metric("Queries", user_data.get("total_queries", 0))

                if user_data.get("avg_confidence_score"):
                    st.metric(
                        "Avg. Confidence", f"{user_data['avg_confidence_score']:.2f}"
                    )

            # Navigation
            st.markdown("---")
            page = st.radio(
                "Navigation",
                ["🔍 Query", "📄 Documents", "📊 Analytics", "⚙️ Settings"],
                key="navigation",
            )

            st.markdown("---")
            if st.button("🚪 Logout", type="secondary"):
                SessionManager.clear_session()
                st.rerun()

            return page.split(" ", 1)[1]  # Return page name without emoji
        else:
            st.info("👋 Please login to continue")
            return "Login"


def render_login_page(api_client: APIClient):
    """Render enhanced login/registration page"""
    st.title("🔐 Authentication")

    # Check API connectivity
    try:
        response = requests.get(f"{Config.API_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ Connected to RAG System")
        else:
            st.warning("⚠️ RAG System may be experiencing issues")
    except:
        st.error(
            "❌ Cannot connect to RAG System. Please check if the backend is running."
        )
        return

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        st.subheader("Sign In")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )
            remember_me = st.checkbox("Remember me")

            if st.form_submit_button(
                "🔑 Sign In", type="primary", use_container_width=True
            ):
                if username and password:
                    with st.spinner("🔐 Authenticating..."):
                        auth_data = api_client.authenticate(username, password)
                        if auth_data:
                            st.session_state.token = auth_data["access_token"]
                            # Get user profile and STORE USERNAME - FIXED
                            profile_data = api_client.get_user_profile()
                            if profile_data:
                                st.session_state.user_data = profile_data
                                st.session_state.username = profile_data.get(
                                    "username", username
                                )  # FIXED
                            st.success("✅ Login successful!")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.error("Please enter both username and password")

    with tab2:
        st.subheader("Create Account")
        with st.form("register_form"):
            new_username = st.text_input(
                "Username*", placeholder="Choose a username (3-50 chars)"
            )
            new_email = st.text_input("Email", placeholder="your.email@example.com")
            new_password = st.text_input(
                "Password*",
                type="password",
                placeholder="Min 8 chars with uppercase, lowercase, and digit",
            )
            confirm_password = st.text_input("Confirm Password*", type="password")
            agree_terms = st.checkbox("I agree to the Terms of Service")

            if st.form_submit_button(
                "📝 Create Account", type="primary", use_container_width=True
            ):
                if not all([new_username, new_password, confirm_password, agree_terms]):
                    st.error("Please fill in all required fields and agree to terms")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Enhanced password validation - FIXED
                    is_valid, message = validate_password(new_password)
                    if not is_valid:
                        st.error(message)
                    elif new_email and not validate_email(new_email):
                        st.error("Please enter a valid email address")
                    else:
                        with st.spinner("📝 Creating account..."):
                            result = api_client.register(
                                new_username, new_email or None, new_password
                            )
                            if result:
                                st.success(
                                    "✅ Account created successfully! Please login."
                                )
                                time.sleep(2)
                                st.rerun()


def render_document_sources(sources: List[Dict], query: str):
    """Render enhanced source citations with highlighting - FIXED STRUCTURE"""
    if not sources:
        return

    st.subheader("📚 Sources & Citations")

    for i, source in enumerate(sources, 1):
        # Handle different source data structures from backend
        filename = source.get("filename", source.get("document_name", "Document"))
        content = source.get(
            "content", source.get("text", source.get("chunk_text", ""))
        )

        with st.expander(f"📄 Source {i}: {filename}", expanded=i == 1):
            col1, col2 = st.columns([3, 1])

            with col1:
                if content:
                    # Enhanced highlighting of query terms - FIXED
                    query_terms = [
                        term.strip() for term in query.lower().split() if len(term) > 2
                    ]
                    highlighted_content = highlight_text(content, query_terms)
                    st.markdown(highlighted_content)
                else:
                    st.info("Source content not available")

            with col2:
                # Source metadata
                st.markdown("**📋 Metadata**")
                if source.get("page_number"):
                    st.text(f"Page: {source['page_number']}")
                if source.get("chunk_id"):
                    st.text(f"Section: {source['chunk_id'][-8:]}")
                if source.get("score", source.get("similarity_score")):
                    score = source.get("score", source.get("similarity_score"))
                    st.text(f"Relevance: {score:.3f}")

                # Citation format
                st.markdown("**📎 Citation**")
                citation = filename
                if source.get("page_number"):
                    citation += f", p. {source['page_number']}"
                st.code(citation, language=None)


def render_query_page(api_client: APIClient):
    """Render enhanced query interface with real-time feedback"""
    st.title("🔍 Document Query System")

    # Query input with enhanced UI
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_area(
            "What would you like to know?",
            value=st.session_state.current_query,
            placeholder="Ask a question about your documents...",
            help="Enter your question in natural language. The system will search through your uploaded documents.",
            height=100,
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        max_results = st.selectbox("Max Results", [3, 5, 10, 15], index=1)
        include_metadata = st.checkbox("Include metadata", value=True)

    # Query button with better UX
    if st.button("🔍 Search Documents", type="primary", disabled=not query.strip()):
        st.session_state.current_query = query

        # Progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Step 1: Validate query
                status_text.text("🔍 Analyzing query...")
                progress_bar.progress(25)
                time.sleep(0.5)

                # Step 2: Search documents
                status_text.text("📚 Searching documents...")
                progress_bar.progress(50)

                # Make the actual query
                result = api_client.query_documents(query, max_results)

                if result:
                    progress_bar.progress(75)
                    status_text.text("✨ Generating response...")
                    time.sleep(0.5)

                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    time.sleep(0.5)

                    # Clear progress indicators
                    progress_container.empty()

                    # Store in history with FIXED result access
                    query_result = {
                        "query": query,
                        "result": result,
                        "timestamp": datetime.now(),
                    }
                    st.session_state.query_history.append(query_result)

                    # Display results with enhanced formatting - FIXED RESPONSE STRUCTURE
                    st.markdown("---")
                    st.subheader("💡 Answer")

                    # Main answer with confidence indicator - FIXED FIELD NAMES
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # Use correct field name from backend response
                        answer_text = result.get(
                            "answer", result.get("result", "No answer generated")
                        )
                        st.markdown(answer_text)
                    with col2:
                        confidence = result.get("confidence_score", 0)
                        if confidence > 0.8:
                            st.success(f"🎯 High confidence\n{confidence:.2f}")
                        elif confidence > 0.6:
                            st.warning(f"⚠️ Medium confidence\n{confidence:.2f}")
                        else:
                            st.error(f"🤔 Low confidence\n{confidence:.2f}")

                    # Enhanced source rendering - FIXED
                    if result.get("sources"):
                        render_document_sources(result["sources"], query)

                    # Processing time
                    processing_time = result.get("processing_time", 0)
                    st.caption(f"⏱️ Processed in {processing_time:.2f} seconds")

                    # Feedback section - FIXED session state reference
                    if result.get("id"):
                        render_feedback_section(
                            api_client, result.get("id"), answer_text
                        )

            except Exception as e:
                progress_container.empty()
                st.error(f"❌ Query failed: {str(e)}")

    # Query history
    if st.session_state.query_history:
        st.markdown("---")
        st.subheader("📋 Recent Queries")

        for i, item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            with st.expander(f"Query {i}: {item['query'][:50]}...", expanded=False):
                st.markdown(f"**Question:** {item['query']}")
                answer = item["result"].get(
                    "answer", item["result"].get("result", "N/A")
                )
                st.markdown(f"**Answer:** {answer}")
                st.caption(
                    f"Asked at {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                )


def render_feedback_section(api_client: APIClient, query_log_id: int, answer_text: str):
    """Render feedback collection interface - FIXED"""
    st.markdown("---")
    st.subheader("💬 Rate this Response")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        rating = st.slider(
            "Overall Rating", 1, 5, 3, help="Rate the quality of this response"
        )

    with col2:
        feedback_type = st.selectbox(
            "Feedback Category",
            ["general", "accuracy", "relevance", "speed"],
            format_func=lambda x: x.title(),
        )

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        was_helpful = st.checkbox("Was helpful")

    comment = st.text_area(
        "Additional Comments (Optional)", placeholder="Tell us how we can improve..."
    )

    if st.button("📤 Submit Feedback", type="secondary"):
        with st.spinner("Submitting feedback..."):
            result = api_client.submit_feedback(
                query_log_id=query_log_id,
                rating=rating,
                comment=comment,
                feedback_type=feedback_type,
            )
            if result:
                st.success("✅ Thank you for your feedback!")


def render_documents_page(api_client: APIClient):
    """Render enhanced document management page"""
    st.title("📄 Document Management")

    # Upload section
    st.subheader("📤 Upload Documents")

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=Config.ALLOWED_FILE_TYPES,
            accept_multiple_files=True,
            help=f"Supported formats: {', '.join(Config.ALLOWED_FILE_TYPES).upper()} (Max {Config.MAX_FILE_SIZE_MB}MB each)",
        )

    with col2:
        st.markdown("**⚙️ Processing Options**")
        chunk_size = st.slider(
            "Chunk Size", 500, 2000, Config.DEFAULT_CHUNK_SIZE, step=100
        )
        chunk_overlap = st.slider(
            "Overlap", 50, 500, Config.DEFAULT_CHUNK_OVERLAP, step=50
        )

    if uploaded_files and st.button("📤 Upload Documents", type="primary"):
        upload_container = st.container()

        for file in uploaded_files:
            with upload_container:
                st.info(f"📄 Processing: {file.name} ({format_file_size(file.size)})")
                progress_bar = st.progress(0)

                try:
                    # Validate file size
                    if file.size > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
                        st.error(
                            f"❌ File {file.name} is too large (max {Config.MAX_FILE_SIZE_MB}MB)"
                        )
                        continue

                    # Read file data
                    file_data = file.read()
                    file.seek(0)  # Reset file pointer

                    progress_bar.progress(25)

                    # Upload with progress tracking
                    result = api_client.upload_document(
                        file_data, file.name, chunk_size, chunk_overlap
                    )

                    if result:
                        progress_bar.progress(100)
                        st.success(f"✅ {file.name} uploaded successfully!")

                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {str(e)}")

        # Refresh document list
        time.sleep(1)
        st.rerun()

    # Document list
    st.markdown("---")
    st.subheader("📚 Your Documents")

    documents = api_client.get_documents()
    if documents:
        # Filter and search
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input(
                "🔍 Search documents", placeholder="Filter by filename..."
            )
        with col2:
            status_filter = st.selectbox(
                "Status", ["All", "completed", "processing", "failed"]
            )
        with col3:
            sort_by = st.selectbox("Sort by", ["Date", "Name", "Size"])

        # Filter documents
        filtered_docs = documents
        if search_term:
            filtered_docs = [
                doc
                for doc in filtered_docs
                if search_term.lower() in doc["filename"].lower()
            ]
        if status_filter != "All":
            filtered_docs = [
                doc
                for doc in filtered_docs
                if doc["processing_status"] == status_filter
            ]

        # Display documents with FIXED field names
        for doc in filtered_docs:
            with st.expander(f"📄 {doc['filename']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**File Type:** {doc['file_type'].upper()}")
                    st.write(f"**Chunks:** {doc.get('total_chunks', 'N/A')}")
                    created_at = format_timestamp(doc.get("created_at", ""))
                    st.write(f"**Uploaded:** {created_at}")

                with col2:
                    status = doc["processing_status"]
                    if status == "completed":
                        st.success(f"✅ {status.title()}")
                    elif status == "processing":
                        st.warning(f"⏳ {status.title()}")
                    else:
                        st.error(f"❌ {status.title()}")

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{doc['id']}"):
                        st.error("Delete functionality not implemented yet")
    else:
        st.info("📝 No documents uploaded yet. Upload your first document above!")


def render_analytics_page(api_client: APIClient):
    """Render comprehensive analytics dashboard - FIXED DATA STRUCTURE"""
    st.title("📊 Analytics Dashboard")

    # Get user profile for metrics
    user_data = st.session_state.user_data or {}
    documents = api_client.get_documents() or []

    # Key metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📄 Total Documents", user_data.get("total_documents", 0))
    with col2:
        st.metric("🔍 Total Queries", user_data.get("total_queries", 0))
    with col3:
        completed_docs = len(
            [d for d in documents if d.get("processing_status") == "completed"]
        )
        st.metric("✅ Processed Docs", completed_docs)
    with col4:
        avg_confidence = user_data.get("avg_confidence_score", 0)
        st.metric(
            "🎯 Avg Confidence", f"{avg_confidence:.2f}" if avg_confidence else "N/A"
        )

    # Document analytics
    if documents:
        st.subheader("📚 Document Analytics")

        # Create dataframe for visualizations with FIXED field names
        df = pd.DataFrame(documents)

        col1, col2 = st.columns(2)

        with col1:
            # Document status distribution
            if "processing_status" in df.columns:
                status_counts = df["processing_status"].value_counts()
                chart = (
                    alt.Chart(
                        pd.DataFrame(
                            {
                                "status": status_counts.index,
                                "count": status_counts.values,
                            }
                        )
                    )
                    .mark_arc()
                    .encode(
                        theta=alt.Theta(field="count", type="quantitative"),
                        color=alt.Color(
                            field="status",
                            type="nominal",
                            scale=alt.Scale(range=["#28a745", "#ffc107", "#dc3545"]),
                        ),
                        tooltip=["status", "count"],
                    )
                    .properties(
                        title="Document Processing Status", width=300, height=300
                    )
                )
                st.altair_chart(chart, use_container_width=True)

        with col2:
            # File type distribution
            if "file_type" in df.columns:
                type_counts = df["file_type"].value_counts()
                chart = (
                    alt.Chart(
                        pd.DataFrame(
                            {"type": type_counts.index, "count": type_counts.values}
                        )
                    )
                    .mark_bar()
                    .encode(
                        x=alt.X("type:N", title="File Type"),
                        y=alt.Y("count:Q", title="Count"),
                        color=alt.Color("type:N", legend=None),
                        tooltip=["type", "count"],
                    )
                    .properties(title="File Type Distribution", width=300, height=300)
                )
                st.altair_chart(chart, use_container_width=True)

    # Query history analytics - FIXED
    if st.session_state.query_history:
        st.subheader("🔍 Query Analytics")

        query_data = []
        for item in st.session_state.query_history:
            result = item["result"]
            query_data.append(
                {
                    "timestamp": item["timestamp"],
                    "query_length": len(item["query"]),
                    "confidence": result.get("confidence_score", 0),
                    "processing_time": result.get("processing_time", 0),
                    "sources_count": len(result.get("sources", [])),
                }
            )

        query_df = pd.DataFrame(query_data)

        col1, col2 = st.columns(2)

        with col1:
            # Confidence over time
            chart = (
                alt.Chart(query_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X("timestamp:T", title="Time"),
                    y=alt.Y(
                        "confidence:Q",
                        title="Confidence Score",
                        scale=alt.Scale(domain=[0, 1]),
                    ),
                    tooltip=["timestamp:T", "confidence:Q"],
                )
                .properties(title="Confidence Scores Over Time", width=400, height=300)
            )
            st.altair_chart(chart, use_container_width=True)

        with col2:
            # Processing time distribution
            chart = (
                alt.Chart(query_df)
                .mark_bar()
                .encode(
                    x=alt.X("processing_time:Q", bin=True, title="Processing Time (s)"),
                    y=alt.Y("count()", title="Count"),
                    tooltip=["count()"],
                )
                .properties(
                    title="Query Processing Time Distribution", width=400, height=300
                )
            )
            st.altair_chart(chart, use_container_width=True)


def render_settings_page(api_client: APIClient):
    """Render user settings and preferences"""
    st.title("⚙️ Settings")

    user_data = st.session_state.user_data or {}

    # Profile settings
    st.subheader("👤 Profile Information")
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Username", value=user_data.get("username", ""), disabled=True)
        st.text_input(
            "Email", value=user_data.get("email", ""), placeholder="No email set"
        )

    with col2:
        created_at = format_timestamp(user_data.get("created_at", ""))
        st.text_input("Member Since", value=created_at, disabled=True)
        is_admin = "Yes" if user_data.get("is_admin") else "No"
        st.text_input("Admin Status", value=is_admin, disabled=True)

    # API Configuration
    st.subheader("🔧 System Configuration")
    st.text_input("API URL", value=Config.API_URL, disabled=True)
    st.caption("Contact your administrator to change the API endpoint")

    # Query preferences
    st.subheader("🔍 Query Preferences")
    col1, col2 = st.columns(2)

    with col1:
        default_max_results = st.slider(
            "Default Max Results",
            3,
            20,
            SessionManager.get_user_preference("max_results", 5),
        )
        include_metadata_default = st.checkbox(
            "Include metadata by default",
            value=SessionManager.get_user_preference("include_metadata", True),
        )

    with col2:
        query_timeout = st.slider("Query Timeout (seconds)", 10, 60, Config.API_TIMEOUT)
        auto_save_queries = st.checkbox("Auto-save query history", value=True)

    # Document processing preferences
    st.subheader("📄 Document Processing")
    col1, col2 = st.columns(2)

    with col1:
        default_chunk_size = st.slider(
            "Default Chunk Size",
            500,
            2000,
            SessionManager.get_user_preference("chunk_size", 1000),
            step=100,
        )
    with col2:
        default_chunk_overlap = st.slider(
            "Default Chunk Overlap",
            50,
            500,
            SessionManager.get_user_preference("chunk_overlap", 200),
            step=50,
        )

    # Save settings button
    if st.button("💾 Save Settings", type="primary"):
        # Store preferences
        SessionManager.set_user_preference("max_results", default_max_results)
        SessionManager.set_user_preference("include_metadata", include_metadata_default)
        SessionManager.set_user_preference("chunk_size", default_chunk_size)
        SessionManager.set_user_preference("chunk_overlap", default_chunk_overlap)

        st.success("✅ Settings saved successfully!")
        st.info("ℹ️ Some settings will take effect after your next login.")


def main():
    """Main application entry point - TESTING MODE (NO AUTH)"""
    # Initialize session state
    SessionManager.init_session()

    # Apply custom styling
    apply_custom_css()

    # Create API client
    api_client = APIClient(Config.API_URL)

    # TESTING MODE: Skip authentication and go directly to document upload
    st.sidebar.markdown("## 🧪 Testing Mode")
    st.sidebar.info("Authentication disabled for testing")

    # Simple page navigation without auth
    current_page = st.sidebar.selectbox(
        "📍 Navigate", ["Documents", "Query", "Analytics", "Settings"]
    )

    # Render selected page directly
    if current_page == "Query":
        render_query_page(api_client)
    elif current_page == "Documents":
        render_documents_page(api_client)
    elif current_page == "Analytics":
        render_analytics_page(api_client)
    elif current_page == "Settings":
        render_settings_page(api_client)


if __name__ == "__main__":
    main()
