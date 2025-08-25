import os
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # API Configuration
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "300"))

    # UI Configuration
    PAGE_TITLE = os.getenv("PAGE_TITLE", "Enterprise RAG System")
    PAGE_ICON = os.getenv("PAGE_ICON", "📚")
    LAYOUT = os.getenv("LAYOUT", "wide")

    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "pdf,txt,docx").split(",")

    # Query Configuration
    DEFAULT_MAX_RESULTS = int(os.getenv("DEFAULT_MAX_RESULTS", "5"))
    DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
    DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "200"))

    # Session Configuration
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    REMEMBER_ME_DAYS = int(os.getenv("REMEMBER_ME_DAYS", "7"))

    # Analytics Configuration
    ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ANALYTICS_REFRESH_INTERVAL = int(os.getenv("ANALYTICS_REFRESH_INTERVAL", "300"))

    # Debug Configuration
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all configuration values"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith("_") and not callable(getattr(cls, attr))
        }

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        try:
            # Check required configurations
            assert cls.API_URL, "API_URL is required"
            assert cls.MAX_FILE_SIZE_MB > 0, "MAX_FILE_SIZE_MB must be positive"
            assert cls.DEFAULT_MAX_RESULTS > 0, "DEFAULT_MAX_RESULTS must be positive"
            assert cls.ALLOWED_FILE_TYPES, "ALLOWED_FILE_TYPES cannot be empty"
            return True
        except AssertionError as e:
            print(f"Configuration validation failed: {e}")
            return False


# Validate configuration on import
if not Config.validate():
    raise RuntimeError("Invalid configuration detected")
