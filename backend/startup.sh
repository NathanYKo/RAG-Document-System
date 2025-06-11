#!/bin/bash

set -e

echo "🚀 Starting Enterprise RAG Backend..."

# Create database directory if it doesn't exist
mkdir -p /app/db

# Initialize SQLite database if it doesn't exist
if [ ! -f /app/enterprise_rag.db ]; then
    echo "📊 Initializing database..."
    touch /app/enterprise_rag.db
    chmod 664 /app/enterprise_rag.db
fi

# Initialize Alembic if needed
if [ ! -d "/app/alembic" ]; then
    echo "🔧 Initializing Alembic..."
    alembic init alembic
fi

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head || echo "⚠️  Migration failed, continuing..."

# Download models on first startup (with proper permissions)
echo "📥 Ensuring models are downloaded..."
python -c "
import os
os.environ.setdefault('TRANSFORMERS_CACHE', '/app/.cache/huggingface')
os.environ.setdefault('HF_HOME', '/app/.cache/huggingface')
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✅ Models downloaded successfully')
" || echo "⚠️  Model download failed, will retry at runtime..."

echo "🎯 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --access-log 