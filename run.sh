#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 could not be found. Please install Python 3.11 or higher."
    exit 1
fi

# Set environment variables to ignore warnings
export PYTHONWARNINGS="ignore::UserWarning:pydantic,ignore::DeprecationWarning:pydantic"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    # Check if venv creation was successful
    if [ ! -d "venv" ]; then
        echo "Failed to create virtual environment. Please check your Python installation."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -e .
fi

# Run the application
python run.py
