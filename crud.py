from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from models import User, Document, QueryLog, Feedback, APIKey
from schemas import UserCreate, DocumentCreate, FeedbackCreate, APIKeyCreate
from auth import get_password_hash, hash_api_key, generate_api_key

logger = logging.getLogger(__name__)

# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    try:
        return db.query(User).filter(User.username == username).first()
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {e}")
        return None

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        return None

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination"""
    try:
        return db.query(User).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

def create_user(db: Session, user: UserCreate) -> Optional[User]:
    """Create a new user"""
    try:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created user: {user.username}")
        return db_user
    except Exception as e:
        logger.error(f"Error creating user {user.username}: {e}")
        db.rollback()
        return None

def update_user(db: Session, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
    """Update user"""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        for field, value in user_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        db.rollback()
        return None

def delete_user(db: Session, user_id: int) -> bool:
    """Delete user"""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        logger.info(f"Deleted user: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        db.rollback()
        return False

# Document CRUD operations
def get_document(db: Session, document_id: int) -> Optional[Document]:
    """Get document by ID"""
    try:
        return db.query(Document).filter(Document.id == document_id).first()
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        return None

def get_documents(db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
    """Get all documents with pagination"""
    try:
        return db.query(Document).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return []

def get_documents_by_owner(
    db: Session, 
    owner_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Document]:
    """Get documents by owner with pagination"""
    try:
        return (
            db.query(Document)
            .filter(Document.owner_id == owner_id)
            .order_by(desc(Document.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting documents for owner {owner_id}: {e}")
        return []

def create_document(db: Session, document: DocumentCreate, owner_id: int) -> Optional[Document]:
    """Create a new document"""
    try:
        db_document = Document(
            filename=document.filename,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
            total_chunks=document.total_chunks,
            chunk_size=document.chunk_size,
            chunk_overlap=document.chunk_overlap,
            chunk_ids=document.chunk_ids,
            doc_metadata=document.doc_metadata,
            owner_id=owner_id,
            processing_status="completed",
            processed_at=datetime.utcnow()
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        logger.info(f"Created document: {document.filename} for user {owner_id}")
        return db_document
    except Exception as e:
        logger.error(f"Error creating document {document.filename}: {e}")
        db.rollback()
        return None

def update_document_status(
    db: Session, 
    document_id: int, 
    status: str, 
    error_message: Optional[str] = None
) -> Optional[Document]:
    """Update document processing status"""
    try:
        db_document = db.query(Document).filter(Document.id == document_id).first()
        if not db_document:
            return None
        
        db_document.processing_status = status
        if error_message:
            db_document.error_message = error_message
        if status == "completed":
            db_document.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_document)
        return db_document
    except Exception as e:
        logger.error(f"Error updating document status {document_id}: {e}")
        db.rollback()
        return None

def delete_document(db: Session, document_id: int, owner_id: int) -> bool:
    """Delete document (only by owner)"""
    try:
        db_document = db.query(Document).filter(
            and_(Document.id == document_id, Document.owner_id == owner_id)
        ).first()
        if not db_document:
            return False
        
        db.delete(db_document)
        db.commit()
        logger.info(f"Deleted document: {document_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        db.rollback()
        return False

# Query Log CRUD operations
def create_query_log(
    db: Session,
    user_id: int,
    query_text: str,
    response_text: Optional[str] = None,
    confidence_score: Optional[float] = None,
    processing_time: Optional[float] = None,
    sources_count: int = 0,
    status: str = "completed",
    error_message: Optional[str] = None,
    max_results: int = 5,
    filter_params: Optional[Dict[str, Any]] = None
) -> Optional[QueryLog]:
    """Create a new query log entry"""
    try:
        db_query_log = QueryLog(
            user_id=user_id,
            query_text=query_text,
            response_text=response_text,
            confidence_score=confidence_score,
            processing_time=processing_time,
            sources_count=sources_count,
            status=status,
            error_message=error_message,
            max_results=max_results,
            filter_params=filter_params
        )
        db.add(db_query_log)
        db.commit()
        db.refresh(db_query_log)
        return db_query_log
    except Exception as e:
        logger.error(f"Error creating query log: {e}")
        db.rollback()
        return None

def get_query_logs_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[QueryLog]:
    """Get query logs by user"""
    try:
        return (
            db.query(QueryLog)
            .filter(QueryLog.user_id == user_id)
            .order_by(desc(QueryLog.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting query logs for user {user_id}: {e}")
        return []

def get_query_log(db: Session, query_log_id: int) -> Optional[QueryLog]:
    """Get query log by ID"""
    try:
        return db.query(QueryLog).filter(QueryLog.id == query_log_id).first()
    except Exception as e:
        logger.error(f"Error getting query log {query_log_id}: {e}")
        return None

# Feedback CRUD operations
def create_feedback(
    db: Session, 
    feedback: FeedbackCreate, 
    user_id: int
) -> Optional[Feedback]:
    """Create feedback"""
    try:
        db_feedback = Feedback(
            rating=feedback.rating,
            comment=feedback.comment,
            feedback_type=feedback.feedback_type,
            was_helpful=feedback.was_helpful,
            suggested_improvement=feedback.suggested_improvement,
            user_id=user_id,
            query_log_id=feedback.query_log_id
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        logger.info(f"Created feedback for query {feedback.query_log_id}")
        return db_feedback
    except Exception as e:
        logger.error(f"Error creating feedback: {e}")
        db.rollback()
        return None

def get_feedback_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Feedback]:
    """Get feedback by user"""
    try:
        return (
            db.query(Feedback)
            .filter(Feedback.user_id == user_id)
            .order_by(desc(Feedback.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting feedback for user {user_id}: {e}")
        return []

# API Key CRUD operations
def create_api_key(
    db: Session,
    api_key_data: APIKeyCreate,
    owner_id: int
) -> Optional[tuple[APIKey, str]]:
    """Create API key and return both the object and the raw key"""
    try:
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        
        expires_at = None
        if api_key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
        
        db_api_key = APIKey(
            key_hash=key_hash,
            name=api_key_data.name,
            description=api_key_data.description,
            rate_limit=api_key_data.rate_limit,
            can_upload=api_key_data.can_upload,
            can_query=api_key_data.can_query,
            can_admin=api_key_data.can_admin,
            owner_id=owner_id,
            expires_at=expires_at
        )
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        logger.info(f"Created API key: {api_key_data.name} for user {owner_id}")
        return db_api_key, raw_key
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        db.rollback()
        return None

def get_api_key_by_hash(db: Session, key_hash: str) -> Optional[APIKey]:
    """Get API key by hash"""
    try:
        return db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    except Exception as e:
        logger.error(f"Error getting API key by hash: {e}")
        return None

def get_api_keys_by_owner(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[APIKey]:
    """Get API keys by owner"""
    try:
        return (
            db.query(APIKey)
            .filter(APIKey.owner_id == owner_id)
            .order_by(desc(APIKey.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting API keys for owner {owner_id}: {e}")
        return []

def update_api_key_usage(db: Session, api_key_id: int) -> bool:
    """Update API key usage"""
    try:
        db_api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not db_api_key:
            return False
        
        db_api_key.last_used = datetime.utcnow()
        db_api_key.total_requests += 1
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating API key usage {api_key_id}: {e}")
        db.rollback()
        return False

def deactivate_api_key(db: Session, api_key_id: int, owner_id: int) -> bool:
    """Deactivate API key (only by owner)"""
    try:
        db_api_key = db.query(APIKey).filter(
            and_(APIKey.id == api_key_id, APIKey.owner_id == owner_id)
        ).first()
        if not db_api_key:
            return False
        
        db_api_key.is_active = False
        db.commit()
        logger.info(f"Deactivated API key: {api_key_id}")
        return True
    except Exception as e:
        logger.error(f"Error deactivating API key {api_key_id}: {e}")
        db.rollback()
        return False

# Statistics and analytics
def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get user statistics"""
    try:
        total_documents = db.query(func.count(Document.id)).filter(
            Document.owner_id == user_id
        ).scalar() or 0
        
        total_queries = db.query(func.count(QueryLog.id)).filter(
            QueryLog.user_id == user_id
        ).scalar() or 0
        
        avg_confidence = db.query(func.avg(QueryLog.confidence_score)).filter(
            and_(
                QueryLog.user_id == user_id,
                QueryLog.confidence_score.isnot(None)
            )
        ).scalar()
        
        return {
            "total_documents": total_documents,
            "total_queries": total_queries,
            "avg_confidence_score": float(avg_confidence) if avg_confidence else None
        }
    except Exception as e:
        logger.error(f"Error getting user stats {user_id}: {e}")
        return {
            "total_documents": 0,
            "total_queries": 0,
            "avg_confidence_score": None
        }

def get_system_stats(db: Session) -> Dict[str, Any]:
    """Get system-wide statistics"""
    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_documents = db.query(func.count(Document.id)).scalar() or 0
        total_queries = db.query(func.count(QueryLog.id)).scalar() or 0
        
        avg_processing_time = db.query(func.avg(QueryLog.processing_time)).filter(
            QueryLog.processing_time.isnot(None)
        ).scalar()
        
        avg_confidence = db.query(func.avg(QueryLog.confidence_score)).filter(
            QueryLog.confidence_score.isnot(None)
        ).scalar()
        
        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_queries": total_queries,
            "avg_processing_time": float(avg_processing_time) if avg_processing_time else None,
            "avg_confidence_score": float(avg_confidence) if avg_confidence else None
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "total_users": 0,
            "total_documents": 0,
            "total_queries": 0,
            "avg_processing_time": None,
            "avg_confidence_score": None
        } 