#!/bin/bash

# Guitar Coach AI - Streamlit App Runner
# Activates the virtual environment and starts the Streamlit app

echo "🎸 Starting Guitar Coach AI..."
echo ""

# Define the correct project directory
PROJECT_DIR="/Users/miked/CY_AI_Music_Coach"

# Check current working directory
CURRENT_DIR=$(pwd)
echo "📍 Current directory: $CURRENT_DIR"
echo "✅ Expected directory: $PROJECT_DIR"
echo ""

# If not in the correct directory, change to it
if [ "$CURRENT_DIR" != "$PROJECT_DIR" ]; then
    echo "🔄 Changing to project directory..."
    cd "$PROJECT_DIR" || {
        echo "❌ Error: Could not change to $PROJECT_DIR"
        exit 1
    }
    echo "✅ Now in: $(pwd)"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment (.venv) not found!"
    echo "Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit
fi

# Run Streamlit
echo "✅ Launching Streamlit app..."
echo "🌐 Opening at http://localhost:8501"
echo ""
streamlit run streamlit_app.py
