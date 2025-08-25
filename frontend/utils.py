import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


def hash_password(password: str) -> str:
    """Simple password hashing for client-side validation"""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, "Password is valid"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    size_index = 0
    size = float(size_bytes)

    while size >= 1024 and size_index < len(size_names) - 1:
        size /= 1024
        size_index += 1

    return f"{size:.2f} {size_names[size_index]}"


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp


def get_status_color(status: str) -> str:
    """Get color for status indicators"""
    status_colors = {
        "completed": "#28a745",
        "processing": "#ffc107",
        "failed": "#dc3545",
        "cancelled": "#6c757d",
    }
    return status_colors.get(status.lower(), "#6c757d")


def get_confidence_color(confidence: float) -> str:
    """Get color based on confidence score"""
    if confidence >= 0.8:
        return "#28a745"  # Green
    elif confidence >= 0.6:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red


def highlight_text(text: str, terms: List[str]) -> str:
    """Highlight search terms in text"""
    if not terms:
        return text

    highlighted = text
    for term in terms:
        if len(term) > 2:  # Only highlight longer terms
            # Case-insensitive highlighting
            import re

            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f"**{term}**", highlighted)

    return highlighted


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def save_session_data(key: str, data: Any) -> None:
    """Save data to session state with JSON serialization"""
    try:
        if isinstance(data, (dict, list)):
            st.session_state[key] = json.dumps(data)
        else:
            st.session_state[key] = data
    except Exception as e:
        st.error(f"Failed to save session data: {e}")


def load_session_data(key: str) -> Any:
    """Load data from session state with JSON deserialization"""
    try:
        data = st.session_state.get(key)
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return data
    except Exception as e:
        st.error(f"Failed to load session data: {e}")
        return None


def create_download_link(data: str, filename: str, link_text: str) -> str:
    """Create a download link for text data"""
    import base64

    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href


def display_api_error(error_response: Dict) -> None:
    """Display formatted API error messages"""
    if isinstance(error_response, dict):
        if "detail" in error_response:
            detail = error_response["detail"]
            if isinstance(detail, list):
                # Validation errors
                for error in detail:
                    st.error(f"❌ {error.get('msg', str(error))}")
            else:
                st.error(f"❌ {detail}")
        else:
            st.error("❌ An unknown error occurred")
    else:
        st.error(f"❌ {str(error_response)}")


def check_file_type(file) -> bool:
    """Check if uploaded file type is supported"""
    allowed_types = ["pdf", "txt", "docx"]
    if file.type:
        file_extension = file.name.split(".")[-1].lower()
        return file_extension in allowed_types
    return False


def estimate_processing_time(file_size: int) -> str:
    """Estimate document processing time based on file size"""
    # Rough estimates based on file size
    if file_size < 1024 * 1024:  # < 1MB
        return "< 1 minute"
    elif file_size < 5 * 1024 * 1024:  # < 5MB
        return "1-3 minutes"
    elif file_size < 10 * 1024 * 1024:  # < 10MB
        return "3-5 minutes"
    else:
        return "5+ minutes"


class SessionManager:
    """Manage user session state and persistence"""

    @staticmethod
    def init_session():
        """Initialize session state variables"""
        defaults = {
            "token": None,
            "user_data": None,
            "current_query": "",
            "query_history": [],
            "selected_documents": [],
            "preferences": {
                "max_results": 5,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "include_metadata": True,
            },
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def clear_session():
        """Clear all session data"""
        keys_to_clear = [
            "token",
            "user_data",
            "current_query",
            "query_history",
            "selected_documents",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return st.session_state.get("token") is not None

    @staticmethod
    def get_user_preference(key: str, default=None):
        """Get user preference with fallback"""
        preferences = st.session_state.get("preferences", {})
        return preferences.get(key, default)

    @staticmethod
    def set_user_preference(key: str, value):
        """Set user preference"""
        if "preferences" not in st.session_state:
            st.session_state.preferences = {}
        st.session_state.preferences[key] = value


def apply_custom_css():
    """Apply custom CSS styling to the Streamlit app"""
    st.markdown(
        """
    <style>
        /* Main app styling */
        .main > div {
            padding-top: 2rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Progress bar styling */
        .stProgress > div > div > div > div {
            background-color: #1f77b4;
        }
        
        /* Metric cards */
        .metric-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
            border: 1px solid #e0e0e0;
        }
        
        /* Source highlighting */
        .source-highlight {
            background-color: #fff3cd;
            padding: 0.5rem;
            border-left: 4px solid #ffc107;
            margin: 0.5rem 0;
            border-radius: 0.25rem;
        }
        
        /* Status badges */
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-completed {
            background-color: #d4edda;
            color: #155724;
        }
        
        .status-processing {
            background-color: #fff3cd;
            color: #856404;
        }
        
        .status-failed {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        /* Custom buttons */
        .stButton > button {
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* File uploader styling */
        .stFileUploader > div > div {
            border: 2px dashed #ccc;
            border-radius: 0.5rem;
            padding: 2rem;
            text-align: center;
        }
        
        /* Query input styling */
        .stTextArea > div > div > textarea {
            border-radius: 0.5rem;
            border: 2px solid #e0e0e0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
        }
        
        /* Alert styling */
        .stAlert {
            border-radius: 0.5rem;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """,
        unsafe_allow_html=True,
    )
