# Reversi Deluxe

A feature-rich implementation of the classic Reversi (Othello) board game with AI opponent, built in Python using Pygame.

![Reversi Deluxe](screenshot.png)

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

# Run the game
python3 Reversi.py
```

### Alternative Installation
```bash
# Install from requirements
pip install -r requirements.txt

# Run the game
python3 Reversi.py
```

## How to Play

### Objective
Reversi is played on an 8x8 board with black and white pieces. The goal is to have the majority of your color pieces on the board when no more moves can be made.

### Rules
1. Players take turns placing pieces on empty squares
2. Each move must "sandwich" at least one opponent piece between your new piece and an existing piece of your color
3. All sandwiched opponent pieces flip to your color
4. If no legal moves are available, the turn passes to the opponent
5. The game ends when neither player can move
6. The player with the most pieces wins

### Controls
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

### Project Structure
```
reversi-deluxe/
├── Reversi.py          # Main game file
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── LICENSE            # MIT License
├── .gitignore         # Git ignore rules
└── assets/            # Game assets (if any)
```

### Architecture
- **Board**: Core game logic and move validation
- **AI**: Minimax algorithm with alpha-beta pruning
- **UI**: Pygame-based interface with themes
- **Analysis**: Move evaluation and game statistics
- **Settings**: Persistent configuration management

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with descriptive messages: `git commit -am 'Add feature'`
5. Push to your branch: `git push origin feature-name`
6. Submit a pull request

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