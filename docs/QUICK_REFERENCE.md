# Iago Deluxe - Quick Reference

## 📁 File Locations

### Configuration Files
```
config/iago-settings.json   # Your game preferences (auto-created)
```

### Game Data
```
data/
├── iago_game_*.pgn       # Saved games (PGN format)
└── iago_game_*.json      # Saved games (JSON format)
```

### Logs
```
iago.log                   # Game logs (auto-rotated at 10MB)
```

## 🚀 Quick Start Commands

### Basic Usage
```bash
# Start game with default settings
./play.sh

# Show all options
./play.sh --help

# Direct Python execution
.venv/bin/python3 main.py
```

## ⌨️ Keyboard Shortcuts

### Game Control
| Key | Action |
|-----|--------|
| `N` | New game |
| `S` | Save game |
| `L` | Load game |
| `Q` | Quit game |
| `ESC` | Pause menu |

### Move Navigation
| Key | Action |
|-----|--------|
| `U` | Undo last move |
| `R` | Redo move |
| `Ctrl+Z` | Undo (alternative) |
| `Ctrl+Y` | Redo (alternative) |

### AI & Hints
| Key | Action |
|-----|--------|
| `H` | Toggle hints |
| `I` | Toggle AI move preview |
| `A` | Toggle AI for current player |
| `D` | Cycle AI difficulty |

### Analysis & Help
| Key | Action |
|-----|--------|
| `V` | Toggle move analysis window |
| `T` | Open tutorial |
| `F1` | Help screen |

### View Options
| Key | Action |
|-----|--------|
| `M` | Toggle sound |
| `Alt` | Show menu bar |
| `F11` | Toggle fullscreen (if supported) |

## 🖱️ Mouse Controls

### Gameplay
- **Click empty square** - Place piece (if legal move)
- **Hover over square** - Highlight move preview
- **Click menu item** - Execute menu action

### Menu Navigation
- **Click menu** - Open dropdown
- **Hover menu item** - Highlight option
- **Click outside menu** - Close menu

## 📊 Game Menus

### Game Menu
```
New Game               # Start fresh game
├── Reset Board        # Clear current game
Board Size            # Choose board dimensions
├── 4×4, 6×6, 8×8     # Small to standard
├── 10×10, 12×12      # Medium boards
└── 14×14, 16×16      # Large boards
Save Game             # Export to data/
Load Game             # Import from data/
Quit                  # Exit application
```

### AI Menu
```
Difficulty Level
├── Level 1 - Beginner    # Depth 1, quick moves
├── Level 2 - Easy        # Depth 2
├── Level 3 - Medium      # Depth 3
├── Level 4 - Normal      # Depth 4, balanced
├── Level 5 - Hard        # Depth 5, strong play
└── Level 6 - Expert      # Depth 6, maximum strength

Play As
├── Black (Human)         # You play black
├── White (Human)         # You play white
└── Both AI               # Watch AI vs AI
```

### Settings Menu
```
Theme
├── Classic               # Traditional green board
├── Ocean                 # Blue water theme
├── Sunset                # Orange/purple palette
├── Midnight              # Dark mode
└── Forest                # Green nature theme

Sound Effects
├── On                    # Enable audio
└── Off                   # Mute sounds

Move Hints
├── On                    # Show legal moves
└── Off                   # Hide hints

Move Preview
├── On                    # Show piece placement preview
└── Off                   # Disable preview
```

### View Menu
```
Analysis Window           # Toggle move-by-move analysis
Game Statistics          # Per-difficulty stats
Tutorial                 # Interactive guide
About                    # Version info
```

## 🎮 Gameplay Tips

### Opening Strategy
1. **Control the center** - Occupy central squares early
2. **Minimize mobility** - Reduce opponent's options
3. **Avoid edges early** - Unless setting up corner captures

### Mid-Game Tactics
1. **Corner strategy** - Corners are permanent positions
2. **Edge control** - Build stable edge formations
3. **Tempo** - Force opponent to make weak moves

### Endgame Techniques
1. **Count pieces** - Know if you need to play aggressive/defensive
2. **Parity** - Try to make last move
3. **Sweep edges** - Convert edge positions to corners

### Using Analysis
1. **Move quality** - Green = Excellent, Red = Poor
2. **Board control** - Track +/- piece advantage
3. **Mobility** - More options = better position
4. **Post-game review** - Study mistakes after game

## 📈 Statistics Tracking

### Per-Difficulty Stats
Automatically tracked for each AI level (1-6):
- **Games played** - Total games against this level
- **Wins** - Your victories
- **Losses** - AI victories  
- **Ties** - Draw games
- **Win rate** - Percentage of wins

Access via: `View → Game Statistics`

### Game Analysis
After each game, view:
- Final score breakdown
- Move quality distribution
- Corner captures count
- Edge control metrics
- Mobility advantage
- Strategic insights

Access via: Help → Game Analysis (after game ends)

## 💾 Save & Load

### Automatic Saves
- Settings automatically saved to `config/reversi-settings.json`
- Statistics updated after each game

### Manual Game Save
```bash
# In-game: Press S or Game → Save Game
# Creates: data/iago_game_YYYYMMDD_HHMMSS.pgn

# Load saved game: Game → Load Game
# Select from data/ directory
```

### Export Formats

**PGN (Portable Game Notation):**
- Standard chess-like notation
- Compatible with analysis tools
- Human-readable text format

**JSON (JavaScript Object Notation):**
- Programmatic access
- Full game state
- Easy parsing for custom tools

## 🔧 Troubleshooting

### Game Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.7+

# Reinstall dependencies
./setup.sh

# Check pygame installation
python3 -c "import pygame; print(pygame.ver)"
```

### Performance Issues
```bash
# Reduce AI difficulty
./play.sh -d 3  # Use level 3 instead of 6

# Disable debug logging
# Remove --debug flag

# Use smaller board
./play.sh -s 8  # Standard 8×8 board
```

### Sound Not Working
```bash
# Check sound setting
# Settings → Sound → On

# Test system audio
# Verify other apps have sound

# Run without sound
./play.sh --no-sound
```

### Settings Not Saving
```bash
# Check config directory exists
ls -la config/

# Check file permissions
chmod 755 config/
chmod 644 config/reversi-settings.json

# Check disk space
df -h
```

## 🧪 Development Commands

### Running Tests
```bash
# All tests
python3 tests/run_tests.py

# Specific test file
python3 -m pytest tests/test_board.py -v

# With coverage
python3 -m pytest --cov=src tests/
```

### Code Quality
```bash
# Linting
python3 -m flake8 src/ tests/

# Type checking (if mypy installed)
python3 -m mypy src/

# Format code (if black installed)
python3 -m black src/ tests/
```

### AI Benchmarking
```bash
# Verify AI difficulty levels
python3 tests/verify_ai_levels.py

# Test specific level
python3 tests/test_ai_levels.py -v
```

## 📚 File Structure Reference

```
Iago_Deluxe/
├── main.py                     # Entry point
├── play.sh                     # Launcher script
├── setup.sh                    # Setup script
├── requirements.txt            # Dependencies
├── .flake8                     # Linting config
│
├── src/                        # Source code
│   ├── Iago.py             # Main game (5100+ lines)
│   ├── config.py              # Configuration
│   ├── logger.py              # Logging system
│   └── error_handling.py      # Error handling
│
├── tests/                      # Test suite
│   ├── run_tests.py           # Test runner
│   ├── test_*.py              # Test files
│   └── verify_ai_levels.py    # AI benchmarking
│
├── docs/                       # Documentation
│   ├── DEVELOPMENT.md         # Dev guide
│   ├── QUICK_REFERENCE.md     # This file
│   └── *.md                   # Other docs
│
├── config/                     # Runtime config
│   └── reversi-settings.json  # User settings
│
├── data/                       # Game data
│   └── *.pgn, *.json          # Saved games
│
└── assets/                     # Game assets
    └── reversi-icon.png       # App icon
```

## 🔗 Additional Resources

- **README.md** - Project overview and installation
- **DEVELOPMENT.md** - Architecture and technical details
- **CONTRIBUTING.md** - Contribution guidelines
- **IMPLEMENTATION_SUMMARY.md** - Feature implementation notes

---

**Version:** 2.0.0  
**Last Updated:** November 19, 2025  
**For More Help:** See docs/README.md
