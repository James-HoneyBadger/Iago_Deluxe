#!/bin/bash

# Reversi Deluxe Setup Script
# This script sets up the Reversi game and its dependencies

echo "🎮 Setting up Reversi Deluxe..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7 or higher and try again."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version found, but Python $required_version or higher is required."
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "You may need to install python3-venv package"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies in virtual environment..."
if .venv/bin/pip install -r requirements.txt; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "Trying with --user flag..."
    if pip3 install --user -r requirements.txt; then
        echo "✅ Dependencies installed in user directory"
    else
        echo "❌ Installation failed. Please install pygame manually."
        exit 1
    fi
fi

# Check if pygame was installed correctly
if .venv/bin/python3 -c "import pygame" 2>/dev/null || python3 -c "import pygame" 2>/dev/null; then
    echo "✅ Pygame installed and working"
else
    echo "❌ Pygame installation failed"
    exit 1
fi

# Make the main script executable
chmod +x main.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To play Reversi Deluxe:"
echo "  .venv/bin/python3 main.py    # Using virtual environment (recommended)"
echo "  python3 main.py              # Using system Python"
echo ""
echo "Or create a launcher script:"
echo "  echo '#!/bin/bash' > play.sh"
echo "  echo 'cd \$(dirname \$0) && .venv/bin/python3 main.py \"\$@\"' >> play.sh"
echo "  chmod +x play.sh"
echo "  ./play.sh"
echo ""
echo "Controls:"
echo "  V - Toggle move analysis"
echo "  H - Toggle hints"
echo "  A - Toggle AI"
echo "  N - New game"
echo "  Q - Quit"
echo ""
echo "Enjoy the game! 🎮"
