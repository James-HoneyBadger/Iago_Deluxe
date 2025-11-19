# HB_Reversi

A feature-rich implementation of the classic Reversi (Othello) board game with AI opponent.

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/James-HoneyBadger/HB_Reversi.git
   cd HB_Reversi
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   This will create a virtual environment and install all dependencies.

### Running the Game

**Easiest way (recommended):**
```bash
./play.sh
```

**Using virtual environment directly:**
```bash
.venv/bin/python3 main.py
```

**Using system Python (if pygame is installed globally):**
```bash
python3 main.py
```

### Command-line Options

```bash
./play.sh --help              # Show all options
./play.sh -s 10               # Play on 10x10 board
./play.sh -d 5 -t midnight    # Hard AI with dark theme
./play.sh --no-sound          # Play without sound effects
```

## Features

- Classic Reversi gameplay with AI opponent
- Multiple difficulty levels (1-6)
- Beautiful themes (Classic, Ocean, Sunset, Midnight, Forest)
- Move hints and analysis
- Undo/Redo functionality
- Save/Load games
- Sound effects

## Documentation

For detailed documentation, see [docs/README.md](docs/README.md)

## Requirements

- Python 3.7 or higher
- Pygame 2.0 or higher (automatically installed by setup script)

## License

See [LICENSE](LICENSE) file for details.
