#!/bin/bash

# Enhanced OCR Document Scanner - Local Development Server
# This script runs the application locally without Docker

echo "🚀 Enhanced OCR Document Scanner - Local Development Server"
echo "==========================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads logs models analytics_charts

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_APP=app.py
export TESSERACT_CMD=/usr/local/bin/tesseract
export PYTHONPATH=$(pwd)
export PYTHONUNBUFFERED=1

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract is not installed. Please install it:"
    echo "   macOS: brew install tesseract"
    echo "   Ubuntu: sudo apt-get install tesseract-ocr"
    echo "   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
    echo "Continuing without Tesseract (some features may not work)..."
fi

# Start the application
echo "🚀 Starting Enhanced OCR Document Scanner..."
echo "Application will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
