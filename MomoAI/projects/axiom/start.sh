#!/bin/bash

# Axiom PWA Startup Script (Unix/Linux/macOS)
# Simple script to start the Axiom PWA server

set -e

echo "⚡ Axiom PWA - Coherent AI Collaboration Platform"
echo "=================================================="

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ required, found $PYTHON_VERSION"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ ANTHROPIC_API_KEY not set"
        echo "   Please set your Anthropic API key:"
        echo "   export ANTHROPIC_API_KEY=your_key_here"
        echo "   or create a .env file with ANTHROPIC_API_KEY=your_key_here"
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .

# Start the server
echo ""
echo "🚀 Starting Axiom PWA server..."
echo "🌐 Server will be available at:"
echo "   http://localhost:8000"
echo "   http://127.0.0.1:8000"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo "=================================================="

cd axiom/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload