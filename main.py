from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import asyncio
import time
import os

# Import all our modules
from sql_database import get_database, create_tables, get_db_info, Base, engine
from models import User, Document, QueryLog, Feedback, APIKey
from schemas import (
    UserCreate, UserRead, UserProfile, Token, DocumentRead, DocumentSummary,
    QueryRequest, QueryResponse, QueryLogRead, FeedbackCreate, FeedbackRead,
    APIKeyCreate, APIKeyRead, APIKeyWithToken, SystemHealth, SystemStats,
    ErrorResponse, ValidationErrorResponse, FileUploadResponse
)
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_current_admin_user, require_upload_permission, require_query_permission,
    require_admin_permission, ACCESS_TOKEN_EXPIRE_MINUTES
)
from services import service_registry
import crud

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
create_tables()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Enterprise Document Intelligence System starting up...")
    logger.info("Database tables created successfully")
    
    # Create default admin user if it doesn't exist
    db = next(get_database())
    try:
        admin_user = crud.get_user_by_username(db, "admin")
        if not admin_user:
            admin_data = UserCreate(
                username="admin",
                email="admin@example.com",
                password="Admin123!"
            )
            admin_user = crud.create_user(db, admin_data)
            if admin_user:
                crud.update_user(db, admin_user.id, {"is_admin": True})
                logger.info("Default admin user created: admin/Admin123!")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Enterprise Document Intelligence System shutting down...")

# FastAPI app initialization
app = FastAPI(
    title="Enterprise Document Intelligence System",
    description="A comprehensive RAG-based document intelligence system with authentication, document management, and query capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": getattr(exc, 'error_code', None),
            "timestamp": datetime.utcnow().isoformat()
        }
    )



# Health check endpoints
@app.get("/health", response_model=SystemHealth)
async def health_check():
    """Comprehensive system health check"""
    health_data = await service_registry.health_check()
    
    return SystemHealth(
        status=health_data["status"],
        database=get_db_info(),
        vector_database=health_data.get("vector_database", {}),
        openai="configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
        timestamp=datetime.utcnow()
    )

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Enterprise Document Intelligence System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication endpoints
@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_database)):
    """Register a new user"""
    # Check if user already exists
    if crud.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if user_data.email and crud.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = crud.create_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed"
        )
    
    logger.info(f"New user registered: {user.username}")
    return user

@app.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database)
):
    """Authenticate user and return access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.username}")
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

# User management endpoints
@app.get("/users/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Get current user profile with statistics"""
    stats = crud.get_user_stats(db, current_user.id)
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        total_documents=stats["total_documents"],
        total_queries=stats["total_queries"],
        avg_confidence_score=stats["avg_confidence_score"]
    )

@app.get("/users", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database)
):
    """List all users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Document management endpoints
@app.post("/documents/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    auth_data: dict = Depends(require_upload_permission),
    db: Session = Depends(get_database)
):
    """Upload and process a document"""
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX, and TXT files are supported"
        )
    
    try:
        # Process document
        start_time = time.time()
        document_data = await service_registry.document_processor.process_document(
            file, chunk_size, chunk_overlap
        )
        
        # Save to database
        document = crud.create_document(db, document_data, auth_data["user"].id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document metadata"
            )
        
        processing_time = time.time() - start_time
        logger.info(f"Document uploaded successfully: {file.filename} in {processing_time:.2f}s")
        
        return FileUploadResponse(
            message=f"Document '{file.filename}' uploaded and processed successfully",
            document_id=document.id,
            processing_status="completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed"
        )

@app.get("/documents", response_model=List[DocumentSummary])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """List user's documents"""
    documents = crud.get_documents_by_owner(db, current_user.id, skip=skip, limit=limit)
    return [
        DocumentSummary(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            total_chunks=doc.total_chunks,
            processing_status=doc.processing_status,
            created_at=doc.created_at
        )
        for doc in documents
    ]

@app.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Get document details"""
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    return document

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Delete a document"""
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )
    
    # Delete from vector database
    if document.chunk_ids:
        await service_registry.vector_db_service.delete_document_vectors(document.chunk_ids)
    
    # Delete from SQL database
    success = crud.delete_document(db, document_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
    
    logger.info(f"Document deleted: {document_id} by user {current_user.id}")
    return {"message": "Document deleted successfully"}

# Query endpoints
@app.post("/query", response_model=QueryResponse)
async def process_query(
    query_request: QueryRequest,
    request: Request,
    auth_data: dict = Depends(require_query_permission),
    db: Session = Depends(get_database)
):
    """Process a query against the document knowledge base"""
    start_time = time.time()
    
    try:
        # Process query
        result = await service_registry.rag_service.query_documents(query_request)
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        
        # Log the query
        query_log = crud.create_query_log(
            db=db,
            user_id=auth_data["user"].id,
            query_text=query_request.query,
            response_text=result["answer"],
            confidence_score=result["confidence_score"],
            processing_time=processing_time,
            sources_count=result["sources_count"],
            status="completed",
            max_results=query_request.max_results,
            filter_params=query_request.filter_params
        )
        
        return QueryResponse(
            id=query_log.id if query_log else 0,
            query=result["query"],
            answer=result["answer"],
            sources=result["sources"],
            confidence_score=result["confidence_score"],
            processing_time=processing_time,
            sources_count=result["sources_count"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Query processing failed: {e}")
        
        # Log the failed query
        crud.create_query_log(
            db=db,
            user_id=auth_data["user"].id,
            query_text=query_request.query,
            processing_time=processing_time,
            status="failed",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query processing failed"
        )

@app.get("/queries", response_model=List[QueryLogRead])
async def list_queries(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """List user's query history"""
    queries = crud.get_query_logs_by_user(db, current_user.id, skip=skip, limit=limit)
    return queries

# Feedback endpoints
@app.post("/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Submit feedback for a query response"""
    # Verify query log exists and belongs to user
    query_log = crud.get_query_log(db, feedback_data.query_log_id)
    if not query_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    if query_log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to provide feedback for this query"
        )
    
    feedback = crud.create_feedback(db, feedback_data, current_user.id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to submit feedback"
        )
    
    logger.info(f"Feedback submitted for query {feedback_data.query_log_id} by user {current_user.id}")
    return feedback

# API Key management endpoints
@app.post("/api-keys", response_model=APIKeyWithToken, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Create a new API key"""
    result = crud.create_api_key(db, api_key_data, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key"
        )
    
    api_key_obj, raw_key = result
    
    return APIKeyWithToken(
        id=api_key_obj.id,
        name=api_key_obj.name,
        description=api_key_obj.description,
        rate_limit=api_key_obj.rate_limit,
        can_upload=api_key_obj.can_upload,
        can_query=api_key_obj.can_query,
        can_admin=api_key_obj.can_admin,
        is_active=api_key_obj.is_active,
        last_used=api_key_obj.last_used,
        total_requests=api_key_obj.total_requests,
        created_at=api_key_obj.created_at,
        expires_at=api_key_obj.expires_at,
        key=raw_key
    )

@app.get("/api-keys", response_model=List[APIKeyRead])
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """List user's API keys"""
    api_keys = crud.get_api_keys_by_owner(db, current_user.id, skip=skip, limit=limit)
    return api_keys

@app.delete("/api-keys/{api_key_id}")
async def deactivate_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Deactivate an API key"""
    success = crud.deactivate_api_key(db, api_key_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    logger.info(f"API key deactivated: {api_key_id} by user {current_user.id}")
    return {"message": "API key deactivated successfully"}

# Admin endpoints
@app.get("/admin/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database)
):
    """Get system-wide statistics (admin only)"""
    stats = crud.get_system_stats(db)
    
    return SystemStats(
        total_users=stats["total_users"],
        total_documents=stats["total_documents"],
        total_queries=stats["total_queries"],
        avg_processing_time=stats["avg_processing_time"],
        avg_confidence_score=stats["avg_confidence_score"],
        system_uptime=0.0  # TODO: implement system uptime tracking
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 