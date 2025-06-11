# Enterprise RAG System - Deployment Guide

## Project Structure

```
/
├── backend/                    # FastAPI backend service
│   ├── main.py                # Main FastAPI application
│   ├── auth.py                # Authentication and JWT handling
│   ├── crud.py                # Database operations
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── services.py            # Business logic services
│   ├── document_processor.py  # Document processing pipeline
│   ├── rag.py                 # RAG system implementation
│   ├── vector_database.py     # Vector database operations
│   ├── embeddings.py          # Text embedding functions
│   ├── sql_database.py        # SQL database configuration
│   ├── utils.py               # Utility functions
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend container configuration
├── frontend/                  # Streamlit frontend service
│   ├── app.py                 # Main Streamlit application
│   ├── config.py              # Frontend configuration
│   ├── utils.py               # Frontend utility functions
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Frontend container configuration
├── docker-compose.yml         # Local development setup
├── ecs-task-definition.json   # AWS ECS task definition
├── .github/workflows/ci-cd.yml # GitHub Actions CI/CD pipeline
├── env.example               # Environment variables template
└── DEPLOYMENT.md             # This file
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- OpenAI API key

### Local Development

1. Clone the repository
2. Copy the environment file:
   ```bash
   cp env.example .env
   ```

3. Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

4. Start all services:
   ```bash
   docker-compose up --build
   ```

5. Access the application:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (without Docker)

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=sk-your-openai-api-key-here
export JWT_SECRET_KEY=your-secret-key
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend
pip install -r requirements.txt
export API_URL=http://localhost:8000
streamlit run app.py --server.port 8501
```

## AWS Deployment

### Prerequisites

- AWS CLI configured
- Docker installed
- GitHub repository with Actions enabled

### Setup Steps

1. **Create AWS Resources:**
   - ECS Cluster: `rag-system-cluster`
   - ECR Repositories: `rag-system-backend`, `rag-system-frontend`
   - ECS Service: `rag-system-service`
   - Application Load Balancer (optional)

2. **Configure Secrets Manager:**
   ```bash
   aws secretsmanager create-secret \
     --name "rag-system/openai-api-key" \
     --secret-string "sk-your-openai-api-key-here"
   
   aws secretsmanager create-secret \
     --name "rag-system/jwt-secret-key" \
     --secret-string "your-super-secret-jwt-key"
   
   aws secretsmanager create-secret \
     --name "rag-system/database-url" \
     --secret-string "postgresql://user:pass@host:5432/dbname"
   ```

3. **Update ECS Task Definition:**
   - Replace `ACCOUNT_ID` with your AWS account ID
   - Replace `BACKEND_IMAGE_URI` and `FRONTEND_IMAGE_URI` with your ECR URIs

4. **Configure GitHub Secrets:**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

5. **Deploy:**
   Push to the `main` branch to trigger automatic deployment.

## Environment Variables

### Backend

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `JWT_SECRET_KEY` | JWT signing key | Yes | - |
| `DATABASE_URL` | Database connection URL | No | SQLite |
| `ALLOWED_HOSTS` | Allowed hostnames | No | localhost,127.0.0.1,0.0.0.0 |
| `ALLOWED_ORIGINS` | CORS allowed origins | No | http://localhost:* |

### Frontend

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_URL` | Backend API URL | Yes | http://localhost:8000 |
| `STREAMLIT_SERVER_HEADLESS` | Run in headless mode | No | true |
| `STREAMLIT_SERVER_ENABLE_CORS` | Enable CORS | No | false |

## Health Checks

Both services include health check endpoints:

- Backend: `GET /health`
- Frontend: `GET /_stcore/health`

## Monitoring

### Logs

- Backend logs: `/ecs/rag-system/backend` (CloudWatch)
- Frontend logs: `/ecs/rag-system/frontend` (CloudWatch)

### Metrics

Health checks run every 30 seconds with:
- 3 retries before marking unhealthy
- 60-second startup grace period

## Troubleshooting

### Common Issues

1. **Container startup failures:**
   - Check CloudWatch logs
   - Verify environment variables
   - Ensure secrets are properly configured

2. **Database connection issues:**
   - Verify DATABASE_URL format
   - Check network connectivity
   - Ensure database credentials are correct

3. **Frontend can't reach backend:**
   - Verify API_URL is correct
   - Check network configuration
   - Ensure backend is healthy

### Debug Commands

```bash
# Check container logs
docker-compose logs backend
docker-compose logs frontend

# Test backend health
curl http://localhost:8000/health

# Test frontend health  
curl http://localhost:8501/_stcore/health
```

## Security Considerations

1. **Change default secrets** in production
2. **Use strong JWT secret keys**
3. **Configure proper CORS origins**
4. **Use HTTPS in production**
5. **Regularly rotate API keys**
6. **Monitor access logs**

## Scaling

The system supports horizontal scaling:

- **Backend:** Scale ECS tasks based on CPU/memory
- **Frontend:** Scale ECS tasks based on user load
- **Database:** Use RDS with read replicas for high availability

## Backup and Recovery

1. **Database backups:** Configure automated RDS backups
2. **Vector database:** Regular ChromaDB persistence
3. **Configuration:** Store deployment configs in version control 