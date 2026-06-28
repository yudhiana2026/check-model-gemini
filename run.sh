#!/usr/bin/env bash

set -euo pipefail

VENV_DIR=".venv"
SCRIPT="check_model.py"

# Ensure virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment '$VENV_DIR' not found."
    echo "Run ./setup.sh first."
    exit 1
fi

# Ensure Python script exists
if [ ! -f "$SCRIPT" ]; then
    echo "Error: '$SCRIPT' not found."
    exit 1
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Run the script
python "$SCRIPT"