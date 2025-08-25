import logging
from datetime import datetime
from typing import Any, Dict, List

import document_processor as doc_proc
import httpx
from fastapi import HTTPException, UploadFile
from rag import rag_system
from schemas import DocumentCreate, QueryRequest

logger = logging.getLogger(__name__)

# Configuration for internal service communication
DOCUMENT_PROCESSOR_URL = "http://localhost:8002"
RAG_SYSTEM_URL = "http://localhost:8001"


class DocumentProcessorService:
    """Service for processing documents using the local document processor"""

    async def process_document(
        self, file: UploadFile, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> DocumentCreate:
        """Process document using the local document processor"""
        try:
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file position

            # Process based on file type
            if file.filename.lower().endswith(".pdf"):
                text = doc_proc.process_pdf(file_content)
            elif file.filename.lower().endswith(".docx"):
                text = doc_proc.process_docx(file_content)
            elif file.filename.lower().endswith(".txt"):
                text = doc_proc.process_txt(file_content)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}. Supported types: PDF, DOCX, TXT",
                )

            # Clean and chunk text
            config = doc_proc.ChunkConfig(size=chunk_size, overlap=chunk_overlap)
            cleaned_text = doc_proc.clean_text(text)
            chunks = doc_proc.create_chunks(cleaned_text, config)

            # Process chunks and store in vector database
            metadata = {
                "source": file.filename,
                "file_type": file.filename.split(".")[-1].lower(),
            }
            chunk_ids = await doc_proc.process_chunks(chunks, metadata)

            # Transform the response to match our DocumentCreate schema
            return DocumentCreate(
                filename=file.filename,
                original_filename=file.filename,
                file_type=file.filename.split(".")[-1].lower(),
                file_size=len(file_content),
                total_chunks=len(chunks),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunk_ids=chunk_ids,
                doc_metadata={
                    "original_text_length": len(text),
                    "cleaned_text_length": len(cleaned_text),
                    "processing_timestamp": datetime.utcnow().isoformat(),
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Document processing failed: {str(e)}"
            )


class RAGService:
    """Service for communicating with the RAG system"""

    @staticmethod
    async def query_documents(query_request: QueryRequest) -> Dict[str, Any]:
        """Query documents using the RAG system"""
        try:
            # Use the existing RAG system directly
            context_chunks = await rag_system.retrieve_context(
                query_request.query, query_request.filter_params
            )

            if not context_chunks:
                return {
                    "query": query_request.query,
                    "answer": "I don't have enough information in the knowledge base to answer this question.",
                    "sources": [],
                    "confidence_score": 0.0,
                    "processing_time": 0.0,
                    "sources_count": 0,
                }

            # Generate answer using the RAG system
            answer, confidence_score = await rag_system.generate_answer(
                query_request.query, context_chunks[: query_request.max_results]
            )

            # Prepare sources
            sources = [
                {
                    "id": chunk.source_id,
                    "content_preview": chunk.content[:200] + "..."
                    if len(chunk.content) > 200
                    else chunk.content,
                    "metadata": chunk.metadata,
                    "relevance_score": chunk.relevance_score,
                }
                for chunk in context_chunks[: query_request.max_results]
            ]

            return {
                "query": query_request.query,
                "answer": answer,
                "sources": sources,
                "confidence_score": confidence_score,
                "processing_time": 0.0,  # Will be calculated at endpoint level
                "sources_count": len(sources),
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise HTTPException(status_code=500, detail="Query processing failed")

    @staticmethod
    async def query_via_http(query_request: QueryRequest) -> Dict[str, Any]:
        """Alternative: Query using HTTP API (if needed for external RAG service)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{RAG_SYSTEM_URL}/query", json=query_request.dict()
                )

                if response.status_code != 200:
                    logger.error(f"RAG query failed: {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Query processing failed: {response.text}",
                    )

                return response.json()

        except httpx.TimeoutException:
            logger.error("RAG query timeout")
            raise HTTPException(status_code=408, detail="Query processing timeout")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during RAG query: {e}")
            raise HTTPException(
                status_code=500, detail="Query processing service unavailable"
            )


class HealthCheckService:
    """Service for health checks and system monitoring"""

    @staticmethod
    async def check_services() -> Dict[str, Any]:
        """Check health of all services"""
        services_status = {}

        # Check document processor
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{DOCUMENT_PROCESSOR_URL}/")
                services_status["document_processor"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                }
        except Exception as e:
            services_status["document_processor"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Check RAG system
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{RAG_SYSTEM_URL}/health")
                services_status["rag_system"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if response.status_code == 200 else None,
                }
        except Exception as e:
            services_status["rag_system"] = {"status": "unhealthy", "error": str(e)}

        return services_status


class VectorDatabaseService:
    """Service for vector database operations"""

    @staticmethod
    async def get_database_info() -> Dict[str, Any]:
        """Get vector database information"""
        try:
            from vector_database import ChromaDB

            db = ChromaDB()
            count = db.count()

            return {"type": "ChromaDB", "document_count": count, "status": "healthy"}
        except Exception as e:
            logger.error(f"Error getting vector database info: {e}")
            return {
                "type": "ChromaDB",
                "document_count": 0,
                "status": "unhealthy",
                "error": str(e),
            }

    @staticmethod
    async def delete_document_vectors(chunk_ids: List[str]) -> bool:
        """Delete document vectors from the vector database"""
        try:
            from vector_database import ChromaDB

            db = ChromaDB()
            await db.delete(chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks from vector database")
            return True
        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            return False


# Service registry for dependency injection
class ServiceRegistry:
    """Central registry for all services"""

    def __init__(self):
        self.document_processor = DocumentProcessorService()
        self.rag_service = RAGService()
        self.health_service = HealthCheckService()
        self.vector_db_service = VectorDatabaseService()

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            services = await self.health_service.check_services()
            vector_db = await self.vector_db_service.get_database_info()

            overall_status = "healthy"
            if any(service.get("status") != "healthy" for service in services.values()):
                overall_status = "degraded"
            if vector_db.get("status") != "healthy":
                overall_status = "degraded"

            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": services,
                "vector_database": vector_db,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# Global service registry instance
service_registry = ServiceRegistry()
