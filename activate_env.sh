#!/bin/bash

# Simple VoiceLens Environment Activation Script
# Source this script to activate the virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at: $VENV_DIR"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Activate and install dependencies
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip install -r "$SCRIPT_DIR/requirements.txt"
        echo "✅ Dependencies installed"
    fi
else
    echo "🔄 Activating existing virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo "🐍 Python: $(which python)"
echo "📦 Pip: $(which pip)"

# Set useful environment variables
if [ -f "deploy_local_prod.py" ]; then
    export FLASK_APP=deploy_local_prod.py
elif [ -f "voicelens_ops_app.py" ]; then
    export FLASK_APP=voicelens_ops_app.py
else
    export FLASK_APP=app.py
fi
export FLASK_ENV=production
export PORT=8080

echo "🚀 Environment ready for VoiceLens deployment!"
