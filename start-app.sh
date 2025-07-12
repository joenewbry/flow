#!/bin/bash

echo "🚀 Screen Tracker Desktop App Launcher"
echo "======================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found."
    echo "Please create a .env file with your configuration:"
    echo "ANTHROPIC_API_KEY=your_api_key_here"
    echo "CHROMA_HOST=localhost"
    echo "CHROMA_PORT=8000"
    echo ""
    echo "You can continue without it, but some features may not work."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the desktop app
echo "🎯 Starting Screen Tracker Desktop App..."
npm start