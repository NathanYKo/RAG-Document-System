#!/bin/bash

# Exit on any error
set -e

echo "🚀 Starting Enterprise Document Intelligence System..."

# Initialize database if needed
echo "📊 Initializing database..."
cd /app/backend
python init_db.py

# Start backend API in background
echo "🔧 Starting Backend API..."
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -f http://localhost:${PORT:-8000}/health 2>/dev/null; then
    echo "✅ Backend is ready!"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 2
done

# Start frontend
echo "🎨 Starting Frontend..."
cd /app/frontend
export API_URL="http://localhost:${PORT:-8000}"
export STREAMLIT_SERVER_PORT=${STREAMLIT_PORT:-8501}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false

streamlit run app.py --server.port ${STREAMLIT_PORT:-8501} --server.address 0.0.0.0 &
FRONTEND_PID=$!

# Wait for any process to exit
wait -n

# Exit with error if any process failed
exit $? 