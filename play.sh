#!/bin/bash
# Reversi Deluxe Launcher
# Automatically uses virtual environment if available

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use virtual environment Python if available, otherwise system Python
if [ -f ".venv/bin/python3" ]; then
    .venv/bin/python3 main.py "$@"
else
    python3 main.py "$@"
fi
