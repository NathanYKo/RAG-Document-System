import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from rag import app, rag_system, RAGConfig, ContextChunk
from vector_database import ChromaDB

# Test client
client = TestClient(app)

# Test configuration
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "This is a test answer based on the provided context. [Source: test_doc_1]"
    return mock_response

@pytest.fixture
def sample_context_chunks():
    """Sample context chunks for testing"""
    return [
        ContextChunk(
            content="This is the first test document about artificial intelligence.",
            source_id="doc_1",
            metadata={"source": "test_document_1.pdf", "file_type": "pdf"},
            relevance_score=0.9,
            retrieval_method="semantic"
        ),
        ContextChunk(
            content="This is the second test document discussing machine learning algorithms.",
            source_id="doc_2", 
            metadata={"source": "test_document_2.pdf", "file_type": "pdf"},
            relevance_score=0.8,
            retrieval_method="semantic"
        ),
        ContextChunk(
            content="This is the third document about neural networks and deep learning.",
            source_id="doc_3",
            metadata={"source": "test_document_3.pdf", "file_type": "pdf"},
            relevance_score=0.7,
            retrieval_method="semantic"
        )
    ]

class TestRAGSystem:
    """Test suite for the enhanced RAG system"""
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Enhanced RAG System is running" in data["message"]
    
    def test_health_check_detailed(self):
        """Test detailed health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
    
    def test_config_endpoint(self):
        """Test configuration endpoint"""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "max_context_length" in data
        assert "top_k_retrieval" in data
        assert "model" in data
    
    @patch('rag.client.chat.completions.create')
    def test_query_endpoint_success(self, mock_openai, mock_openai_response):
        """Test successful query processing"""
        mock_openai.return_value = mock_openai_response
        
        # Mock database query to return test results
        with patch.object(rag_system.db, 'query') as mock_query:
            mock_query.return_value = {
                'documents': [['Test document content about AI']],
                'ids': [['test_doc_1']],
                'metadatas': [[{'source': 'test.pdf', 'file_type': 'pdf'}]],
                'distances': [[0.1]]
            }
            
            response = client.post(
                "/query",
                json={"query": "What is artificial intelligence?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "answer" in data
            assert "sources" in data
            assert "confidence_score" in data
            assert "processing_time" in data
    
    def test_query_endpoint_validation(self):
        """Test query endpoint input validation"""
        # Empty query
        response = client.post("/query", json={"query": ""})
        assert response.status_code == 422
        
        # Query too long
        long_query = "x" * 1001
        response = client.post("/query", json={"query": long_query})
        assert response.status_code == 422
        
        # Invalid max_results
        response = client.post("/query", json={"query": "test", "max_results": 0})
        assert response.status_code == 422
        
        response = client.post("/query", json={"query": "test", "max_results": 25})
        assert response.status_code == 422
    
    @patch('rag.client.chat.completions.create')
    def test_query_no_context_found(self, mock_openai, mock_openai_response):
        """Test query when no relevant context is found"""
        mock_openai.return_value = mock_openai_response
        
        with patch.object(rag_system.db, 'query') as mock_query:
            mock_query.return_value = {
                'documents': [[]],
                'ids': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
            
            response = client.post(
                "/query",
                json={"query": "What is quantum computing?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "don't have enough information" in data["answer"]
            assert data["confidence_score"] == 0.0
            assert len(data["sources"]) == 0

class TestEnhancedRAGSystem:
    """Test the core RAG system functionality"""
    
    @pytest.mark.asyncio
    async def test_context_retrieval(self, sample_context_chunks):
        """Test context retrieval and ranking"""
        with patch.object(rag_system.db, 'query') as mock_query:
            mock_query.return_value = {
                'documents': [[chunk.content for chunk in sample_context_chunks]],
                'ids': [[chunk.source_id for chunk in sample_context_chunks]],
                'metadatas': [[chunk.metadata for chunk in sample_context_chunks]],
                'distances': [[1 - chunk.relevance_score for chunk in sample_context_chunks]]
            }
            
            result = await rag_system.retrieve_context("test query")
            
            assert len(result) > 0
            assert all(isinstance(chunk, ContextChunk) for chunk in result)
            # Should be sorted by relevance score
            assert result[0].relevance_score >= result[-1].relevance_score
    
    @pytest.mark.asyncio 
    async def test_advanced_filtering(self, sample_context_chunks):
        """Test advanced filtering functionality"""
        # Test file type filtering
        filter_params = {"file_type": "pdf"}
        filtered = await rag_system._apply_advanced_filtering(
            sample_context_chunks, "test query", filter_params
        )
        
        assert all(chunk.metadata.get("file_type") == "pdf" for chunk in filtered)
        
        # Test minimum score filtering
        filter_params = {"min_score": 0.75}
        filtered = await rag_system._apply_advanced_filtering(
            sample_context_chunks, "test query", filter_params
        )
        
        assert all(chunk.relevance_score >= 0.75 for chunk in filtered)
    
    def test_diversity_filtering(self, sample_context_chunks):
        """Test diversity filtering to avoid redundant content"""
        # Create similar chunks
        similar_chunks = [
            ContextChunk(
                content="Machine learning is a subset of artificial intelligence",
                source_id="doc_a",
                metadata={},
                relevance_score=0.9,
                retrieval_method="semantic"
            ),
            ContextChunk(
                content="Machine learning represents a subset of artificial intelligence",
                source_id="doc_b", 
                metadata={},
                relevance_score=0.85,
                retrieval_method="semantic"
            )
        ]
        
        diverse = rag_system._ensure_diversity(similar_chunks)
        # Should filter out very similar content
        assert len(diverse) < len(similar_chunks)
    
    def test_context_window_management(self, sample_context_chunks):
        """Test optimal context selection within token limits"""
        # Create chunks that would exceed context window
        large_chunks = []
        for i, chunk in enumerate(sample_context_chunks):
            large_chunk = ContextChunk(
                content=chunk.content * 100,  # Make very large
                source_id=f"large_doc_{i}",
                metadata=chunk.metadata,
                relevance_score=chunk.relevance_score,
                retrieval_method=chunk.retrieval_method
            )
            large_chunks.append(large_chunk)
        
        selected = rag_system._select_optimal_context(large_chunks)
        
        # Should respect context limits
        total_length = sum(len(chunk.content) for chunk in selected)
        estimated_tokens = total_length // 4
        assert estimated_tokens <= RAGConfig().max_context_length
    
    def test_context_string_construction(self, sample_context_chunks):
        """Test context string formatting"""
        context_str = rag_system._construct_context_string(sample_context_chunks)
        
        assert "Source 1" in context_str
        assert "Source 2" in context_str
        assert sample_context_chunks[0].content in context_str
        assert sample_context_chunks[0].source_id in context_str
    
    def test_confidence_score_calculation(self, sample_context_chunks, mock_openai_response):
        """Test confidence score calculation"""
        confidence = rag_system._calculate_confidence_score(
            "test query",
            "This is a comprehensive answer with citations [Source: doc_1]",
            sample_context_chunks,
            mock_openai_response
        )
        
        assert 0.0 <= confidence <= 1.0
        
        # Test with uncertain answer
        uncertain_confidence = rag_system._calculate_confidence_score(
            "test query", 
            "I don't know the answer to this question",
            sample_context_chunks,
            mock_openai_response
        )
        
        assert uncertain_confidence < confidence
    
    @pytest.mark.asyncio
    @patch('rag.client.chat.completions.create')
    async def test_answer_generation(self, mock_openai, sample_context_chunks, mock_openai_response):
        """Test answer generation with LLM"""
        mock_openai.return_value = mock_openai_response
        
        answer, confidence = await rag_system.generate_answer(
            "What is AI?", 
            sample_context_chunks
        )
        
        assert len(answer) > 0
        assert 0.0 <= confidence <= 1.0
        assert mock_openai.called

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @patch('rag.client.chat.completions.create')
    def test_openai_api_error(self, mock_openai):
        """Test handling of OpenAI API errors"""
        mock_openai.side_effect = Exception("API Error")
        
        with patch.object(rag_system.db, 'query') as mock_query:
            mock_query.return_value = {
                'documents': [['Test content']],
                'ids': [['test_id']],
                'metadatas': [[{}]],
                'distances': [[0.1]]
            }
            
            response = client.post("/query", json={"query": "test query"})
            assert response.status_code == 500
    
    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        with patch.object(rag_system, 'db', None):
            response = client.post("/query", json={"query": "test query"})
            assert response.status_code == 500

class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    @patch('rag.client.chat.completions.create')
    async def test_response_time(self, mock_openai, mock_openai_response):
        """Test that responses are generated within reasonable time"""
        mock_openai.return_value = mock_openai_response
        
        with patch.object(rag_system.db, 'query') as mock_query:
            mock_query.return_value = {
                'documents': [['Fast test content']],
                'ids': [['fast_test']],
                'metadatas': [[{}]],
                'distances': [[0.1]]
            }
            
            start_time = datetime.now()
            response = client.post("/query", json={"query": "fast test"})
            end_time = datetime.now()
            
            assert response.status_code == 200
            processing_time = (end_time - start_time).total_seconds()
            assert processing_time < 30  # Should complete within 30 seconds
            
            # Check reported processing time
            data = response.json()
            assert data["processing_time"] > 0

# Integration tests
class TestIntegration:
    """Integration tests with real components"""
    
    @pytest.mark.integration
    def test_end_to_end_with_sample_data(self):
        """End-to-end test with sample document data"""
        # This would require actual document processing and embedding
        # Skip if no test data available
        if not os.path.exists("sample_document.txt"):
            pytest.skip("No sample document available for integration test")
        
        # Test would involve:
        # 1. Processing sample document
        # 2. Querying the RAG system
        # 3. Validating response quality
        pass

# Fixtures for test setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment"""
    # Set test environment variables
    os.environ["OPENAI_API_KEY"] = "test_key_12345"
    yield
    # Cleanup if needed

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 