# Reversi Deluxe

A feature-rich implementation of the classic Reversi (Othello) board game with AI opponent, built in Python using Pygame.

![Reversi Deluxe](screenshot.png)

## 🎯 What's New in v2.0

**Major improvements for reliability and usability:**
- ✅ **Comprehensive test suite** - 75+ automated tests
- ✅ **Advanced logging system** - Debug and monitor gameplay
- ✅ **Enhanced CLI** - 10+ command-line options
- ✅ **Better error handling** - Graceful error recovery
- ✅ **Centralized configuration** - Easy customization

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for full details.

## Features

### Game Features
- **Classic Reversi gameplay** with standard 8x8 board
- **AI opponent** with configurable difficulty levels (1-6)
- **Human vs Human** or **Human vs AI** gameplay modes
- **Move hints** and **legal move highlighting**
- **Undo/Redo** functionality for move exploration
- **Save/Load** games with JSON format
- **Sound effects** and **visual animations**

### Analysis Features
- **Post-game analysis** with comprehensive statistics
- **Move-by-move analysis** with quality ratings
- **Real-time move feedback** during gameplay
- **Board control tracking** and strategic insights
- **Performance metrics** for both players

### Interface Features
- **Multiple themes** (Classic, Wood, Ocean, Midnight)
- **Responsive design** with resizable window
- **Clean menu system** with keyboard shortcuts
- **Tutorial system** for new players
- **Desktop launcher** creation

## Installation

### Requirements
- Python 3.7 or higher
- Pygame 2.0 or higher

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/reversi-deluxe.git
cd reversi-deluxe

# Install dependencies
pip install pygame

# Run the game with default settings
python3 Reversi.py

# Or with custom options
python3 Reversi.py --size 10 --difficulty 5 --theme midnight
```

### Alternative Installation
```bash
# Install from requirements
pip install -r requirements.txt

# Run the game
python3 Reversi.py
```

## How to Play

### Command-Line Options (New in v2.0!)

```bash
# View all options
python3 Reversi.py --help

# Start with custom board size
python3 Reversi.py --size 10

# Set AI difficulty (1=Beginner, 6=Master)
python3 Reversi.py --difficulty 5

# Choose a theme
python3 Reversi.py --theme midnight

# Disable sound effects
python3 Reversi.py --no-sound

# Load a saved game
python3 Reversi.py --load mygame.rsv

# AI vs AI mode
python3 Reversi.py --ai-black --ai-white

# Enable debug logging
python3 Reversi.py --debug

# Combine multiple options
python3 Reversi.py -s 10 -d 5 -t ocean --no-sound
```

Available options:
- `-s, --size N` - Board size (4-16, even numbers)
- `-d, --difficulty LEVEL` - AI difficulty (1-6)
- `-t, --theme THEME` - Color theme (classic, ocean, sunset, midnight, forest)
- `--no-sound` - Disable sound effects
- `--load FILE` - Load saved game
- `--ai-black` - Enable AI for black player
- `--ai-white` - Enable AI for white player
- `--debug` - Enable debug logging
- `--version` - Show version
- `-h, --help` - Show help message

### Objective
Reversi is played on an 8x8 board with black and white pieces. The goal is to have the majority of your color pieces on the board when no more moves can be made.

### Rules
1. Players take turns placing pieces on empty squares
2. Each move must "sandwich" at least one opponent piece between your new piece and an existing piece of your color
3. All sandwiched opponent pieces flip to your color
4. If no legal moves are available, the turn passes to the opponent
5. The game ends when neither player can move
6. The player with the most pieces wins

### In-Game Controls
- **Mouse**: Click to place pieces
- **V**: Toggle move analysis window
- **H**: Toggle move hints
- **U/R**: Undo/Redo moves
- **N**: New game
- **S/L**: Save/Load game
- **A**: Toggle AI for current player
- **D**: Cycle AI difficulty
- **G**: Show post-game analysis (after game ends)
- **T**: Show tutorial
- **M**: Toggle sound
- **Q/ESC**: Quit

## Game Modes

### AI Difficulty Levels
1. **Beginner** - Simple evaluation, good for learning
2. **Easy** - Basic strategy with some lookahead
3. **Medium** - Balanced play with moderate depth
4. **Hard** - Strong strategic play
5. **Expert** - Advanced evaluation with deep search
6. **Master** - Maximum difficulty with sophisticated strategy

### Analysis Features
- **Move Quality Ratings**: Excellent, Good, Fair, Poor
- **Strategic Metrics**: Board control, corner control, mobility
- **Performance Tracking**: Move accuracy, critical moments
- **Post-game Review**: Complete game analysis with suggestions

## Themes

Choose from multiple visual themes:
- **Classic**: Traditional black and white
- **Wood**: Elegant wooden board design
- **Ocean**: Blue oceanic theme
- **Midnight**: Dark theme for night play

## Configuration

The game automatically saves settings including:
- Theme preference
- Sound settings
- AI difficulty levels
- Window size and position

Settings are stored in `reversi_settings.json`.

## Development

## Development

### Running Tests (New in v2.0!)

The project includes a comprehensive test suite with 75+ tests.

```bash
# Run all tests
cd tests
python3 run_tests.py

# Run tests with verbose output
python3 run_tests.py -v

# Run specific test module
python3 run_tests.py -m test_board

# Quiet mode (only show summary)
python3 run_tests.py -q
```

Test coverage includes:
- **Board logic** - Move validation, game state, undo/redo
- **AI functionality** - Evaluation, move selection, difficulty levels
- **Settings & I/O** - Save/load, error handling, validation

### Debugging

Enable debug logging to troubleshoot issues:

```bash
python3 Reversi.py --debug
```

Logs are written to `reversi.log` with detailed information about:
- Game state changes
- AI decision making
- File operations
- Performance metrics

### Project Structure
```
reversi-deluxe/
├── Reversi.py              # Main game file
├── config.py               # Centralized configuration
├── logger.py               # Logging system
├── error_handling.py       # Error handling utilities
├── tests/                  # Test suite
│   ├── test_board.py       # Board tests
│   ├── test_ai.py          # AI tests
│   ├── test_settings.py    # Settings tests
│   └── run_tests.py        # Test runner
├── README.md               # This file
├── IMPROVEMENTS.md         # Detailed improvement docs
├── IMPLEMENTATION_SUMMARY.md  # Implementation summary
├── requirements.txt        # Python dependencies
└── LICENSE                 # MIT License
```

### Architecture
- **Board**: Core game logic and move validation
- **AI**: Minimax algorithm with alpha-beta pruning
- **UI**: Pygame-based interface with themes
- **Analysis**: Move evaluation and game statistics
- **Settings**: Persistent configuration management
- **Logger**: Centralized logging framework (v2.0)
- **Config**: Centralized configuration (v2.0)
- **Error Handling**: Validation and error recovery (v2.0)

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. **Run the test suite**: `cd tests && python3 run_tests.py`
5. Commit with descriptive messages: `git commit -am 'Add feature'`
6. Push to your branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the classic Reversi/Othello board game
- Built with Python and Pygame
- AI implementation uses minimax with alpha-beta pruning
- Thanks to the Pygame community for excellent documentation

## Screenshots

### Main Game Interface
Classic gameplay with move hints enabled.

### Post-Game Analysis
Comprehensive analysis showing move quality and strategic insights.

### Move Analysis Window
Real-time analysis of individual moves with detailed metrics.

---

**Enjoy playing Reversi Deluxe!** 🎮

For questions, suggestions, or bug reports, please open an issue on GitHub.