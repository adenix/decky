#!/bin/bash

# Standalone runner for Decky that uses the virtual environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/.venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found. Creating it now..."
    python3 -m venv "$VENV_PATH"

    echo "Installing dependencies..."
    "$VENV_PATH/bin/pip" install --upgrade pip
    "$VENV_PATH/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Run Decky with the virtual environment
exec "$VENV_PATH/bin/python" "$SCRIPT_DIR/src/decky.py" "$@"
