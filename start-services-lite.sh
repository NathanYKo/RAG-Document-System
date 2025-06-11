#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Lightweight Enterprise RAG System on Render..."

# Set memory optimization environment variables
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1

# Initialize database if needed
echo "📊 Initializing database..."
cd /app/backend
python init_db.py

# Start backend API with memory optimizations
echo "🔧 Starting Backend API (Memory Optimized)..."
cd /app/backend

# Use single worker and limit memory
uvicorn main:app \
  --host 0.0.0.0 \
  --port ${PORT:-10000} \
  --workers 1 \
  --loop uvloop \
  --no-access-log \
  --timeout-keep-alive 30 &

BACKEND_PID=$!

# Wait for backend with shorter timeout
echo "⏳ Waiting for backend..."
for i in {1..15}; do
  if curl -f http://localhost:${PORT:-10000}/health 2>/dev/null; then
    echo "✅ Backend ready!"
    break
  fi
  echo "Wait $i/15..."
  sleep 3
done

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
  echo "❌ Backend failed to start"
  exit 1
fi

echo "🎉 Lightweight RAG System started successfully!"
echo "🌐 API available on port ${PORT:-10000}"

# Keep backend running (don't start Streamlit to save memory)
wait $BACKEND_PID 