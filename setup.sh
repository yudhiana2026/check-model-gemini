#!/usr/bin/env bash

set -euo pipefail

VENV_DIR=".venv"

echo "=================================="
echo " Python Virtual Environment Setup "
echo "=================================="

# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

echo
echo "=================================="
echo "Setup completed successfully!"
echo
echo "To activate the environment later, run:"
echo "source .venv/bin/activate"
echo "=================================="