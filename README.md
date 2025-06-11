# Enterprise Document Intelligence System with RAG

A comprehensive enterprise-grade document intelligence system that combines document processing, vector search, retrieval-augmented generation (RAG), and advanced monitoring capabilities. Built with FastAPI, Streamlit, and modern AI technologies.

## 🚀 Features

### Core Capabilities
- **📄 Multi-format Document Processing**: PDF, DOCX, TXT with intelligent chunking
- **🔍 Advanced Vector Search**: ChromaDB with sentence transformers for semantic search  
- **🤖 RAG-powered Q&A**: OpenAI GPT integration for intelligent document querying
- **👥 User Management**: JWT-based authentication with role-based access control
- **📊 Real-time Monitoring**: Performance metrics, system health, and user analytics

### Enterprise Features  
- **🧪 A/B Testing Framework**: Statistically rigorous experimentation platform
- **📈 Response Evaluation**: LLM-as-a-judge quality scoring with confidence intervals
- **🎯 Performance Monitoring**: ML-specific metrics and alerting
- **📱 Interactive Dashboard**: Real-time monitoring with Streamlit and Plotly
- **🐳 Container Deployment**: Docker and Docker Compose support
- **☸️ Production Ready**: Prometheus monitoring, logging, and error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Vector DB     │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Database      │    │   OpenAI API    │
│   (Monitoring)  │    │  (SQLite/PG)    │    │     (GPT)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (optional)
- OpenAI API key

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd Enterprise-Document-Intelligence-System-with-RAG

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
export OPENAI_API_KEY="your_openai_api_key_here"
export DATABASE_URL="sqlite:///./enterprise_rag.db"
export JWT_SECRET_KEY="your_secret_key_here"
```

### 3. Database Setup

```bash
cd backend
python init_db.py
```

### 4. Start the Services

**Option A: Development Mode**
```bash
# Terminal 1: Start Backend API
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start Frontend
cd frontend
streamlit run app.py --server.port 8501

# Terminal 3: Start Monitoring Dashboard
streamlit run monitoring/dashboard/dashboard.py --server.port 8502
```

**Option B: Docker Compose**
```bash
docker-compose up -d
```

### 5. Access the System

- **API Documentation**: http://localhost:8000/docs
- **Frontend Interface**: http://localhost:8501  
- **Monitoring Dashboard**: http://localhost:8502
- **Health Check**: http://localhost:8000/health

## 📖 Usage Guide

### 1. Document Upload & Processing

```python
import requests

# Upload a document
files = {'file': open('document.pdf', 'rb')}
response = requests.post(
    'http://localhost:8000/documents/upload',
    files=files,
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

### 2. Query Documents

```python
# Query the knowledge base
query_data = {
    "query": "What is the main topic of the documents?",
    "max_results": 5
}
response = requests.post(
    'http://localhost:8000/query',
    json=query_data,
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

### 3. Evaluate Response Quality

```python
# Evaluate a response
eval_data = {
    "query": "What is machine learning?",
    "response": "Machine learning is a subset of AI...",
    "context_sources": ["AI Textbook Chapter 1"]
}
response = requests.post(
    'http://localhost:8000/evaluate',
    json=eval_data,
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

### 4. A/B Testing

```python
# Create A/B test (admin only)
test_config = {
    "test_name": "embedding_comparison",
    "control_version": "sentence-transformers", 
    "treatment_version": "openai-embeddings",
    "traffic_split": 0.5
}
response = requests.post(
    'http://localhost:8000/ab-tests',
    json=test_config,
    headers={'Authorization': 'Bearer ADMIN_TOKEN'}
)
```

## 🧪 Testing

### Run Test Suite

```bash
# Backend tests
cd backend
pytest test_evaluation_system.py -v

# Integration tests  
pytest test_backend.py -v

# End-to-end tests
python ../test_e2e.py
```

### Test Coverage

```bash
pytest --cov=. --cov-report=html
```

## 🔧 API Reference

### Authentication Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/token` - Login and get JWT token

### Document Management
- `POST /documents/upload` - Upload and process documents
- `GET /documents` - List user's documents  
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document

### Query & RAG
- `POST /query` - Query document knowledge base
- `GET /queries` - Get query history

### Evaluation & Monitoring
- `POST /evaluate` - Evaluate response quality
- `POST /ab-tests` - Create A/B test (admin)
- `GET /metrics/performance` - System performance metrics
- `GET /metrics/dashboard` - Dashboard data

### System Health
- `GET /health` - System health check
- `GET /` - API information

## 🐳 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.yml up -d

# With monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Production deployment
docker-compose -f docker-compose.fullstack.yml up -d
```

### AWS ECS Deployment

```bash
# Deploy to AWS ECS
./setup_deployment.sh

# Configure ECS task definition
aws ecs update-service --cluster rag-cluster --service rag-service
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./enterprise_rag.db` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000,http://localhost:8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 📊 Monitoring & Analytics

### Performance Metrics
- Response time distribution
- Query success rates  
- User satisfaction scores
- System resource utilization

### Dashboard Features
- Real-time performance monitoring
- Interactive visualizations
- System health indicators
- User analytics and feedback

### Alerting
- Prometheus metrics integration
- Custom alert rules for system health
- Performance degradation detection

## 🔍 Key Components

### Backend (`/backend`)
- **FastAPI application** with async support
- **SQLAlchemy ORM** for database operations
- **JWT authentication** and authorization
- **OpenAI integration** for RAG capabilities
- **ChromaDB** for vector storage and search

### Frontend (`/frontend`) 
- **Streamlit interface** for document management
- **User-friendly upload** and query interface
- **Real-time feedback** collection
- **Responsive design** with modern UI

### Monitoring (`/monitoring`)
- **Performance dashboard** with real-time metrics
- **Prometheus integration** for metrics collection
- **Alert rules** for system health monitoring
- **Custom visualizations** with Plotly

### Evaluation System
- **LLM-as-a-judge** response quality evaluation
- **Statistical A/B testing** framework
- **Confidence intervals** for evaluation scores
- **Performance tracking** and analytics

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `pip install -r backend/requirements.txt`
4. Make your changes and add tests
5. Run the test suite: `pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings for all functions and classes
- Maintain test coverage above 80%

### Adding New Features

1. **Document Processors**: Add new file format support in `document_processor.py`
2. **Evaluation Metrics**: Extend evaluation framework in `evaluation.py`
3. **Dashboard Widgets**: Add new visualizations in `monitoring/dashboard/`
4. **API Endpoints**: Add new endpoints in `main.py` with proper authentication

## 📋 Project Structure

```
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API application
│   ├── evaluation.py          # Evaluation & monitoring services
│   ├── models.py              # Database models
│   ├── auth.py                # Authentication logic
│   ├── rag.py                 # RAG implementation
│   └── test_evaluation_system.py # Test suite
├── frontend/                   # Streamlit frontend
│   └── app.py                 # Main frontend application
├── monitoring/                 # Monitoring & dashboard
│   ├── dashboard/
│   │   └── dashboard.py       # Real-time monitoring dashboard
│   ├── prometheus.yml         # Prometheus configuration
│   └── alert_rules.yml        # Alert rules
├── enterprise_rag_system/      # Documentation
│   └── step_07_evaluation_and_monitoring_corrected.md
├── docker-compose.yml          # Docker compose configuration
├── requirements.txt            # Dependencies
└── README.md                  # This file
```

## 🚨 Troubleshooting

### Common Issues

**OpenAI API Errors**
```bash
# Check API key configuration
echo $OPENAI_API_KEY
# Verify API key validity at https://platform.openai.com/api-keys
```

**Database Connection Issues**
```bash
# Reset database
cd backend && python init_db.py
```

**Docker Issues**
```bash
# Rebuild containers
docker-compose down && docker-compose up --build
```

**Import Errors**
```bash
# Install dependencies
pip install -r backend/requirements.txt
```

### Performance Optimization

- Increase `chunk_size` for faster processing of large documents
- Use `max_results` parameter to limit query response size  
- Enable caching for frequently accessed documents
- Monitor dashboard for performance bottlenecks

### Getting Help

- Check the [API documentation](http://localhost:8000/docs) for endpoint details
- Review the [monitoring dashboard](http://localhost:8502) for system health
- Open an issue for bugs or feature requests
- Join our community discussions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and embedding APIs
- **ChromaDB** for vector database functionality  
- **FastAPI** for the excellent web framework
- **Streamlit** for rapid dashboard development
- **Prometheus** for monitoring and alerting

---

**Enterprise Document Intelligence System** - Transform your documents into intelligent, searchable knowledge with advanced AI capabilities.

For more information, visit our [documentation](enterprise_rag_system/) or check the [deployment guide](DEPLOYMENT.md).
