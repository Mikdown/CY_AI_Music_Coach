#!/bin/bash

# Quick Start Script for Guitar Coach AI
# This script starts both the backend and frontend servers

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🎸 Guitar Coach AI - Quick Start"
echo "=================================="
echo ""

# Check for .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create $PROJECT_ROOT/.env with:"
    echo "  GITHUB_TOKEN=your_token_here"
    echo "  TAVILY_API_KEY=your_key_here (optional)"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo ""

# Install/update backend dependencies
echo "📦 Installing backend dependencies..."
pip install -q -r "$PROJECT_ROOT/api/requirements.txt" || {
    echo "❌ Failed to install backend dependencies"
    exit 1
}
echo "✅ Backend dependencies installed"
echo ""

# Install/update frontend dependencies
echo "📦 Installing frontend dependencies..."
cd "$PROJECT_ROOT/frontend"
npm install --quiet || {
    echo "❌ Failed to install frontend dependencies"
    exit 1
}
echo "✅ Frontend dependencies installed"
echo ""

echo "🚀 Starting servers..."
echo ""
echo "Backend will run on:  http://localhost:8000"
echo "Frontend will run on: http://localhost:5173"
echo ""
echo "Press CTRL+C to stop all servers"
echo ""

# Start backend in background
cd "$PROJECT_ROOT"
python3 -m uvicorn api.main:app --reload &
BACKEND_PID=$!

# Give backend time to start
sleep 2

# Start frontend
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
