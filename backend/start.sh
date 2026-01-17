#!/bin/bash
# start.sh - Start the FastAPI backend server

echo "🚀 Starting LahStats Backend API..."
echo "=================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your Supabase credentials"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Run the server
echo "🌐 Starting server on http://0.0.0.0:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo "=================================="
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
