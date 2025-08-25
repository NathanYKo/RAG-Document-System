from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Enums for consistent values
class ProcessingStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FeedbackType(str, Enum):
    GENERAL = "general"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    SPEED = "speed"


class QueryStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserRead):
    total_documents: int = 0
    total_queries: int = 0
    avg_confidence_score: Optional[float] = None


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


# Document schemas
class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., pattern="^(pdf|docx|txt)$")


class DocumentCreate(DocumentBase):
    original_filename: str
    file_size: int = Field(..., gt=0)
    total_chunks: int = Field(..., ge=0)
    chunk_size: int = Field(..., gt=0)
    chunk_overlap: int = Field(..., ge=0)
    chunk_ids: List[str]
    doc_metadata: Optional[Dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    processing_status: Optional[ProcessingStatus] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


class DocumentRead(DocumentBase):
    id: int
    total_chunks: int
    chunk_size: int
    chunk_overlap: int
    processing_status: ProcessingStatus
    error_message: Optional[str]
    doc_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    processed_at: Optional[datetime]
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class DocumentSummary(BaseModel):
    id: int
    filename: str
    file_type: str
    total_chunks: int
    processing_status: ProcessingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Query schemas
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=20)
    include_metadata: bool = Field(default=True)
    filter_params: Optional[Dict[str, Any]] = Field(default=None)


class QueryResponse(BaseModel):
    id: int
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    sources_count: int
    timestamp: datetime


# Query log schemas
class QueryLogRead(BaseModel):
    id: int
    query_text: str
    response_text: Optional[str]
    confidence_score: Optional[float]
    processing_time: Optional[float]
    sources_count: int
    status: QueryStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Feedback schemas
class FeedbackBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    feedback_type: FeedbackType = FeedbackType.GENERAL
    was_helpful: Optional[bool] = None
    suggested_improvement: Optional[str] = Field(None, max_length=500)


class FeedbackCreate(FeedbackBase):
    query_log_id: int


class FeedbackRead(FeedbackBase):
    id: int
    created_at: datetime
    user_id: int
    query_log_id: int

    model_config = ConfigDict(from_attributes=True)


# API Key schemas
class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate_limit: int = Field(default=1000, ge=1, le=10000)
    can_upload: bool = Field(default=False)
    can_query: bool = Field(default=True)
    can_admin: bool = Field(default=False)


class APIKeyCreate(APIKeyBase):
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyRead(APIKeyBase):
    id: int
    is_active: bool
    last_used: Optional[datetime]
    total_requests: int
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class APIKeyWithToken(APIKeyRead):
    key: str  # Only returned once when created


# System schemas
class SystemHealth(BaseModel):
    status: str
    database: Dict[str, Any]
    vector_database: Dict[str, Any]
    openai: str
    timestamp: datetime


class SystemStats(BaseModel):
    total_users: int
    total_documents: int
    total_queries: int
    avg_processing_time: Optional[float]
    avg_confidence_score: Optional[float]
    system_uptime: float


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime


class ValidationErrorResponse(BaseModel):
    detail: List[Dict[str, Any]]
    error_code: str = "validation_error"
    timestamp: datetime


# File upload schemas
class FileUploadResponse(BaseModel):
    message: str
    document_id: int
    processing_status: ProcessingStatus
    estimated_completion: Optional[datetime] = None
