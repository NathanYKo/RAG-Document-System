from unittest.mock import Mock, patch

import pytest
from evaluation import (
    ABTestConfig,
    EvaluationRequest,
    EvaluationResult,
    PerformanceMetrics,
    ab_testing_service,
    evaluation_service,
    monitoring_service,
)
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "relevance_score": 4.2,
        "accuracy_score": 4.0,
        "clarity_score": 4.5,
        "completeness_score": 3.8,
        "reasoning": "The response addresses the query well with clear information.",
        "confidence": 0.85,
    }


@pytest.fixture
def sample_evaluation_request():
    """Sample evaluation request"""
    return EvaluationRequest(
        query="What is machine learning?",
        response="Machine learning is a subset of AI that enables computers to learn without explicit programming.",
        context_sources=["Source 1: ML textbook", "Source 2: Research paper"],
    )


class TestEvaluationService:
    """Test the EvaluationService class"""

    @pytest.mark.asyncio
    async def test_evaluate_response_success(
        self, mock_openai_response, sample_evaluation_request
    ):
        """Test successful response evaluation"""
        with patch.object(
            evaluation_service, "_get_llm_evaluation", return_value=mock_openai_response
        ):
            result = await evaluation_service.evaluate_response(
                sample_evaluation_request
            )

            assert isinstance(result, EvaluationResult)
            assert 0 <= result.overall_score <= 5
            assert result.relevance_score == 4.2
            assert result.accuracy_score == 4.0
            assert result.clarity_score == 4.5
            assert len(result.confidence_interval) == 2
            assert "evaluation_version" in result.evaluation_metadata

    @pytest.mark.asyncio
    async def test_evaluate_response_failure_fallback(self):
        """Test evaluation failure returns fallback response"""
        request = EvaluationRequest(query="Test query", response="Test response")

        with patch.object(
            evaluation_service,
            "_get_llm_evaluation",
            side_effect=Exception("API Error"),
        ):
            result = await evaluation_service.evaluate_response(request)

            assert result.overall_score == 2.5
            assert result.evaluation_metadata["fallback"] is True
            assert "error" in result.evaluation_metadata

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation"""
        scores = [4.0, 4.2, 3.8, 4.1]
        evaluator_confidence = 0.8

        ci = evaluation_service._calculate_confidence_interval(
            scores, evaluator_confidence
        )

        assert len(ci) == 2
        assert ci[0] <= ci[1]  # Lower bound <= upper bound
        assert 0 <= ci[0] <= 5
        assert 0 <= ci[1] <= 5


class TestABTestingService:
    """Test the ABTestingService class"""

    def test_create_ab_test(self):
        """Test A/B test creation"""
        config = ABTestConfig(
            test_name="embedding_model_test",
            control_version="sentence-transformers",
            treatment_version="openai-embeddings",
            traffic_split=0.5,
            minimum_sample_size=100,
            significance_level=0.05,
        )

        success = ab_testing_service.create_ab_test(config)

        assert success is True
        assert "embedding_model_test" in ab_testing_service.active_tests
        assert "embedding_model_test" in ab_testing_service.test_results

    def test_assign_variant_consistency(self):
        """Test that variant assignment is consistent for same user"""
        config = ABTestConfig(test_name="test_consistency")
        ab_testing_service.create_ab_test(config)

        user_id = 12345
        variant1 = ab_testing_service.assign_variant("test_consistency", user_id)
        variant2 = ab_testing_service.assign_variant("test_consistency", user_id)

        assert variant1 == variant2  # Should be consistent
        assert variant1 in ["A", "B"]

    def test_assign_variant_distribution(self):
        """Test that variant assignment follows traffic split"""
        config = ABTestConfig(test_name="test_distribution", traffic_split=0.3)
        ab_testing_service.create_ab_test(config)

        # Test with many users to check distribution
        variants = []
        for user_id in range(1000):
            variant = ab_testing_service.assign_variant("test_distribution", user_id)
            variants.append(variant)

        b_ratio = variants.count("B") / len(variants)
        # Should be approximately 30% (with some tolerance)
        assert 0.25 <= b_ratio <= 0.35


class TestMonitoringService:
    """Test the MonitoringService class"""

    def test_performance_metrics_structure(self):
        """Test that performance metrics have correct structure"""
        # Create a mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        metrics = monitoring_service.get_performance_metrics(mock_db, days=7)

        assert isinstance(metrics, PerformanceMetrics)
        assert hasattr(metrics, "avg_response_time")
        assert hasattr(metrics, "avg_quality_score")
        assert hasattr(metrics, "total_queries")
        assert hasattr(metrics, "success_rate")
        assert hasattr(metrics, "user_satisfaction")
        assert hasattr(metrics, "retrieval_accuracy")


class TestHealthCheck:
    """Test system health and basic functionality"""

    def test_health_endpoint(self, test_client):
        """Test that health endpoint is accessible"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self, test_client):
        """Test that root endpoint is accessible"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Enterprise Document Intelligence System"


class TestIntegration:
    """Test integration scenarios"""

    def test_evaluation_request_validation(self):
        """Test that evaluation requests are properly validated"""
        # Valid request
        valid_request = EvaluationRequest(query="Test query", response="Test response")
        assert valid_request.query == "Test query"
        assert valid_request.response == "Test response"

        # Test field validation
        with pytest.raises(ValueError):
            EvaluationRequest(query="", response="Test")  # Empty query

        with pytest.raises(ValueError):
            EvaluationRequest(query="Test", response="")  # Empty response

    def test_ab_test_config_validation(self):
        """Test that A/B test configs are properly validated"""
        # Valid config
        valid_config = ABTestConfig(test_name="valid_test", traffic_split=0.5)
        assert valid_config.test_name == "valid_test"
        assert valid_config.traffic_split == 0.5

        # Test validation constraints
        with pytest.raises(ValueError):
            ABTestConfig(test_name="invalid", traffic_split=1.5)  # Invalid split

        with pytest.raises(ValueError):
            ABTestConfig(test_name="invalid", significance_level=0.5)  # Invalid alpha


def test_imports_work():
    """Test that all imports work correctly"""
    from evaluation import (
        ABTestConfig,
        EvaluationRequest,
        EvaluationResult,
        PerformanceMetrics,
        ab_testing_service,
        evaluation_service,
        monitoring_service,
    )

    # Test that services are properly initialized
    assert evaluation_service is not None
    assert ab_testing_service is not None
    assert monitoring_service is not None

    # Test that classes are properly defined
    assert EvaluationRequest is not None
    assert EvaluationResult is not None
    assert ABTestConfig is not None
    assert PerformanceMetrics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
