#!/usr/bin/env python3
"""
Reversi Deluxe - Main Entry Point

A polished, feature-rich implementation of the classic Reversi/Othello
board game.

Usage:
    python3 main.py [board_size]
    python3 main.py 8       # Standard 8x8 board
    python3 main.py 10      # 10x10 board

For more information, see docs/README.md
"""
import sys
import subprocess
import importlib.util


def check_and_install_dependencies():
    """Check for required dependencies and install if missing."""
    required_packages = {"pygame": "pygame>=2.0.0"}

    missing_packages = []

    for package, pip_name in required_packages.items():
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(pip_name)

    if missing_packages:
        print("⚠️  Missing required packages:", ", ".join(missing_packages))
        print("📦 Installing missing packages...")

        try:
            # Try to install in user mode first
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--user", *missing_packages]
            )
            print("✅ Packages installed successfully!")
            print("🔄 Please restart the game.")
            sys.exit(0)
        except subprocess.CalledProcessError:
            print("\n❌ Failed to install packages automatically.")
            print("\nPlease install manually:")
            print(f"  pip install {' '.join(missing_packages)}")
            print("\nOr use the setup script:")
            print("  ./setup.sh")
            sys.exit(1)


if __name__ == "__main__":
    # Check dependencies before importing the game
    check_and_install_dependencies()

    # Import and run the game
    from src.Reversi import main

    main()
