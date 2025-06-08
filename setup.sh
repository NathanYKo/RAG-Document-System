#!/bin/bash

echo "🚀 Setting up Document Processing Pipeline..."
echo "=" * 50

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To run the server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the server: uvicorn document_processor:app --reload"
echo "3. Visit: http://localhost:8000"
echo "4. API docs: http://localhost:8000/docs"
echo ""
echo "To run tests:"
echo "pytest test_document_processor.py -v" 