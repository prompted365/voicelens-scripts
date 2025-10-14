#!/bin/bash

# VoiceLens Deployment Script
# Ensures consistent virtual environment activation and deployment

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "🚀 VoiceLens Deployment Script"
echo "================================"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at: $VENV_DIR"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Verify activation
if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Check if requirements.txt exists and install dependencies
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "📦 Installing/updating dependencies..."
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, skipping dependency installation"
fi

# Run the application
echo "🏃 Starting VoiceLens application..."
cd "$SCRIPT_DIR"

# Check if we should run on a different port (to avoid port 5000 conflicts)
PORT=${PORT:-8080}
echo "🌐 Running on port: $PORT"

# Export environment variables
if [ -f "deploy_local_prod.py" ]; then
    export FLASK_APP=deploy_local_prod.py
elif [ -f "voicelens_ops_app.py" ]; then
    export FLASK_APP=voicelens_ops_app.py
else
    export FLASK_APP=app.py
fi
export FLASK_ENV=production
export PORT=$PORT

# Run the Flask application
if [ -f "deploy_local_prod.py" ]; then
    echo "🚀 Running via deployment script..."
    python deploy_local_prod.py
elif [ -f "voicelens_ops_app.py" ]; then
    echo "🚀 Running VoiceLens ops application directly..."
    python voicelens_ops_app.py
elif [ -f "app.py" ]; then
    echo "🚀 Running app.py..."
    python app.py
elif [ -f "main.py" ]; then
    echo "🚀 Running main.py..."
    python main.py
else
    echo "❌ No recognized application entry point found."
    echo "Available options: deploy_local_prod.py, voicelens_ops_app.py, app.py, main.py"
    exit 1
fi
