# Evaluation & Monitoring Implementation

**Generated:** 2025-06-07T21:03:49.654798

Here is a complete implementation of an evaluation and monitoring system for the RAG system, including all the requested features:

1. Code Files:

evaluation.py:
```python
import os
import openai
from database import SessionLocal
from models import Feedback, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class EvaluationRequest(BaseModel):
    query: str
    response: str

class EvaluationResult(BaseModel):
    score: float
    feedback: str

@app.post("/evaluate", response_model=EvaluationResult)
def evaluate_response(request: EvaluationRequest):
    prompt = f"""
    Please evaluate the following response to the given query and provide a quality score and feedback.

    Query: {request.query}
    Response: {request.response}

    Evaluation Criteria:
    - Relevance: How well does the response address the query?
    - Accuracy: Is the information in the response accurate and factual? 
    - Clarity: Is the response clear, coherent and easy to understand?
    - Insightfulness: Does the response provide insightful or novel information?

    Please provide a score between 1-5 (1=very poor, 5=excellent) and a brief explanation of your evaluation.
    """

    evaluation = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI response evaluation assistant. Provide honest and objective evaluations."},
            {"role": "user", "content": prompt}
        ]
    )

    result = evaluation.choices[0].message.content
    score = float(result.split("Score:")[1].split("Feedback:")[0])
    feedback = result.split("Feedback:")[1].strip()

    return EvaluationResult(score=score, feedback=feedback)

@app.post("/log_feedback")
def log_feedback(feedback: Feedback, db: Session = Depends(get_db)):
    db.add(feedback)
    db.commit()

@app.get("/query_metrics")
def get_query_metrics(db: Session = Depends(get_db)):
    total_queries = db.query(func.count(Query.id)).scalar()
    avg_quality_score = db.query(func.avg(Response.quality_score)).scalar()
    avg_latency = db.query(func.avg(Query.duration)).scalar()
    
    return {
        "total_queries": total_queries,
        "avg_quality_score": avg_quality_score,
        "avg_latency": avg_latency
    }
```

ab_testing.py:
```python
from fastapi import FastAPI, Header
from rag import query_rag
from typing import Optional
import random

app = FastAPI()

@app.post("/query")
async def ab_test_query(query: str, version: Optional[str] = Header(None)):
    if version == "B":
        # Call alternative RAG implementation
        result = await query_rag_v2(query)
    else:  
        # Call default RAG implementation
        result = await query_rag(query)
    
    return result
```

monitoring.py:
```python
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI
import logging
import os

app = FastAPI() 

instrumentator = Instrumentator().instrument(app).expose(app)

gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Add /metrics endpoint to expose Prometheus metrics
metrics.info("app_info", "Application info", version="1.0.0")
instrumentator.expose(app, include_in_schema=False, should_gzip=True)
```

test_evaluation.py:
```python
from fastapi.testclient import TestClient
from evaluation import app

client = TestClient(app)

def test_evaluate_response():
    request = {
        "query": "What is the capital of France?",
        "response": "The capital of France is Paris."
    }
    response = client.post("/evaluate", json=request)
    result = response.json()

    assert response.status_code == 200
    assert "score" in result
    assert "feedback" in result
    assert result["score"] >= 1 and result["score"] <= 5

def test_log_feedback():
    feedback = {
        "query_id": 1,
        "user_id": 1,
        "score": 4,
        "comment": "Good response"
    }
    response = client.post("/log_feedback", json=feedback)
    assert response.status_code == 200

def test_get_query_metrics():
    response = client.get("/query_metrics")
    result = response.json()

    assert response.status_code == 200
    assert "total_queries" in result
    assert "avg_quality_score" in result
    assert "avg_latency" in result
```

dashboard.py:
```python
import streamlit as st
from database import SessionLocal
from sqlalchemy.orm import Session
from models import Query, Response, Feedback
import altair as alt
import pandas as pd

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_charts(df):
    quality_chart = alt.Chart(df).mark_bar().encode(
        x='quality_score:O',
        y='count()',
        tooltip=['quality_score', 'count()']
    ).properties(
        title='Quality Score Distribution'
    )

    latency_chart = alt.Chart(df).mark_bar().encode(
        x='latency_bucket:O',
        y='count()',
        tooltip=['latency_bucket', 'count()']  
    ).properties(
        title='Query Latency Distribution'
    )

    return quality_chart, latency_chart

def main():
    st.set_page_config(page_title="RAG System Dashboard", layout="wide")
    st.title("RAG System Dashboard")

    db = SessionLocal()

    # Query metrics
    st.header("Query Metrics")
    col1, col2, col3 = st.columns(3)

    total_queries = db.query(Query).count()
    col1.metric("Total Queries", total_queries)

    avg_score = db.query(Response.quality_score).scalar()
    col2.metric("Avg Quality Score", round(avg_score,2))

    avg_latency = db.query(Query.duration).scalar()  
    col3.metric("Avg Latency (ms)", round(avg_latency,0))

    # Charts
    query_data = db.query(Query.id, Query.duration, Response.quality_score).join(Response).all()
    df = pd.DataFrame(query_data, columns=["id", "latency", "quality_score"])
    df['latency_bucket'] = pd.qcut(df['latency'], q=5, labels=['<0.2s', '0.2-0.4s', '0.4-0.6s', '0.6-0.8s', '>0.8s'])

    st.header("Charts")
    quality_chart, latency_chart = create_charts(df) 
    st.altair_chart(quality_chart, use_container_width=True)
    st.altair_chart(latency_chart, use_container_width=True)

    # Feedback
    st.header("User Feedback")
    feedback_data = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(10).all()
    for feedback in feedback_data:
        st.text(f"User {feedback.user_id} on Query {feedback.query_id}: {feedback.comment} ({feedback.score} stars)")

if __name__ == "__main__":
    main()
```

2. Setup Instructions:

1. Set up the evaluation API:
   - Save `evaluation.py` and install dependencies
   - Set the `OPENAI_API_KEY` environment variable
   - Run the API with `uvicorn evaluation:app --reload`

2. Set up the A/B testing endpoint:
   - Save `ab_testing.py`
   - Run the API with `uvicorn ab_testing:app --reload`

3. Set up the monitoring API:
   - Save `monitoring.py` and install dependencies
   - Run the API with `uvicorn monitoring:app --reload` 
   - Configure Prometheus to scrape metrics from the `/metrics` endpoint

4. Set up the dashboard:
   - Save `dashboard.py` and install dependencies
   - Run the dashboard with `streamlit run dashboard.py`

3. Dependencies:

evaluation.py:
```
fastapi
sqlalchemy
openai
pydantic
```

ab_testing.py:
```
fastapi
```

monitoring.py:
```
fastapi
prometheus-fastapi-instrumentator
```

dashboard.py:  
```
streamlit
sqlalchemy
altair
pandas
```

4. Configuration:
- Set the `OPENAI_API_KEY` environment variable for the evaluation API
- Configure Prometheus to scrape metrics from the `/metrics` endpoint of the monitoring API

5. Testing:
- Run `pytest test_evaluation.py` to test the evaluation API

6. Integration with Previous Components:

- Update the RAG query endpoint to call the A/B testing endpoint in `ab_testing.py`
- Log queries, responses, and feedback to the database used by the evaluation and dashboard components
- Configure the monitoring API to expose metrics from the RAG backend
- Integrate the dashboard with the database to display RAG system metrics and feedback

This evaluation and monitoring system provides comprehensive features including:
- Automated response quality evaluation using GPT-4
- A/B testing framework for comparing RAG implementations  
- Performance monitoring with Prometheus metrics
- User feedback collection and analysis
- Unit tests for the evaluation API
- System health checks 
- Analytics and reporting dashboard with Streamlit

The components are designed to integrate seamlessly with the existing RAG system. By logging queries, responses, and feedback to a shared database, the evaluation and dashboard components can provide valuable insights into system performance and user satisfaction.

Let me know if you have any other questions! Follow the setup instructions to add these evaluation and monitoring capabilities to your RAG system.