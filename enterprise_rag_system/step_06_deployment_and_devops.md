# Deployment & DevOps Implementation

**Generated:** 2025-06-07T21:02:16.913305

Here is a complete deployment setup for the RAG system using Docker, GitHub Actions, and AWS ECS:

**Project Structure:**
```
/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── crud.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py
│   ├── config.py
│   ├── utils.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── ecs-task-definition.json
├── .github/workflows/ci-cd.yml
└── env.example
```

1. Code Files:

backend/Dockerfile:
```dockerfile
FROM python:3.9

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Create necessary directories
RUN mkdir -p db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

frontend/Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all frontend code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

docker-compose.yml:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./enterprise_rag.db}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-secret-key-change-in-production}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost,127.0.0.1,0.0.0.0,backend}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:8000,http://localhost:8501}
    volumes:
      - ./backend/db:/app/db
      - ./backend/enterprise_rag.db:/app/enterprise_rag.db
    depends_on:
      - db
    networks:
      - rag-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://backend:8000
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ENABLE_CORS=false
    depends_on:
      - backend
    networks:
      - rag-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-enterprise_rag}
      - POSTGRES_USER=${POSTGRES_USER:-rag_user}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-rag_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rag-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-rag_user}"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  postgres_data:

networks:
  rag-network:
    driver: bridge
```

.github/workflows/ci-cd.yml:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY_BACKEND: rag-system-backend
  ECR_REPOSITORY_FRONTEND: rag-system-frontend

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run backend tests
      run: |
        cd backend
        python -m pytest ../test_*.py -v

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
    
    - name: Build, tag, and push backend image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        cd backend
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest
    
    - name: Build, tag, and push frontend image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        cd frontend
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest
    
    - name: Update ECS task definition for backend
      id: backend-task-def
      uses: aws-actions/amazon-ecs-render-task-definition@v1
      with:
        task-definition: ecs-task-definition.json
        container-name: backend
        image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY_BACKEND }}:${{ github.sha }}
    
    - name: Update ECS task definition for frontend
      id: frontend-task-def
      uses: aws-actions/amazon-ecs-render-task-definition@v1
      with:
        task-definition: ${{ steps.backend-task-def.outputs.task-definition }}
        container-name: frontend
        image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY_FRONTEND }}:${{ github.sha }}
    
    - name: Deploy to Amazon ECS
      uses: aws-actions/amazon-ecs-deploy-task-definition@v1
      with:
        task-definition: ${{ steps.frontend-task-def.outputs.task-definition }}
        service: rag-system-service
        cluster: rag-system-cluster
        wait-for-service-stability: true
```

ecs-task-definition.json:
```json
{
  "family": "rag-system-task",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "BACKEND_IMAGE_URI",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:rag-system/database-url"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:rag-system/openai-api-key"
        },
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:rag-system/jwt-secret-key"
        }
      ],
      "environment": [
        {
          "name": "ALLOWED_HOSTS",
          "value": "localhost,127.0.0.1,0.0.0.0,backend"
        },
        {
          "name": "ALLOWED_ORIGINS", 
          "value": "http://localhost:3000,http://localhost:8000,http://localhost:8501"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/rag-system/backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    },
    {
      "name": "frontend",
      "image": "FRONTEND_IMAGE_URI",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_URL",
          "value": "http://localhost:8000"
        },
        {
          "name": "STREAMLIT_SERVER_HEADLESS",
          "value": "true"
        },
        {
          "name": "STREAMLIT_SERVER_ENABLE_CORS",
          "value": "false"
        }
      ],
      "dependsOn": [
        {
          "containerName": "backend",
          "condition": "HEALTHY"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/rag-system/frontend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "1024",
  "memory": "2048",
  "tags": [
    {
      "key": "Project",
      "value": "Enterprise RAG System"
    },
    {
      "key": "Environment",  
      "value": "production"
    }
  ]
}
```

2. Setup Instructions:

1. Set up AWS resources:
   - Create an ECS cluster and Fargate task definition using the provided `ecs-task-definition.json` file. 
   - Create an ECS service for the task definition.
   - Set up an ECR repository for the Docker images.
   - Create secrets in AWS Secrets Manager for sensitive configurations (`DATABASE_URL`, `OPENAI_API_KEY`, `JWT_SECRET_KEY`).
   - Create IAM roles and policies for ECS task execution.

2. Set up GitHub repository:
   - Push your code to a GitHub repository.
   - Configure repository secrets for AWS access (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

3. Configure GitHub Actions:
   - Set up the provided GitHub Actions workflow in `.github/workflows/ci-cd.yml`.
   - Update the `ECR_REPOSITORY` and `AWS_REGION` variables if needed.

4. Configure monitoring and logging:
   - Set up CloudWatch log groups for ECS task logs (`/ecs/backend`, `/ecs/frontend`).
   - Configure Prometheus to scrape metrics from the backend and frontend services.
   - Set up CloudWatch alarms for key metrics.

5. Configure scaling:
   - Configure auto scaling for the ECS service based on CPU/memory utilization or custom metrics.
   - Use Application Load Balancer to distribute traffic across multiple task instances.

6. Run the pipeline:
   - Push changes to the `main` branch to trigger the CI/CD pipeline.
   - The pipeline will build and push the Docker images to ECR, update the ECS task definition, and deploy the updated services.

3. Dependencies:

- Docker
- Docker Compose
- AWS CLI
- GitHub Actions

4. Configuration Files:

- `Dockerfile`: Defines the Docker image for the backend service.
- `docker-compose.yml`: Defines the multi-container setup for local development and testing.
- `.github/workflows/ci-cd.yml`: Defines the GitHub Actions CI/CD workflow.
- `ecs-task-definition.json`: Defines the ECS task definition for deployment.

5. Testing:

- Include unit tests for individual components.
- Run integration tests against a staging environment before deploying to production.

6. Integration with Previous Components:

- Update the `Dockerfile` and `docker-compose.yml` files to include the frontend and backend services from previous steps.
- Configure the frontend to use the backend API URL using environment variables.
- Update the backend to read sensitive configurations from AWS Secrets Manager.
- Integrate monitoring and logging for both frontend and backend services.

This setup provides a complete deployment solution using Docker, GitHub Actions, and AWS ECS. The CI/CD pipeline automatically builds and deploys the system whenever changes are pushed to the main branch.

Let me know if you have any further questions! Follow the setup instructions to configure your AWS resources, set up the GitHub repository and Actions workflow, and run the pipeline to deploy your RAG system.