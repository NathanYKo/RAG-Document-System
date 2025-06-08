# Deployment & DevOps Implementation

**Generated:** 2025-06-07T21:02:16.913305

Here is a complete deployment setup for the RAG system using Docker, GitHub Actions, and AWS ECS:

1. Code Files:

Dockerfile:
```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
```

docker-compose.yml:
```yaml
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "8000:80"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
      
  frontend:
    build: ./frontend  
    ports:
      - "8501:8501"
    environment:  
      - API_URL=http://backend
    depends_on:
      - backend
      
  db:
    image: postgres:13
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}  
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      
volumes:
  db_data:
```

.github/workflows/ci-cd.yml:
```yaml
name: CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  AWS_REGION: us-east-1 
  ECR_REPOSITORY: rag-system

jobs:

  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
        
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker-compose build
        docker-compose push
        
    - name: Fill in the new image ID in the Amazon ECS task definition
      id: task-def
      uses: aws-actions/amazon-ecs-render-task-definition@v1
      with:
        task-definition: task-definition.json
        container-name: backend
        image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}

    - name: Deploy Amazon ECS task definition
      uses: aws-actions/amazon-ecs-deploy-task-definition@v1
      with:
        task-definition: ${{ steps.task-def.outputs.task-definition }}
        service: rag-system-service
        cluster: rag-system-cluster
```

ecs-task-definition.json:
```json
{
  "family": "rag-system-task",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<IMAGE1_NAME>",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 80,
          "hostPort": 80
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:database_url"
        },
        {
          "name": "OPENAI_API_KEY",  
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:openai_api_key"
        },
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:jwt_secret_key"  
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }  
      }
    },
    {
      "name": "frontend", 
      "image": "<IMAGE2_NAME>",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "hostPort": 8501
        }
      ],
      "environment": [
        {
          "name": "API_URL",
          "value": "http://backend" 
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/frontend",
          "awslogs-region": "us-east-1", 
          "awslogs-stream-prefix": "ecs"
        }
      }  
    }
  ],
  "requiresCompatibilities": [
    "FARGATE"  
  ],
  "networkMode": "awsvpc",
  "cpu": "1024",
  "memory": "2048",
  "tags": [
    {
      "key": "Project",
      "value": "RAG System"
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