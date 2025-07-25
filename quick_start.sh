#!/bin/bash

# Quick Start Script for OCR Document Scanner
# This script provides a simple way to get the application running quickly

echo "🚀 OCR Document Scanner - Quick Start"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if the backend directory exists
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found. Please run this script from the project root."
    exit 1
fi

# Make the setup script executable
chmod +x setup_environment.py

# Run the environment setup
echo "🔧 Setting up environment..."
python3 setup_environment.py

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "🎯 Quick Commands:"
    echo "1. Start development server:"
    echo "   source backend/venv/bin/activate && python backend/run.py"
    echo ""
    echo "2. Start with Docker:"
    echo "   docker-compose up -d"
    echo ""
    echo "3. View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "4. Stop services:"
    echo "   docker-compose down"
    echo ""
    echo "📝 For detailed documentation, see README.md"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi