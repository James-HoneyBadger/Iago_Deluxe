# Iago_Deluxe Documentation

Welcome to the comprehensive documentation for Iago_Deluxe, a feature-rich implementation of the classic Iago (Othello) board game.

## 📚 Documentation Index

### Quick Start
- **[Main README](../README.md)** - Project overview, installation, and quick start guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commands, shortcuts, and file locations

### Development
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Architecture, technical details, and development workflow
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines and code standards

### Implementation Details
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and feature changes
- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user manual

### Testing & Verification
- **[AI_LEVELS_VERIFICATION.md](AI_LEVELS_VERIFICATION.md)** - AI difficulty testing methodology

## 🎯 Quick Navigation

### For Users
**Just want to play?**
1. See [Installation Guide](../README.md#quick-start)
2. Read [Quick Reference](QUICK_REFERENCE.md) for commands
3. Check [Gameplay Tips](QUICK_REFERENCE.md#gameplay-tips)

### For Developers
**Contributing code?**
1. Read [Development Guide](DEVELOPMENT.md)
2. Review [Contributing Guidelines](../CONTRIBUTING.md)
3. Set up your [Development Environment](DEVELOPMENT.md#development-setup)

### For Researchers
**Analyzing the AI?**
1. See [AI Levels Verification](AI_LEVELS_VERIFICATION.md)
2. Review [AI Implementation](DEVELOPMENT.md#ai-class)
3. Run [AI Benchmarks](QUICK_REFERENCE.md#ai-benchmarking)

## 📁 Project Structure

```
Iago_Deluxe/
├── README.md                    # Main project documentation
├── CONTRIBUTING.md              # How to contribute
│
├── src/                         # Source code
│   ├── Iago.py              # Main game (5300+ lines)
│   ├── config.py               # Configuration
│   ├── logger.py               # Logging system
│   └── error_handling.py       # Error handling
│
├── tests/                       # Test suite
│   ├── test_*.py               # Unit tests
│   └── verify_ai_levels.py     # AI benchmarking
│
├── docs/                        # Documentation (you are here)
│   ├── README.md               # This file
│   ├── DEVELOPMENT.md          # Development guide
│   ├── QUICK_REFERENCE.md      # Quick reference
│   └── *.md                    # Other documentation
│
├── config/                      # Configuration files
│   └── reversi-settings.json   # User preferences
│
├── data/                        # Game data
│   └── *.pgn, *.json           # Saved games
│
└── assets/                      # Game assets
    └── reversi-icon.png        # Application icon
```

## 🎮 Features Overview

### Gameplay
- **Classic Iago** - Full implementation of Iago/Othello rules
- **6 AI Levels** - From beginner (Level 1) to expert (Level 6)
- **Multiple Board Sizes** - 4×4 to 16×16 (default 8×8)
- **Undo/Redo** - Full move history with unlimited undo
- **Move Hints** - Visual indicators for legal moves
- **Tutorial** - Interactive guide for new players

### Analysis
- **Move Analysis** - Real-time evaluation of move quality
- **Game Statistics** - Comprehensive post-game analysis
- **Performance Tracking** - Win/loss records per difficulty
- **Strategic Insights** - Board control, mobility, corner metrics

### Customization
- **5 Themes** - Classic, Ocean, Sunset, Midnight, Forest
- **Sound Effects** - Toggleable audio feedback
- **Save/Load** - PGN and JSON export formats
- **Settings Persistence** - Preferences saved automatically

## 🚀 Getting Started

### Installation
```bash
git clone https://github.com/James-HoneyBadger/Iago_Deluxe.git
cd Iago_Deluxe
./setup.sh
```

### Running the Game
```bash
./play.sh                        # Start with default settings
./play.sh -s 10 -d 5 -t ocean   # 10×10, Level 5, Ocean theme
./play.sh --help                # Show all options
```

See [Quick Reference](QUICK_REFERENCE.md) for complete command-line options.

## 🛠️ Development

### Prerequisites
- Python 3.7+
- Pygame 2.0+
- pytest (for testing)
- flake8 (for linting)

### Development Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
python3 tests/run_tests.py

# Check code quality
python3 -m flake8 src/ tests/
```

See [Development Guide](DEVELOPMENT.md) for detailed information.

## 📊 Testing

### Test Coverage
- **Board Logic:** 95% coverage
- **AI System:** 85% coverage
- **Settings:** 90% coverage
- **Overall:** ~87% coverage

### Running Tests
```bash
# All tests
python3 tests/run_tests.py

# With coverage report
python3 -m pytest --cov=src --cov-report=html tests/

# AI difficulty verification
python3 tests/verify_ai_levels.py
```

See [AI Levels Verification](AI_LEVELS_VERIFICATION.md) for testing methodology.

## 🤝 Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [DEVELOPMENT.md](DEVELOPMENT.md) - Technical architecture
- [Code of Conduct](#) - Community standards

### Quick Contribution Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📝 Version History

### v2.0.0 (Current - November 2025)
**Major Refactoring Release**
- Restructured into modular `src/` package
- Added comprehensive logging system
- Implemented error handling framework
- Enhanced configuration management
- Improved test coverage
- Updated documentation

### v1.0.0
**Initial Feature-Complete Release**
- Complete Iago gameplay
- AI opponent with 6 difficulty levels
- Post-game analysis
- Multiple themes
- Save/load functionality
- Tutorial system

## 🔗 External Resources

### Iago Strategy
- [World Othello Federation](https://www.worldothello.org/)
- [Iago Strategy Guide](https://www.worldothello.org/strategy)

### Technical References
- [Minimax Algorithm](https://en.wikipedia.org/wiki/Minimax)
- [Alpha-Beta Pruning](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning)
- [Pygame Documentation](https://www.pygame.org/docs/)

### Similar Projects
- [Edax](https://github.com/abulmo/edax-reversi) - Strong Iago engine
- [Logistello](http://www.radagast.se/othello/log.html) - Historic Othello program

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/James-HoneyBadger/Iago_Deluxe/issues)
- **Discussions:** [GitHub Discussions](https://github.com/James-HoneyBadger/Iago_Deluxe/discussions)
- **Email:** See repository for contact information

## 📄 License

This project is licensed under the terms in the [LICENSE](../LICENSE) file.

---

**Version:** 2.1.0  
**Last Updated:** November 27, 2025  
**Repository:** [https://github.com/James-HoneyBadger/Iago_Deluxe](https://github.com/James-HoneyBadger/Iago_Deluxe)
