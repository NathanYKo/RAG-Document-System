# Project Structure & Setup Implementation

**Generated:** 2025-06-07T21:04:59.180337

Here is the complete project structure and setup for the RAG system based on all the implemented components:

1. Project Directory Structure:

```
rag-system/
│
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── rag.py
│   │   ├── evaluation.py
│   │   └── monitoring.py
│   ├── tests/
│   │   ├── test_main.py
│   │   ├── test_auth.py
│   │   ├── test_rag.py
│   │   └── test_evaluation.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app.py
│   ├── utils.py  
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── task-definition.json
├── .github/
│   └── workflows/
│       └── ci-cd.yml
│
├── README.md
├── .env.example
└── setup.sh
```

2. requirements.txt:

backend/requirements.txt:
```
fastapi[all]==0.95.1
SQLAlchemy==2.0.12
alembic==1.10.4
psycopg2-binary==2.9.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
chromadb==0.3.1
sentence-transformers==2.2.2
openai==0.27.2
prometheus-fastapi-instrumentator==0.11.0
```

frontend/requirements.txt:
```
streamlit==1.21.0
requests==2.28.2
requests-toolbelt==0.10.1
altair==4.2.2
pandas==1.5.3
```

3. README.md:

```markdown
# RAG System

A Retrieval-Augmented Generation (RAG) system with document processing, vector database, user management, feedback collection, A/B testing, monitoring, and analytics dashboard.

## Features

- Document processing pipeline to extract and chunk text from PDF, DOCX, TXT files
- Vector database (ChromaDB) for efficient semantic search
- FastAPI backend with user authentication and authorization
- Streamlit frontend for document upload, querying, and feedback submission
- Response quality evaluation using GPT-4
- A/B testing framework for comparing RAG implementations
- Prometheus metrics for monitoring system performance
- Analytics dashboard for visualizing key metrics and user feedback

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rag-system.git
   cd rag-system
   ```

2. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env and set the required variables
   ```

3. Run the setup script:
   ```
   ./setup.sh
   ```

4. Start the system:
   ```
   docker-compose up
   ```

5. Access the frontend at `http://localhost:8501` and the backend API at `http://localhost:8000`.

## Testing

Run integration tests:
```
./integration_tests.sh
```

## Deployment

Follow the deployment checklist in `DEPLOYMENT.md` for production deployment on AWS ECS.

```

4. .env.example:

```
# Backend
DATABASE_URL=postgresql://username:password@localhost:5432/rag_system
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret_key

# Frontend 
API_URL=http://localhost:8000

# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

5. setup.sh:

```bash
#!/bin/bash

# Create Python virtual environments
python -m venv backend/venv
python -m venv frontend/venv

# Install backend dependencies
source backend/venv/bin/activate
pip install -r backend/requirements.txt
deactivate

# Install frontend dependencies  
source frontend/venv/bin/activate
pip install -r frontend/requirements.txt
deactivate

# Set up database
docker-compose up -d db
sleep 10
source backend/venv/bin/activate
alembic upgrade head
deactivate

# Build Docker images
docker-compose build

echo "Setup complete. Run 'docker-compose up' to start the system."
```

6. integration_tests.sh:

```bash
#!/bin/bash

# Start the system
docker-compose up -d

# Run backend tests
docker-compose exec backend pytest tests/

# Run frontend tests
docker-compose exec frontend pytest tests/

# Test document processing
curl -X POST -F "file=@path/to/test/document.pdf" http://localhost:8000/upload

# Test querying  
response=$(curl -X POST -H "Content-Type: application/json" -d '{"query":"test query"}' http://localhost:8000/query)
echo $response

# Test A/B testing
response_a=$(curl -X POST -H "Content-Type: application/json" -d '{"query":"test query"}' http://localhost:8000/query)
response_b=$(curl -X POST -H "Content-Type: application/json" -H "version: B" -d '{"query":"test query"}' http://localhost:8000/query)
echo "A: $response_a"
echo "B: $response_b"  

# Test evaluation
evaluation=$(curl -X POST -H "Content-Type: application/json" -d '{"query":"test query", "response":"test response"}' http://localhost:8000/evaluate)
echo $evaluation

# Test monitoring
metrics=$(curl http://localhost:8000/metrics)
echo $metrics  

docker-compose down
```

7. DEPLOYMENT.md:

```markdown
# Deployment Checklist

1. Set up AWS resources:
   - [ ] Create ECS cluster and Fargate task definition
   - [ ] Create ECS service for the task definition
   - [ ] Set up ECR repository for Docker images  
   - [ ] Create secrets in AWS Secrets Manager
   - [ ] Create IAM roles and policies for ECS task execution

2. Configure GitHub Actions:
   - [ ] Set up GitHub repository secrets for AWS access
   - [ ] Configure CI/CD workflow in `.github/workflows/ci-cd.yml`
   - [ ] Update `ECR_REPOSITORY` and `AWS_REGION` variables if needed

3. Set up monitoring and logging:  
   - [ ] Create CloudWatch log groups for ECS task logs
   - [ ] Configure Prometheus to scrape metrics from backend and frontend
   - [ ] Set up CloudWatch alarms for key metrics

4. Configure scaling:
   - [ ] Configure auto scaling for ECS service based on CPU/memory utilization or custom metrics
   - [ ] Set up Application Load Balancer to distribute traffic 

5. Deploy:
   - [ ] Push changes to `main` branch to trigger CI/CD pipeline
   - [ ] Monitor deployment progress in GitHub Actions
   - [ ] Verify successful deployment in AWS ECS console

6. Post-deployment:
   - [ ] Run integration tests against production environment
   - [ ] Verify frontend and backend are accessible 
   - [ ] Check monitoring dashboards and logs for any issues
   - [ ] Conduct final manual testing
```

This project structure organizes the backend and frontend code into separate directories, each with their own dependencies and Dockerfiles. The `docker-compose.yml` file defines the multi-container setup for local development and testing.

The `README.md` provides a comprehensive getting-started guide with setup instructions. The `.env.example` file lists all the required environment variables.

The `setup.sh` script automates the setup process by creating virtual environments, installing dependencies, setting up the database, and building Docker images.

The `integration_tests.sh` script demonstrates how to run integration tests that exercise various components of the system.

Finally, the `DEPLOYMENT.md` checklist outlines the steps for deploying the system to production using AWS ECS and GitHub Actions for CI/CD.

Let me know if you have any further questions! This project structure and setup should provide a solid foundation for the RAG system.