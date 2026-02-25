#!/bin/bash
# Iago Deluxe Launcher
# Automatically sets up virtual environment and installs dependencies if needed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -f ".venv/bin/python3" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        echo "Install python3-venv: sudo apt install python3-venv"
        exit 1
    fi
fi

# Install/upgrade dependencies if requirements.txt has changed or packages are missing
if [ ! -f ".venv/.deps_installed" ] || [ requirements.txt -nt ".venv/.deps_installed" ]; then
    echo "Installing dependencies..."
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies."
        exit 1
    fi
    touch .venv/.deps_installed
    echo "Dependencies ready."
fi

# Launch the game
exec .venv/bin/python3 main.py "$@"
