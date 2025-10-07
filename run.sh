#!/bin/bash

# FAR Bot Startup Script
echo "🤖 Starting FAR Bot..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python -m venv venv"
    echo "   Then: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Creating default .env file..."
    python setup_env.py
    echo "   Please edit .env file and add your OpenAI API key"
    echo "   Then run this script again"
    exit 1
fi

# Start the application
echo "🚀 Starting FAR Bot Application..."
python start.py
