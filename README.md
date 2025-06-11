# Enterprise Document Intelligence System with RAG

A comprehensive enterprise-grade document intelligence system that combines document processing, vector search, retrieval-augmented generation (RAG), and advanced monitoring capabilities. Built with FastAPI, Streamlit, and modern AI technologies.

## Features

### Core Capabilities
- Multi-format Document Processing: PDF, DOCX, TXT with intelligent chunking
- Advanced Vector Search: ChromaDB with sentence transformers for semantic search  
- RAG-powered Q&A: OpenAI GPT integration for intelligent document querying
- User Management: JWT-based authentication with role-based access control
- Real-time Monitoring: Performance metrics, system health, and user analytics

### Enterprise Features  
- A/B Testing Framework: Statistically rigorous experimentation platform
- Response Evaluation: LLM-as-a-judge quality scoring with confidence intervals
- Performance Monitoring: ML-specific metrics and alerting
- Interactive Dashboard: Real-time monitoring with Streamlit and Plotly
- Container Deployment: Docker and Docker Compose support
- Production Ready: Prometheus monitoring, logging, and error handling

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (optional)
- OpenAI API key

### Installation

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

### Configuration

Create a `.env` file with your configuration:

```bash
OPENAI_API_KEY="your_openai_api_key_here"
DATABASE_URL="sqlite:///./enterprise_rag.db"
JWT_SECRET_KEY="your_secret_key_here"
```

### Setup Database

```bash
cd backend
python init_db.py
```

### Run the Application

**Development Mode:**
```bash
# Terminal 1: Backend API
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
streamlit run app.py --server.port 8501

# Terminal 3: Monitoring Dashboard
streamlit run monitoring/dashboard/dashboard.py --server.port 8502
```

**Docker Compose:**
```bash
docker-compose up -d
```

### Access Points

- API Documentation: http://localhost:8000/docs
- Frontend Interface: http://localhost:8501  
- Monitoring Dashboard: http://localhost:8502
- Health Check: http://localhost:8000/health

## Usage

### Upload Documents

Upload documents through the web interface at http://localhost:8501 or via API:

```python
import requests

files = {'file': open('document.pdf', 'rb')}
response = requests.post(
    'http://localhost:8000/documents/upload',
    files=files,
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

### Query Documents

```python
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

## API Endpoints

### Authentication
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

### System Health
- `GET /health` - System health check

## Deployment

### Docker Deployment

```bash
# Basic deployment
docker-compose up -d

# With monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./enterprise_rag.db` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `LOG_LEVEL` | Logging level | `INFO` |

## Project Structure

```
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API application
│   ├── evaluation.py          # Evaluation & monitoring services
│   ├── models.py              # Database models
│   ├── auth.py                # Authentication logic
│   └── rag.py                 # RAG implementation
├── frontend/                   # Streamlit frontend
│   └── app.py                 # Main frontend application
├── monitoring/                 # Monitoring & dashboard
│   └── dashboard/
│       └── dashboard.py       # Real-time monitoring dashboard
├── docker-compose.yml          # Docker compose configuration
└── requirements.txt            # Dependencies
```

## Testing

```bash
# Run backend tests
cd backend
pytest test_evaluation_system.py -v

# Run integration tests
pytest test_backend.py -v
```

## Troubleshooting

### Common Issues

**OpenAI API Errors:**
- Verify your API key is set correctly
- Check API key validity at https://platform.openai.com/api-keys

**Database Connection Issues:**
```bash
cd backend && python init_db.py
```

**Docker Issues:**
```bash
docker-compose down && docker-compose up --build
```

## License

This project is licensed under the MIT License.
