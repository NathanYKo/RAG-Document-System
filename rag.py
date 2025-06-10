import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from openai import OpenAI

from vector_database import ChromaDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with error handling
def get_openai_client():
    """Get OpenAI client with proper error handling"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OpenAI API key not set. Some functionality will be limited.")
        return None
    return OpenAI(api_key=api_key)

client = get_openai_client()

# Configuration
@dataclass
class RAGConfig:
    """Configuration for RAG system parameters"""
    max_context_length: int = 4000
    top_k_retrieval: int = 10
    final_context_chunks: int = 5
    min_relevance_score: float = 0.1
    max_tokens: int = 1000
    temperature: float = 0.3
    model: str = "gpt-4"

config = RAGConfig()

# Advanced prompt templates
SYSTEM_PROMPT = """You are an expert AI assistant that provides accurate, well-reasoned answers based on the provided context.

Guidelines:
1. Answer based ONLY on the provided context
2. If information is insufficient, clearly state this limitation
3. Cite specific sources when making claims
4. Provide structured, clear responses
5. Acknowledge uncertainty when appropriate
6. Distinguish between facts and inferences"""

QUERY_PROMPT_TEMPLATE = """Context Information:
{context}

Question: {question}

Instructions:
- Provide a comprehensive answer based on the context above
- Include specific citations using [Source: document_id] format
- If the context doesn't contain sufficient information, state this clearly
- Structure your response logically with clear reasoning

Answer:"""

EVALUATION_PROMPT = """Evaluate the relevance of this document chunk to the query:
Query: {query}
Chunk: {chunk}

Rate relevance from 0.0 to 1.0 and provide a brief justification.
Response format: {{\"score\": 0.0-1.0, \"reason\": \"brief explanation\"}}"""

# Data models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=20)
    include_metadata: bool = Field(default=True)
    filter_params: Optional[Dict[str, Any]] = Field(default=None)

class ContextChunk(BaseModel):
    content: str
    source_id: str
    metadata: Dict[str, Any]
    relevance_score: float
    retrieval_method: str

class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    context_used: List[ContextChunk]
    confidence_score: float
    processing_time: float
    timestamp: datetime

# FastAPI app
app = FastAPI(
    title="Enhanced RAG System",
    description="Advanced Retrieval-Augmented Generation with intelligent context ranking",
    version="2.0.0"
)

class EnhancedRAGSystem:
    """Enhanced RAG system with improved retrieval and ranking"""
    
    def __init__(self):
        self.db = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database connection with error handling"""
        try:
            self.db = ChromaDB()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise HTTPException(status_code=500, detail="Database initialization failed")
    
    async def retrieve_context(
        self, 
        query: str, 
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[ContextChunk]:
        """Enhanced context retrieval with multiple strategies"""
        try:
            # Primary semantic retrieval
            semantic_results = self.db.query(
                query_texts=[query], 
                n_results=config.top_k_retrieval
            )
            
            context_chunks = []
            
            if semantic_results and semantic_results.get('documents'):
                documents = semantic_results['documents'][0]
                ids = semantic_results['ids'][0]
                metadatas = semantic_results.get('metadatas', [{}] * len(documents))[0]
                distances = semantic_results.get('distances', [0.5] * len(documents))[0]
                
                for doc, doc_id, metadata, distance in zip(documents, ids, metadatas, distances):
                    # Convert distance to relevance score (lower distance = higher relevance)
                    relevance_score = max(0.0, 1.0 - distance)
                    
                    # Apply minimum relevance filter
                    if relevance_score >= config.min_relevance_score:
                        chunk = ContextChunk(
                            content=doc,
                            source_id=doc_id,
                            metadata=metadata or {},
                            relevance_score=relevance_score,
                            retrieval_method="semantic"
                        )
                        context_chunks.append(chunk)
            
            # Enhanced filtering and ranking
            filtered_chunks = await self._apply_advanced_filtering(
                context_chunks, query, filter_params
            )
            
            # Re-rank using LLM-based evaluation
            reranked_chunks = await self._llm_rerank_contexts(query, filtered_chunks)
            
            # Select top chunks within context window
            final_chunks = self._select_optimal_context(reranked_chunks)
            
            logger.info(f"Retrieved {len(final_chunks)} relevant context chunks")
            return final_chunks
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            raise HTTPException(status_code=500, detail="Context retrieval failed")
    
    async def _apply_advanced_filtering(
        self, 
        chunks: List[ContextChunk], 
        query: str,
        filter_params: Optional[Dict[str, Any]]
    ) -> List[ContextChunk]:
        """Apply advanced filtering strategies"""
        
        filtered_chunks = chunks.copy()
        
        # Content quality filtering
        filtered_chunks = [
            chunk for chunk in filtered_chunks
            if len(chunk.content.strip()) > 50 and  # Minimum content length
            not chunk.content.lower().startswith(('error', 'warning', 'debug'))  # Filter system messages
        ]
        
        # Apply user-specified filters
        if filter_params:
            if 'file_type' in filter_params:
                filtered_chunks = [
                    chunk for chunk in filtered_chunks
                    if chunk.metadata.get('file_type') == filter_params['file_type']
                ]
            
            if 'min_score' in filter_params:
                min_score = float(filter_params['min_score'])
                filtered_chunks = [
                    chunk for chunk in filtered_chunks
                    if chunk.relevance_score >= min_score
                ]
        
        # Diversity filtering (avoid too similar chunks)
        diverse_chunks = self._ensure_diversity(filtered_chunks)
        
        return diverse_chunks
    
    def _ensure_diversity(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Ensure diversity in selected chunks to avoid redundancy"""
        if len(chunks) <= 1:
            return chunks
        
        diverse_chunks = [chunks[0]]  # Always include the most relevant
        
        for chunk in chunks[1:]:
            # Simple diversity check based on content overlap
            should_include = True
            for existing_chunk in diverse_chunks:
                # Calculate rough similarity based on common words
                chunk_words = set(chunk.content.lower().split())
                existing_words = set(existing_chunk.content.lower().split())
                
                if len(chunk_words) > 0 and len(existing_words) > 0:
                    overlap = len(chunk_words & existing_words) / len(chunk_words | existing_words)
                    if overlap > 0.7:  # Too similar
                        should_include = False
                        break
            
            if should_include:
                diverse_chunks.append(chunk)
        
        return diverse_chunks
    
    async def _llm_rerank_contexts(
        self, 
        query: str, 
        chunks: List[ContextChunk]
    ) -> List[ContextChunk]:
        """Use LLM to re-rank context chunks for better relevance"""
        
        if not chunks:
            return chunks
        
        # For efficiency, only re-rank if we have more chunks than needed
        if len(chunks) <= config.final_context_chunks:
            return sorted(chunks, key=lambda x: x.relevance_score, reverse=True)
        
        try:
            # Re-rank top candidates using LLM evaluation
            rerank_candidates = chunks[:min(8, len(chunks))]  # Limit LLM calls
            
            for chunk in rerank_candidates:
                evaluation_prompt = EVALUATION_PROMPT.format(
                    query=query, 
                    chunk=chunk.content[:500]  # Limit chunk size for evaluation
                )
                
                try:
                    if client is None:
                        # Skip LLM re-ranking if client not available
                        continue
                        
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",  # Use faster model for evaluation
                        messages=[
                            {"role": "system", "content": "You are a relevance evaluation expert."},
                            {"role": "user", "content": evaluation_prompt}
                        ],
                        max_tokens=100,
                        temperature=0.1
                    )
                    
                    # Parse LLM evaluation (simple approach)
                    eval_text = response.choices[0].message.content.lower()
                    if "score" in eval_text:
                        # Extract score (basic parsing - in production use JSON parsing)
                        import re
                        score_match = re.search(r'[\d.]+', eval_text)
                        if score_match:
                            llm_score = float(score_match.group())
                            # Combine with original score
                            chunk.relevance_score = (chunk.relevance_score + llm_score) / 2
                            
                except Exception as e:
                    logger.warning(f"LLM re-ranking failed for chunk: {e}")
                    # Continue with original score
            
            # Return all chunks sorted by updated scores
            return sorted(chunks, key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            logger.warning(f"LLM re-ranking failed: {e}")
            return sorted(chunks, key=lambda x: x.relevance_score, reverse=True)
    
    def _select_optimal_context(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Select optimal context chunks within token limits"""
        
        selected_chunks = []
        total_length = 0
        
        for chunk in chunks:
            # Rough token estimation (1 token ≈ 4 characters)
            chunk_tokens = len(chunk.content) // 4
            
            if total_length + chunk_tokens <= config.max_context_length:
                selected_chunks.append(chunk)
                total_length += chunk_tokens
                
                if len(selected_chunks) >= config.final_context_chunks:
                    break
            else:
                # Try to fit a truncated version
                remaining_tokens = config.max_context_length - total_length
                if remaining_tokens > 100:  # Worth including a truncated version
                    truncated_content = chunk.content[:remaining_tokens * 4]
                    chunk.content = truncated_content + "..."
                    selected_chunks.append(chunk)
                break
        
        return selected_chunks
    
    def _construct_context_string(self, chunks: List[ContextChunk]) -> str:
        """Construct formatted context string from chunks"""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"Source {i} (ID: {chunk.source_id})"
            if chunk.metadata.get('source'):
                source_info += f" - {chunk.metadata['source']}"
            
            context_parts.append(f"{source_info}:\n{chunk.content}\n")
        
        return "\n" + "="*50 + "\n".join(context_parts)
    
    async def generate_answer(
        self, 
        query: str, 
        context_chunks: List[ContextChunk]
    ) -> Tuple[str, float]:
        """Generate answer using LLM with enhanced prompting"""
        
        try:
            if client is None:
                # Fallback response when OpenAI is not available
                context_string = self._construct_context_string(context_chunks)
                fallback_answer = f"Based on the available context:\n\n{context_string[:500]}...\n\nI cannot provide a complete answer as the AI service is not configured."
                return fallback_answer, 0.5
            
            context_string = self._construct_context_string(context_chunks)
            
            user_prompt = QUERY_PROMPT_TEMPLATE.format(
                context=context_string,
                question=query
            )
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Calculate confidence score based on various factors
            confidence_score = self._calculate_confidence_score(
                query, answer, context_chunks, response
            )
            
            return answer, confidence_score
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise HTTPException(status_code=500, detail="Answer generation failed")
    
    def _calculate_confidence_score(
        self, 
        query: str, 
        answer: str, 
        context_chunks: List[ContextChunk],
        llm_response
    ) -> float:
        """Calculate confidence score for the generated answer"""
        
        factors = []
        
        # Factor 1: Average relevance of context chunks
        if context_chunks:
            avg_relevance = sum(chunk.relevance_score for chunk in context_chunks) / len(context_chunks)
            factors.append(avg_relevance)
        
        # Factor 2: Answer length and completeness
        answer_length_score = min(1.0, len(answer) / 200)  # Normalize to reasonable length
        factors.append(answer_length_score)
        
        # Factor 3: Presence of uncertainty indicators
        uncertainty_phrases = ['i don\'t know', 'unclear', 'insufficient information', 'not enough']
        uncertainty_penalty = sum(1 for phrase in uncertainty_phrases if phrase in answer.lower()) * 0.2
        certainty_score = max(0.0, 1.0 - uncertainty_penalty)
        factors.append(certainty_score)
        
        # Factor 4: Citation presence
        citation_score = 1.0 if '[Source:' in answer or 'Source ' in answer else 0.7
        factors.append(citation_score)
        
        return sum(factors) / len(factors) if factors else 0.5

# Initialize RAG system
rag_system = EnhancedRAGSystem()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Enhanced RAG System is running", "version": "2.0.0"}

@app.post("/query", response_model=RAGResponse)
async def query_rag(request: QueryRequest) -> RAGResponse:
    """Main RAG query endpoint with enhanced processing"""
    
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Retrieve and rank context
        context_chunks = await rag_system.retrieve_context(
            request.query, 
            request.filter_params
        )
        
        if not context_chunks:
            return RAGResponse(
                query=request.query,
                answer="I don't have enough information in the knowledge base to answer this question.",
                sources=[],
                context_used=[],
                confidence_score=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now()
            )
        
        # Generate answer
        answer, confidence_score = await rag_system.generate_answer(
            request.query, 
            context_chunks[:request.max_results]
        )
        
        # Prepare sources
        sources = [
            {
                "id": chunk.source_id,
                "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "metadata": chunk.metadata,
                "relevance_score": chunk.relevance_score
            }
            for chunk in context_chunks[:request.max_results]
        ]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Query processed successfully in {processing_time:.2f}s with confidence {confidence_score:.2f}")
        
        return RAGResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            context_used=context_chunks[:request.max_results] if request.include_metadata else [],
            confidence_score=confidence_score,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db_status = "healthy"
        doc_count = rag_system.db.count() if rag_system.db else 0
        
        # Test OpenAI connection
        openai_status = "healthy" if os.getenv("OPENAI_API_KEY") else "no_api_key"
        
        return {
            "status": "healthy",
            "database": db_status,
            "document_count": doc_count,
            "openai": openai_status,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }

@app.get("/config")
async def get_config():
    """Get current RAG configuration"""
    return {
        "max_context_length": config.max_context_length,
        "top_k_retrieval": config.top_k_retrieval,
        "final_context_chunks": config.final_context_chunks,
        "min_relevance_score": config.min_relevance_score,
        "model": config.model,
        "temperature": config.temperature
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 