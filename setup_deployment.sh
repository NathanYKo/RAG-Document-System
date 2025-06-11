#!/bin/bash

# Enterprise RAG System - Deployment Setup Script
# This script helps set up the deployment environment

set -e

echo "🚀 Enterprise RAG System - Deployment Setup"
echo "============================================"

# Check if required tools are installed
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file and add your OpenAI API key!"
else
    echo "✅ .env file already exists"
fi

# Check if OpenAI API key is set
if [ -f .env ]; then
    source .env
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        echo "⚠️  OpenAI API key not configured in .env file"
        echo "    Please edit .env and set OPENAI_API_KEY=sk-your-actual-key"
    else
        echo "✅ OpenAI API key configured"
    fi
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/db
mkdir -p logs

echo "🔧 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and set your OpenAI API key"
echo "2. Run: docker-compose up --build"
echo "3. Access the application:"
echo "   - Frontend: http://localhost:8501"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "For AWS deployment, see DEPLOYMENT.md" 