import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List

import crud
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
)
from evaluation import (
    ABTestConfig,
    EvaluationRequest,
    EvaluationResult,
    PerformanceMetrics,
    ab_testing_service,
    evaluation_service,
    monitoring_service,
)
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from models import Base, Feedback, QueryLog, User
from schemas import (
    APIKeyCreate,
    APIKeyRead,
    APIKeyWithToken,
    DocumentRead,
    DocumentSummary,
    FeedbackCreate,
    FeedbackRead,
    FileUploadResponse,
    QueryLogRead,
    QueryRequest,
    QueryResponse,
    SystemHealth,
    SystemStats,
    Token,
    UserCreate,
    UserProfile,
    UserRead,
)
from services import service_registry

# Import all our modules
from sql_database import Base, create_tables, engine, get_database, get_db_info
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./enterprise_rag.db")

# Initialize database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create database tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on startup
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
                username="admin", email="admin@example.com", password="Admin123!"
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
    lifespan=lifespan,
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(","),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
    ).split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "timestamp": datetime.utcnow().isoformat()},
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": getattr(exc, "error_code", None),
            "timestamp": datetime.utcnow().isoformat(),
        },
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
        timestamp=datetime.utcnow(),
    )


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Enterprise Document Intelligence System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Authentication endpoints
@app.post(
    "/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_database)):
    """Register a new user"""
    # Check if user already exists
    if crud.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if user_data.email and crud.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = crud.create_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User registration failed"
        )

    logger.info(f"New user registered: {user.username}")
    return user


@app.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database),
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
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# User management endpoints
@app.get("/users/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
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
        avg_confidence_score=stats["avg_confidence_score"],
    )


@app.get("/users", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database),
):
    """List all users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


# Document management endpoints
@app.post(
    "/documents/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    db: Session = Depends(get_database),
):
    """Upload and process a document"""
    # Validate file type
    if not file.filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX, and TXT files are supported",
        )

    try:
        # Process document
        start_time = time.time()
        document_data = await service_registry.document_processor.process_document(
            file, chunk_size, chunk_overlap
        )

        # Save to database (using user_id = 1 for testing)
        document = crud.create_document(db, document_data, 1)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document metadata",
            )

        processing_time = time.time() - start_time
        logger.info(
            f"Document uploaded successfully: {file.filename} in {processing_time:.2f}s"
        )

        return FileUploadResponse(
            message=f"Document '{file.filename}' uploaded and processed successfully",
            document_id=document.id,
            processing_status="completed",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed",
        )


@app.get("/documents", response_model=List[DocumentSummary])
async def list_documents(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_database)
):
    """List all documents (testing without auth)"""
    documents = crud.get_documents_by_owner(db, 1, skip=skip, limit=limit)
    return [
        DocumentSummary(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            total_chunks=doc.total_chunks,
            processing_status=doc.processing_status,
            created_at=doc.created_at,
        )
        for doc in documents
    ]


@app.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """Get document details"""
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check ownership
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document",
        )

    return document


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """Delete a document"""
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check ownership
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document",
        )

    # Delete from vector database
    if document.chunk_ids:
        await service_registry.vector_db_service.delete_document_vectors(
            document.chunk_ids
        )

    # Delete from SQL database
    success = crud.delete_document(db, document_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )

    logger.info(f"Document deleted: {document_id} by user {current_user.id}")
    return {"message": "Document deleted successfully"}


# Query endpoints
@app.post("/query", response_model=QueryResponse)
async def process_query(
    query_request: QueryRequest, request: Request, db: Session = Depends(get_database)
):
    """Process a query against the document knowledge base"""
    start_time = time.time()

    try:
        # Process query
        result = await service_registry.rag_service.query_documents(query_request)
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time

        # Log the query (using user_id = 1 for testing)
        query_log = crud.create_query_log(
            db=db,
            user_id=1,
            query_text=query_request.query,
            response_text=result["answer"],
            confidence_score=result["confidence_score"],
            processing_time=processing_time,
            sources_count=result["sources_count"],
            status="completed",
            max_results=query_request.max_results,
            filter_params=query_request.filter_params,
        )

        return QueryResponse(
            id=query_log.id if query_log else 0,
            query=result["query"],
            answer=result["answer"],
            sources=result["sources"],
            confidence_score=result["confidence_score"],
            processing_time=processing_time,
            sources_count=result["sources_count"],
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Query processing failed: {e}")

        # Log the failed query (using user_id = 1 for testing)
        crud.create_query_log(
            db=db,
            user_id=1,
            query_text=query_request.query,
            processing_time=processing_time,
            status="failed",
            error_message=str(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query processing failed",
        )


@app.get("/queries", response_model=List[QueryLogRead])
async def list_queries(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """List user's query history"""
    queries = crud.get_query_logs_by_user(db, current_user.id, skip=skip, limit=limit)
    return queries


# Feedback endpoints
@app.post("/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """Submit feedback for a query response"""
    # Verify query log exists and belongs to user
    query_log = crud.get_query_log(db, feedback_data.query_log_id)
    if not query_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
        )

    if query_log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to provide feedback for this query",
        )

    feedback = crud.create_feedback(db, feedback_data, current_user.id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to submit feedback"
        )

    logger.info(
        f"Feedback submitted for query {feedback_data.query_log_id} by user {current_user.id}"
    )
    return feedback


# API Key management endpoints
@app.post(
    "/api-keys", response_model=APIKeyWithToken, status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """Create a new API key"""
    result = crud.create_api_key(db, api_key_data, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create API key"
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
        key=raw_key,
    )


@app.get("/api-keys", response_model=List[APIKeyRead])
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """List user's API keys"""
    api_keys = crud.get_api_keys_by_owner(db, current_user.id, skip=skip, limit=limit)
    return api_keys


@app.delete("/api-keys/{api_key_id}")
async def deactivate_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
):
    """Deactivate an API key"""
    success = crud.deactivate_api_key(db, api_key_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    logger.info(f"API key deactivated: {api_key_id} by user {current_user.id}")
    return {"message": "API key deactivated successfully"}


# Admin endpoints
@app.get("/admin/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database),
):
    """Get system-wide statistics (admin only)"""
    stats = crud.get_system_stats(db)

    return SystemStats(
        total_users=stats["total_users"],
        total_documents=stats["total_documents"],
        total_queries=stats["total_queries"],
        avg_processing_time=stats["avg_processing_time"],
        avg_confidence_score=stats["avg_confidence_score"],
        system_uptime=0.0,  # TODO: implement system uptime tracking
    )


# Evaluation & Monitoring Endpoints
@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate_response(
    request: EvaluationRequest, current_user: User = Depends(get_current_active_user)
):
    """Evaluate response quality using LLM-as-a-judge"""
    try:
        result = await evaluation_service.evaluate_response(request)
        logger.info(
            f"Response evaluated by user {current_user.id}: score={result.overall_score}"
        )
        return result
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation service temporarily unavailable",
        )


@app.post("/ab-tests", status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    config: ABTestConfig, current_user: User = Depends(get_current_admin_user)
):
    """Create a new A/B test (admin only)"""
    success = ab_testing_service.create_ab_test(config)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create A/B test"
        )

    logger.info(f"A/B test '{config.test_name}' created by admin {current_user.id}")
    return {"message": f"A/B test '{config.test_name}' created successfully"}


@app.get("/ab-tests/{test_name}/variant")
async def get_test_variant(
    test_name: str, current_user: User = Depends(get_current_active_user)
):
    """Get A/B test variant assignment for current user"""
    variant = ab_testing_service.assign_variant(test_name, current_user.id)
    return {"test_name": test_name, "variant": variant, "user_id": current_user.id}


@app.post("/ab-tests/{test_name}/results")
async def record_test_result(
    test_name: str,
    outcome_metric: float,
    current_user: User = Depends(get_current_active_user),
):
    """Record A/B test result for current user"""
    variant = ab_testing_service.assign_variant(test_name, current_user.id)
    ab_testing_service.record_result(
        test_name, variant, current_user.id, outcome_metric
    )
    return {"message": "Result recorded", "variant": variant}


@app.get("/ab-tests/{test_name}/analysis")
async def analyze_test_results(
    test_name: str, current_user: User = Depends(get_current_admin_user)
):
    """Analyze A/B test results (admin only)"""
    analysis = ab_testing_service.analyze_test_results(test_name)
    return analysis


@app.get("/metrics/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    days: int = 7,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database),
):
    """Get comprehensive performance metrics (admin only)"""
    metrics = monitoring_service.get_performance_metrics(db, days)
    return metrics


@app.get("/metrics/dashboard")
async def get_dashboard_data(
    days: int = 7,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database),
):
    """Get dashboard data for monitoring UI (admin only)"""
    try:
        # Get performance metrics
        performance = monitoring_service.get_performance_metrics(db, days)

        # Get query statistics
        recent_queries = (
            db.query(QueryLog)
            .filter(QueryLog.created_at >= datetime.utcnow() - timedelta(days=days))
            .all()
        )

        # Get feedback statistics
        feedback_data = (
            db.query(Feedback)
            .join(QueryLog)
            .filter(QueryLog.created_at >= datetime.utcnow() - timedelta(days=days))
            .all()
        )

        # Calculate additional metrics
        query_volume_by_day = {}
        error_count = 0

        for query in recent_queries:
            day = query.created_at.date().isoformat()
            query_volume_by_day[day] = query_volume_by_day.get(day, 0) + 1
            if query.status != "completed":
                error_count += 1

        feedback_distribution = {
            1: sum(1 for f in feedback_data if f.rating == 1),
            2: sum(1 for f in feedback_data if f.rating == 2),
            3: sum(1 for f in feedback_data if f.rating == 3),
            4: sum(1 for f in feedback_data if f.rating == 4),
            5: sum(1 for f in feedback_data if f.rating == 5),
        }

        return {
            "performance_metrics": performance.dict(),
            "query_volume_by_day": query_volume_by_day,
            "error_count": error_count,
            "feedback_distribution": feedback_distribution,
            "recent_queries_count": len(recent_queries),
            "recent_feedback_count": len(feedback_data),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
