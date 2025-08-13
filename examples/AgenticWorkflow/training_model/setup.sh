#!/bin/bash

# Gemma 7B Fine-tuning Setup Script
echo "Gemma 2B Fine-tuning Setup"
echo "============================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed."
    exit 1
fi

echo "pip3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install --upgrade pip

# Install PyTorch first (for better compatibility)
echo "Installing PyTorch..."
pip install torch

# Install other requirements
echo "Installing other dependencies..."
pip install -r requirements_training.txt

echo ""
echo "Setup complete!"

