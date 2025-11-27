# Iago_Deluxe

A feature-rich, professionally-crafted implementation of the classic Reversi (Othello) board game with an intelligent AI opponent and comprehensive game analysis.

## ✨ Features

### 🎮 Gameplay
- **Classic Reversi/Othello** gameplay with authentic rules
- **6 AI Difficulty Levels** - From beginner-friendly to expert challenge
- **Configurable Board Sizes** - 4x4 to 16x16 (default 8x8)
- **Move Hints & Preview** - Visual indicators for legal moves and outcomes
- **Undo/Redo System** - Full move history with unlimited undo/redo
- **Interactive Tutorial** - Step-by-step guide for new players

### 🎨 Customization
- **5 Beautiful Themes** - Classic, Ocean, Sunset, Midnight, Forest
- **6 Piece Styles** - Traditional, Modern, Minimal, Glass, Neon, Emoji
- **Sound Effects** - Satisfying audio feedback (toggleable)
- **Responsive UI** - Clean, modern interface with hover effects

### 📊 Analysis & Statistics
- **Post-Game Analysis** - Detailed breakdown of game performance
- **Move-by-Move Analysis** - Real-time evaluation of move quality
- **Strategic Insights** - Board control, corner capture, edge play metrics
- **Performance Tracking** - Win/loss records per difficulty level

### 💾 Data Management
- **Game Save/Load** - Continue games anytime with PGN/JSON export
- **Settings Persistence** - Your preferences saved automatically
- **Game History** - Review past games with full move notation

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/James-HoneyBadger/Iago_Deluxe.git
   cd Iago_Deluxe
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   This creates a virtual environment and installs all dependencies automatically.

### Running the Game

**Recommended (using helper script):**
```bash
./play.sh
```

**Direct execution:**
```bash
.venv/bin/python3 main.py
```

**With system Python (if pygame installed globally):**
```bash
python3 main.py
```

## 🌐 Alternative Versions

### Web Browser Version
A simplified web-based version that runs directly in any modern browser:

**Location:** `web_version/index.html`  
**Features:** Basic Reversi gameplay, move hints, **three game modes** (Human vs Human, Human vs Computer, Computer vs Computer), **AI opponent** with difficulty levels  
**Requirements:** Any modern web browser (Chrome, Firefox, Safari, Edge)  
**Advantages:** No installation, works on mobile devices, cross-platform, includes AI gameplay  

```bash
# Run locally
cd web_version
python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

## 📁 Project Structure

```
Iago_Deluxe/
├── main.py                  # Entry point with dependency management
├── play.sh                  # Convenient launcher script
├── setup.sh                 # Installation and environment setup
├── requirements.txt         # Python dependencies
├── .flake8                  # Linting configuration
│
├── src/                     # Source code
│   ├── __init__.py
│   ├── Iago.py             # Main game implementation (5300+ lines)
│   ├── config.py           # Configuration constants and settings
│   ├── logger.py           # Logging system with file rotation
│   └── error_handling.py   # Custom exceptions and validation
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── run_tests.py        # Test runner
│   ├── test_board.py       # Board logic tests
│   ├── test_ai.py          # AI behavior tests
│   ├── test_settings.py    # Settings management tests
│   ├── test_ai_levels.py   # AI difficulty verification
│   └── verify_ai_levels.py # AI performance benchmarking
│
├── docs/                    # Documentation
│   ├── README.md           # Documentation index
│   ├── DEVELOPMENT.md      # Architecture and technical details
│   ├── QUICK_REFERENCE.md  # Command reference and shortcuts
│   ├── AI_LEVELS_VERIFICATION.md  # AI testing methodology
│   └── USER_GUIDE.md       # Comprehensive user manual
│
├── assets/                  # Game assets
│   └── reversi-icon.png    # Application icon
│
├── config/                  # Runtime configuration (auto-created)
│   └── iago-settings.json   # User preferences (auto-generated)
│
├── data/                    # Game data (auto-created)
│   └── iago_game_*.pgn, *.json  # Saved games (auto-generated)
│
├── web_version/             # Web browser version
│   └── index.html          # Complete web-based game
```

## 🎯 Game Controls

### Mouse Controls
- **Click** - Make a move on highlighted squares
- **Menu Navigation** - Click menu items or use hover effects

### Keyboard Shortcuts
- **ESC** - Toggle pause menu
- **U** - Undo move
- **R** - Redo move
- **H** - Toggle hints
- **S** - Save game
- **N** - New game

### Menu System
- **Game Menu** - New game, board size, save/load, quit
- **AI Menu** - Difficulty levels, AI color selection
- **Settings Menu** - Themes, sound, hints, move preview
- **View Menu** - Analysis window, statistics, tutorial

## 🛠️ Development

### Requirements
- **Python 3.7+** (tested on 3.13)
- **Pygame 2.0+**
- **Linux/macOS/Windows** (cross-platform)

### Running Tests
```bash
# Run all tests
.venv/bin/python3 tests/run_tests.py

# Run specific test file
.venv/bin/python3 -m pytest tests/test_board.py

# Run with coverage
.venv/bin/python3 -m pytest --cov=src tests/

# Verify AI difficulty levels
.venv/bin/python3 tests/verify_ai_levels.py
```

### Code Quality
```bash
# Run linter
.venv/bin/python3 -m flake8 src/ tests/

# Format code (if black is installed)
.venv/bin/python3 -m black src/ tests/
```

### Architecture Highlights
- **Minimax AI** with alpha-beta pruning and transposition tables
- **Move Analysis System** evaluating strategic factors
- **Settings Persistence** via JSON configuration
- **Modular Design** with clear separation of concerns
- **Comprehensive Logging** for debugging and monitoring
- **Error Handling** with custom exception hierarchy

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- **[Documentation Index](docs/README.md)** - Overview of all documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Architecture and implementation details
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Commands and shortcuts
- **[AI Verification](docs/AI_LEVELS_VERIFICATION.md)** - AI testing methodology

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the terms in the [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Classic Reversi/Othello game rules
- Pygame community for excellent documentation
- Python community for best practices

## 📧 Contact

**Author:** James "HoneyBadger"  
**Repository:** [https://github.com/James-HoneyBadger/Iago_Deluxe](https://github.com/James-HoneyBadger/Iago_Deluxe)

---

**Version:** 2.0 - Refactored Edition  
**Last Updated:** November 19, 2025
