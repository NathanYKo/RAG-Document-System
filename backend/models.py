from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sql_database import Base
import uuid

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Document(Base):
    """Document model for storing document metadata and processing results"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    total_chunks = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    chunk_overlap = Column(Integer, nullable=False)
    processing_status = Column(String(20), default="processing", index=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata storage
    doc_metadata = Column(JSON, nullable=True)
    chunk_ids = Column(JSON, nullable=False)  # Store vector DB chunk IDs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    owner = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.processing_status}')>"

class QueryLog(Base):
    """Log all queries for analytics and monitoring"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    sources_count = Column(Integer, default=0)
    
    # Query parameters
    max_results = Column(Integer, default=5)
    filter_params = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="completed", index=True)  # completed, failed, timeout
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="queries")
    feedback = relationship("Feedback", back_populates="query_log", uselist=False)

    def __repr__(self):
        return f"<QueryLog(id={self.id}, status='{self.status}', confidence={self.confidence_score})>"

class Feedback(Base):
    """User feedback on query responses for system improvement"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    comment = Column(Text, nullable=True)
    feedback_type = Column(String(20), default="general", index=True)  # general, accuracy, relevance, speed
    
    # Additional feedback data
    was_helpful = Column(Boolean, nullable=True)
    suggested_improvement = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query_log_id = Column(Integer, ForeignKey("query_logs.id"), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="feedback")
    query_log = relationship("QueryLog", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating}, type='{self.feedback_type}')>"

class APIKey(Base):
    """API keys for external access"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=1000)  # requests per hour
    
    # Permissions
    can_upload = Column(Boolean, default=False)
    can_query = Column(Boolean, default=True)
    can_admin = Column(Boolean, default=False)
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True), nullable=True)
    total_requests = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    owner = relationship("User")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', active={self.is_active})>" 