import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from models import Feedback, QueryLog
from openai import OpenAI
from pydantic import BaseModel, Field
from scipy import stats
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EvaluationRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    response: str = Field(..., min_length=1, max_length=5000)
    context_sources: Optional[List[str]] = Field(default=None)


class EvaluationResult(BaseModel):
    overall_score: float = Field(..., ge=0, le=5)
    relevance_score: float = Field(..., ge=0, le=5)
    accuracy_score: float = Field(..., ge=0, le=5)
    clarity_score: float = Field(..., ge=0, le=5)
    confidence_interval: Tuple[float, float]
    feedback: str
    reasoning: str
    evaluation_metadata: Dict


class ABTestConfig(BaseModel):
    test_name: str
    control_version: str = "A"
    treatment_version: str = "B"
    traffic_split: float = Field(default=0.5, ge=0.1, le=0.9)
    minimum_sample_size: int = Field(default=100, ge=30)
    significance_level: float = Field(default=0.05, ge=0.01, le=0.1)


class PerformanceMetrics(BaseModel):
    avg_response_time: float
    avg_quality_score: float
    total_queries: int
    success_rate: float
    user_satisfaction: float
    retrieval_accuracy: float


class EvaluationService:
    """Enhanced evaluation service with statistical rigor"""

    def __init__(self):
        """Initialize the evaluation service"""
        self.evaluation_prompt_template = """
        You are an expert evaluator for RAG (Retrieval-Augmented Generation) systems.

        Evaluate the following response on a scale of 0-5 for each criterion:

        Query: {query}
        Response: {response}
        Context Sources: {context_sources}

        Evaluation Criteria:
        1. RELEVANCE (0-5): How well does the response address the specific query?
        2. ACCURACY (0-5): Is the information factually correct based on the sources?
        3. CLARITY (0-5): Is the response clear, coherent, and well-structured?
        4. COMPLETENESS (0-5): Does the response adequately cover the query scope?

        Respond with ONLY valid JSON in this exact format:
        {{
            "relevance_score": <float 0-5>,
            "accuracy_score": <float 0-5>,
            "clarity_score": <float 0-5>,
            "completeness_score": <float 0-5>,
            "reasoning": "<detailed explanation>",
            "confidence": <float 0-1>
        }}
        """

    async def evaluate_response(self, request: EvaluationRequest) -> EvaluationResult:
        """Evaluate response quality with statistical confidence"""
        try:
            # Format context sources for evaluation
            context_str = (
                "\n".join(request.context_sources)
                if request.context_sources
                else "No context provided"
            )

            prompt = self.evaluation_prompt_template.format(
                query=request.query,
                response=request.response,
                context_sources=context_str,
            )

            # Get LLM evaluation with retry logic
            evaluation_data = await self._get_llm_evaluation(prompt)

            # Calculate overall score
            scores = [
                evaluation_data["relevance_score"],
                evaluation_data["accuracy_score"],
                evaluation_data["clarity_score"],
                evaluation_data["completeness_score"],
            ]
            overall_score = np.mean(scores)

            # Calculate confidence interval (assuming normal distribution)
            confidence_interval = self._calculate_confidence_interval(
                scores, evaluation_data["confidence"]
            )

            return EvaluationResult(
                overall_score=overall_score,
                relevance_score=evaluation_data["relevance_score"],
                accuracy_score=evaluation_data["accuracy_score"],
                clarity_score=evaluation_data["clarity_score"],
                confidence_interval=confidence_interval,
                feedback=f"Overall quality: {overall_score:.2f}/5.0",
                reasoning=evaluation_data["reasoning"],
                evaluation_metadata={
                    "completeness_score": evaluation_data["completeness_score"],
                    "evaluator_confidence": evaluation_data["confidence"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "evaluation_version": "1.0",
                },
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Return fallback evaluation
            return EvaluationResult(
                overall_score=2.5,
                relevance_score=2.5,
                accuracy_score=2.5,
                clarity_score=2.5,
                confidence_interval=(2.0, 3.0),
                feedback="Evaluation failed - manual review required",
                reasoning=f"Automatic evaluation failed: {str(e)}",
                evaluation_metadata={"error": str(e), "fallback": True},
            )

    async def _get_llm_evaluation(self, prompt: str, max_retries: int = 3) -> Dict:
        """Get LLM evaluation with robust error handling"""
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise evaluator. Respond only with valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,  # Low temperature for consistent evaluation
                    max_tokens=500,
                )

                result_text = response.choices[0].message.content.strip()

                # Clean and parse JSON response
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]

                evaluation_data = json.loads(result_text)

                # Validate required fields
                required_fields = [
                    "relevance_score",
                    "accuracy_score",
                    "clarity_score",
                    "completeness_score",
                    "reasoning",
                    "confidence",
                ]
                if not all(field in evaluation_data for field in required_fields):
                    raise ValueError("Missing required fields in evaluation response")

                # Validate score ranges
                for score_field in [
                    "relevance_score",
                    "accuracy_score",
                    "clarity_score",
                    "completeness_score",
                ]:
                    score = evaluation_data[score_field]
                    if not (0 <= score <= 5):
                        raise ValueError(f"Score {score_field} out of range: {score}")

                return evaluation_data

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Evaluation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Failed to get valid evaluation after {max_retries} attempts"
                    ) from e
                await asyncio.sleep(1)  # Brief delay before retry


    def _calculate_confidence_interval(
        self, scores: List[float], evaluator_confidence: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the evaluation"""
        mean_score = np.mean(scores)
        std_score = np.std(scores) if len(scores) > 1 else 0.5

        # Adjust standard error based on evaluator confidence
        adjusted_se = std_score * (1 - evaluator_confidence + 0.1)

        # 95% confidence interval
        margin_error = 1.96 * adjusted_se
        return (max(0, mean_score - margin_error), min(5, mean_score + margin_error))


class ABTestingService:
    """Statistically rigorous A/B testing framework"""

    def __init__(self):
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[Dict]] = {}

    def create_ab_test(self, config: ABTestConfig) -> bool:
        """Create new A/B test with proper experimental design"""
        # Calculate required sample size for statistical power
        required_sample = self._calculate_sample_size(
            effect_size=0.2,  # Minimum detectable effect
            power=0.8,
            alpha=config.significance_level,
        )

        config.minimum_sample_size = max(config.minimum_sample_size, required_sample)
        self.active_tests[config.test_name] = config
        self.test_results[config.test_name] = []

        logger.info(
            f"Created A/B test '{config.test_name}' requiring {required_sample} samples per variant"
        )
        return True

    def assign_variant(self, test_name: str, user_id: int) -> str:
        """Assign user to test variant using stratified randomization"""
        if test_name not in self.active_tests:
            return "A"  # Default to control

        config = self.active_tests[test_name]

        # Use consistent hash-based assignment
        hash_input = f"{test_name}_{user_id}"
        hash_value = hash(hash_input) % 100

        if hash_value < (config.traffic_split * 100):
            return config.treatment_version
        else:
            return config.control_version

    def record_result(
        self, test_name: str, variant: str, user_id: int, outcome_metric: float
    ):
        """Record test result with metadata"""
        if test_name not in self.test_results:
            return

        self.test_results[test_name].append(
            {
                "variant": variant,
                "user_id": user_id,
                "outcome": outcome_metric,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def analyze_test_results(self, test_name: str) -> Dict:
        """Perform statistical analysis of A/B test results"""
        if test_name not in self.test_results:
            return {"error": "Test not found"}

        results = self.test_results[test_name]
        config = self.active_tests[test_name]

        # Separate results by variant
        control_results = [
            r["outcome"] for r in results if r["variant"] == config.control_version
        ]
        treatment_results = [
            r["outcome"] for r in results if r["variant"] == config.treatment_version
        ]

        if len(control_results) < 30 or len(treatment_results) < 30:
            return {
                "status": "insufficient_data",
                "message": "Need at least 30 samples per variant",
            }

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(treatment_results, control_results)

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(
            (
                (len(control_results) - 1) * np.var(control_results, ddof=1)
                + (len(treatment_results) - 1) * np.var(treatment_results, ddof=1)
            )
            / (len(control_results) + len(treatment_results) - 2)
        )

        cohens_d = (np.mean(treatment_results) - np.mean(control_results)) / pooled_std

        # Determine statistical significance
        is_significant = p_value < config.significance_level

        return {
            "status": "complete" if is_significant else "inconclusive",
            "control_mean": np.mean(control_results),
            "treatment_mean": np.mean(treatment_results),
            "lift": (
                (np.mean(treatment_results) - np.mean(control_results))
                / np.mean(control_results)
            )
            * 100,
            "p_value": p_value,
            "effect_size": cohens_d,
            "confidence_level": 1 - config.significance_level,
            "sample_sizes": {
                "control": len(control_results),
                "treatment": len(treatment_results),
            },
            "recommendation": "deploy"
            if (
                is_significant and np.mean(treatment_results) > np.mean(control_results)
            )
            else "no_change",
        }

    def _calculate_sample_size(
        self, effect_size: float, power: float, alpha: float
    ) -> int:
        """Calculate required sample size for statistical power"""
        # Simplified calculation - in production, use proper power analysis libraries
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)

        n = 2 * ((z_alpha + z_beta) ** 2) / (effect_size**2)
        return int(np.ceil(n))


class MonitoringService:
    """Enhanced monitoring with ML-specific metrics"""

    def get_performance_metrics(self, db: Session, days: int = 7) -> PerformanceMetrics:
        """Get comprehensive performance metrics"""
        try:
            # Query performance data
            recent_queries = (
                db.query(QueryLog)
                .filter(QueryLog.created_at >= datetime.utcnow() - timedelta(days=days))
                .all()
            )

            if not recent_queries:
                return PerformanceMetrics(
                    avg_response_time=0.0,
                    avg_quality_score=0.0,
                    total_queries=0,
                    success_rate=0.0,
                    user_satisfaction=0.0,
                    retrieval_accuracy=0.0,
                )

            # Calculate metrics
            response_times = [
                q.processing_time for q in recent_queries if q.processing_time
            ]
            confidence_scores = [
                q.confidence_score for q in recent_queries if q.confidence_score
            ]
            successful_queries = [q for q in recent_queries if q.status == "completed"]

            # Get user feedback data
            feedback_data = (
                db.query(Feedback)
                .join(QueryLog)
                .filter(QueryLog.created_at >= datetime.utcnow() - timedelta(days=days))
                .all()
            )

            user_ratings = [f.rating for f in feedback_data]

            return PerformanceMetrics(
                avg_response_time=np.mean(response_times) if response_times else 0.0,
                avg_quality_score=np.mean(confidence_scores)
                if confidence_scores
                else 0.0,
                total_queries=len(recent_queries),
                success_rate=len(successful_queries) / len(recent_queries)
                if recent_queries
                else 0.0,
                user_satisfaction=np.mean(user_ratings) if user_ratings else 0.0,
                retrieval_accuracy=self._calculate_retrieval_accuracy(recent_queries),
            )

        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(
                avg_response_time=0.0,
                avg_quality_score=0.0,
                total_queries=0,
                success_rate=0.0,
                user_satisfaction=0.0,
                retrieval_accuracy=0.0,
            )

    def _calculate_retrieval_accuracy(self, queries: List[QueryLog]) -> float:
        """Calculate retrieval accuracy based on confidence scores and feedback"""
        if not queries:
            return 0.0

        # Simple heuristic: queries with high confidence and positive feedback
        high_quality_queries = [
            q for q in queries if q.confidence_score and q.confidence_score > 0.7
        ]

        return len(high_quality_queries) / len(queries) if queries else 0.0


# Global service instances
evaluation_service = EvaluationService()
ab_testing_service = ABTestingService()
monitoring_service = MonitoringService()
