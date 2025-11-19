# Reversi Deluxe - Development Guide

## Table of Contents

- [Version History](#version-history)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Technical Implementation](#technical-implementation)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)

## Version History

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
- Complete Reversi gameplay implementation
- AI opponent with 6 difficulty levels
- Post-game analysis system
- Move-by-move analysis window
- Multiple themes and visual customization
- Save/load functionality
- Tutorial system
- Sound effects and animations

## Architecture Overview

### Design Philosophy

HB_Reversi follows a **component-based architecture** with clear separation of concerns:

1. **Game Logic Layer** - Pure game rules and state management
2. **AI Layer** - Intelligent opponent with configurable difficulty
3. **UI Layer** - Pygame-based rendering and user interaction
4. **Data Layer** - Settings persistence and game export
5. **Analysis Layer** - Move evaluation and statistical tracking

### Technology Stack

- **Language:** Python 3.7+ (tested on 3.13)
- **Graphics:** Pygame 2.0+
- **Configuration:** JSON-based settings
- **Testing:** pytest with coverage reporting
- **Code Quality:** Flake8 linting, Black formatting

## Project Structure

```
HB_Reversi/
├── src/                        # Source code package
│   ├── __init__.py            # Package initialization
│   ├── Reversi.py             # Main game implementation (5100+ lines)
│   ├── config.py              # Configuration constants and dataclasses
│   ├── logger.py              # Logging system with file rotation
│   └── error_handling.py      # Custom exceptions and validators
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── run_tests.py           # Test runner with coverage
│   ├── test_board.py          # Board logic unit tests
│   ├── test_ai.py             # AI behavior tests
│   ├── test_settings.py       # Settings persistence tests
│   ├── test_ai_levels.py      # AI difficulty tests
│   ├── test_move_analysis.py  # Move analysis tests
│   └── verify_ai_levels.py    # AI performance benchmarking
│
├── docs/                       # Documentation
│   ├── README.md              # Documentation index
│   ├── DEVELOPMENT.md         # This file
│   ├── QUICK_REFERENCE.md     # Commands and shortcuts
│   ├── IMPLEMENTATION_SUMMARY.md  # Implementation notes
│   ├── IMPROVEMENTS.md        # Enhancement history
│   ├── ENHANCEMENTS.md        # Feature descriptions
│   ├── AI_LEVELS_VERIFICATION.md  # AI testing results
│   └── MENU_IMPROVEMENTS.txt  # UI enhancement notes
│
├── assets/                     # Game assets
│   └── reversi-icon.png       # Application icon
│
├── config/                     # Runtime configuration
│   └── reversi-settings.json  # User preferences (auto-generated)
│
├── data/                       # Game data
│   ├── *.pgn                  # Saved games in PGN format
│   └── *.json                 # Saved games in JSON format
│
├── main.py                     # Entry point with dependency checks
├── play.sh                     # Convenient launcher script
├── setup.sh                    # Installation script
├── requirements.txt            # Python dependencies
├── .flake8                     # Linting configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Project overview
├── CONTRIBUTING.md             # Contribution guidelines
└── LICENSE                     # License information
```

## Core Components

## Core Components

### 1. Board Class
**Location:** `src/Reversi.py`

**Responsibilities:**
- Game state management (8x8 to 16x16 grids)
- Move validation and legal move generation
- Win condition checking
- Board serialization for save/load
- Move history tracking

**Key Methods:**
```python
def legal_moves(player: int) -> list[tuple[int, int]]
    """Generate all valid moves for player."""

def make_move(row: int, col: int, player: int) -> bool
    """Execute move and flip pieces."""

def check_game_over() -> tuple[bool, int | None]
    """Check if game has ended and determine winner."""
```

**Design Decisions:**
- Uses 2D list for grid (0=empty, 1=black, 2=white)
- Efficient directional search for valid moves
- Immutable move history for undo/redo

### 2. AI Class
**Location:** `src/Reversi.py`

**Responsibilities:**
- Intelligent move selection
- Position evaluation
- Search depth management
- Performance optimization

**Algorithm:** Minimax with Alpha-Beta Pruning
- **Levels 1-2:** Shallow search (1-2 ply), basic evaluation
- **Levels 3-4:** Medium search (3-4 ply), strategic factors
- **Levels 5-6:** Deep search (5-6 ply), advanced heuristics

**Evaluation Function Factors:**
1. **Piece Count** - Basic material advantage
2. **Corner Control** - High-value stable positions
3. **Edge Control** - Semi-stable positions
4. **Mobility** - Number of legal moves
5. **Position Tables** - Strategic square values

**Optimizations:**
- Alpha-beta pruning (reduces search space by ~50%)
- Transposition table (caching evaluated positions)
- Move ordering (best moves first for better pruning)

**Key Methods:**
```python
def find_best_move(board: Board, depth: int) -> tuple[int, int] | None
    """Find optimal move using minimax search."""

def minimax(board: Board, depth: int, alpha: float, beta: float, 
            is_maximizing: bool) -> float
    """Minimax algorithm with alpha-beta pruning."""

def evaluate(board: Board) -> float
    """Evaluate position from AI perspective."""
```

### 3. Game Class
**Location:** `src/Reversi.py`

**Responsibilities:**
- Main game loop and event handling
- UI coordination and rendering
- State machine management
- Integration of all subsystems

**Game States:**
- `MENU` - Main menu display
- `PLAYING` - Active gameplay
- `GAME_OVER` - Post-game state
- `PAUSED` - Pause menu
- `TUTORIAL` - Tutorial mode

**Key Methods:**
```python
def run() -> None
    """Main game loop."""

def handle_events() -> None
    """Process user input."""

def update() -> None
    """Update game state."""

def render() -> None
    """Draw everything to screen."""
```

### 4. UI Components

#### MenuSystem
**Location:** `src/Reversi.py`

**Features:**
- Dynamic menu generation
- Hover effects and visual feedback
- Nested submenus
- Keyboard shortcuts

**Menu Structure:**
```
Game
├── New Game
├── Board Size
├── Save Game
└── Quit

AI
├── Difficulty
└── Play as

Settings
├── Theme
├── Sound
├── Hints
└── Move Preview

View
├── Analysis
├── Statistics
└── Tutorial
```

#### GameAnalysisDisplay
**Location:** `src/Reversi.py`

**Features:**
- Post-game statistics
- Move quality breakdown
- Strategic insights
- Performance metrics

**Metrics Displayed:**
- Final score and winner
- Total moves played
- Corner captures
- Edge control
- Mobility advantage
- Move quality distribution

#### MoveAnalysisDisplay
**Location:** `src/Reversi.py`

**Features:**
- Real-time move analysis window
- Move-by-move evaluation
- Strategic impact assessment
- Quality ratings (Excellent/Good/Fair/Poor/Blunder)

**Analysis Factors:**
- Board control change
- Position score change
- Mobility impact
- Corner/edge implications

### 5. Configuration System
**Location:** `src/config.py`

**Components:**
```python
@dataclass
class GameConfig:
    """Game logic configuration."""
    DEFAULT_BOARD_SIZE: int = 8
    MIN_BOARD_SIZE: int = 4
    MAX_BOARD_SIZE: int = 16
    DEFAULT_AI_DEPTH: int = 4
    MAX_AI_DEPTH: int = 6

@dataclass
class UIConfig:
    """UI settings."""
    DEFAULT_WINDOW_WIDTH: int = 1000
    DEFAULT_WINDOW_HEIGHT: int = 800
    FPS: int = 60
    ANIMATION_SPEED: int = 10

@dataclass
class FileConfig:
    """File paths."""
    SETTINGS_FILE: str = "config/reversi-settings.json"
    DATA_DIR: str = "data/"
    ICON_PATH: str = "assets/reversi-icon.png"

class Colors:
    """Color constants."""
    # Theme colors defined here

THEMES: dict[str, dict[str, tuple[int, int, int]]]
    # Theme definitions
```

### 6. Logging System
**Location:** `src/logger.py`

**Features:**
- Dual output (console + file)
- Automatic log rotation (10MB max, 3 backups)
- Configurable log levels
- Performance logging decorator
- Exception logging context manager

**Usage:**
```python
from src.logger import get_logger, log_performance

logger = get_logger(__name__)

logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")

@log_performance
def expensive_function():
    """Automatically logs execution time."""
    pass

with ErrorContext("Operation description"):
    # Automatically logs exceptions
    risky_operation()
```

### 7. Error Handling
**Location:** `src/error_handling.py`

**Custom Exceptions:**
```python
class ReversiError(Exception)
    """Base exception for all Reversi errors."""

class InvalidMoveError(ReversiError)
    """Raised for illegal moves."""

class InvalidBoardStateError(ReversiError)
    """Raised for corrupted board state."""

class SaveFileError(ReversiError)
    """Raised for save/load failures."""

class ConfigurationError(ReversiError)
    """Raised for invalid configuration."""
```

**Validation Functions:**
```python
validate_board_size(size: int) -> bool
validate_ai_depth(depth: int) -> bool
validate_theme(theme: str) -> bool
validate_save_file(filepath: str) -> bool
```

## Technical Implementation

### Move Validation Algorithm

```python
def legal_moves(self, player: int) -> list[tuple[int, int]]:
    """
    Efficient legal move generation.
    Time Complexity: O(n²) where n is board size
    """
    moves = []
    for row in range(self.size):
        for col in range(self.size):
            if self.grid[row][col] == 0:  # Empty square
                if self._is_legal_move(row, col, player):
                    moves.append((row, col))
    return moves
```

### AI Search Algorithm

```python
def minimax(self, board, depth, alpha, beta, is_maximizing):
    """
    Minimax with alpha-beta pruning.
    Average pruning: ~50% of nodes
    Transposition table hit rate: ~30-40%
    """
    # Check transposition table
    board_key = board.to_key()
    if board_key in self.transposition_table:
        cached_depth, cached_value = self.transposition_table[board_key]
        if cached_depth >= depth:
            return cached_value
    
    # Base case: depth limit or game over
    if depth == 0 or board.check_game_over()[0]:
        return self.evaluate(board)
    
    # Recursive search with pruning
    if is_maximizing:
        max_eval = float('-inf')
        for move in board.legal_moves(self.color):
            # ... evaluation logic ...
            if eval_score > max_eval:
                max_eval = eval_score
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    # ... minimizing logic ...
```

### Disc Rendering System

**Caching Strategy:**
```python
def _render_disc(self, color, size):
    """
    Pre-render discs for all sizes.
    Cache hit rate: ~99% during normal gameplay
    Memory usage: ~2MB for all cached discs
    """
    cache_key = (color, size)
    if cache_key in self._disc_cache:
        return self._disc_cache[cache_key]
    
    # Render new disc with radial gradient
    disc = self._create_disc_surface(color, size)
    self._disc_cache[cache_key] = disc
    return disc
```

### Settings Persistence

```python
@dataclass
class Settings:
    """User preferences with JSON serialization."""
    theme: str = "classic"
    sound: bool = True
    hints: bool = True
    ai_difficulty: int = 4
    board_size: int = 8
    
    def save(self):
        """Save to JSON file."""
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls):
        """Load from JSON file with defaults."""
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                return cls(**json.load(f))
        return cls()  # Use defaults
```

## Development Setup

## Development Setup

### Initial Setup

1. **Clone repository:**
   ```bash
   git clone https://github.com/James-HoneyBadger/HB_Reversi.git
   cd HB_Reversi
   ```

2. **Run setup script:**
   ```bash
   ./setup.sh
   ```
   This creates a virtual environment and installs dependencies.

3. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

### Development Workflow

**Running the game:**
```bash
# Using launcher script
./play.sh

# Direct execution
.venv/bin/python3 main.py

# With debug logging
.venv/bin/python3 main.py --debug

# Custom configuration
.venv/bin/python3 main.py -s 10 -d 5 -t ocean
```

**Code quality checks:**
```bash
# Linting
python3 -m flake8 src/ tests/

# Auto-formatting (if Black installed)
python3 -m black src/ tests/

# Type checking (if mypy installed)
python3 -m mypy src/
```

### Environment Variables

Optional environment variables for development:

```bash
# Enable debug logging
export REVERSI_DEBUG=1

# Custom settings file
export REVERSI_SETTINGS="/path/to/settings.json"

# Disable sound (useful for automated testing)
export REVERSI_NO_SOUND=1
```

## Testing

### Test Suite Organization

```
tests/
├── run_tests.py           # Main test runner
├── test_board.py          # Board logic tests (15 tests)
├── test_ai.py             # AI behavior tests (10 tests)
├── test_settings.py       # Settings tests (8 tests)
├── test_ai_levels.py      # AI difficulty tests (6 tests)
├── test_move_analysis.py  # Analysis tests (12 tests)
└── verify_ai_levels.py    # AI benchmarking tool
```

### Running Tests

**All tests:**
```bash
python3 tests/run_tests.py
```

**Specific test file:**
```bash
python3 -m pytest tests/test_board.py -v
```

**With coverage:**
```bash
python3 -m pytest --cov=src --cov-report=html tests/
# View report: open htmlcov/index.html
```

**Performance tests:**
```bash
python3 -m pytest tests/ -v -s --durations=10
```

### Test Coverage

Current coverage (as of v2.0.0):
- **Board Logic:** 95% coverage
- **AI System:** 85% coverage
- **Settings:** 90% coverage
- **Overall:** ~87% coverage

### Writing New Tests

Example test structure:
```python
import pytest
from src.Reversi import Board, AI

class TestBoard:
    """Board logic tests."""
    
    def setup_method(self):
        """Setup before each test."""
        self.board = Board(size=8)
    
    def test_initial_position(self):
        """Test starting position is correct."""
        assert self.board.grid[3][3] == 2
        assert self.board.grid[4][4] == 2
    
    def test_legal_moves_black(self):
        """Test legal moves for black from start."""
        moves = self.board.legal_moves(player=1)
        assert len(moves) == 4
        assert (2, 3) in moves

@pytest.mark.parametrize("size,expected", [
    (4, 4),
    (6, 36),
    (8, 64),
])
def test_board_sizes(size, expected):
    """Test various board sizes."""
    board = Board(size=size)
    assert board.size == size
    assert len(board.grid) * len(board.grid[0]) == expected
```

### Benchmarking

**AI Performance Benchmarking:**
```bash
python3 tests/verify_ai_levels.py
```

This runs performance tests for each AI difficulty level:
- Measures average move time
- Evaluates move quality
- Tests win rates against random play

**Expected Performance:**
- Level 1: <0.1s per move
- Level 2: <0.2s per move
- Level 3: <0.5s per move
- Level 4: <1.0s per move
- Level 5: <2.0s per move
- Level 6: <5.0s per move

## Performance Optimization

### Profiling

**Profile AI performance:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run AI move
ai = AI(color=1, depth=5)
move = ai.find_best_move(board)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)
```

**Memory profiling:**
```bash
# Install memory_profiler
pip install memory-profiler

# Run with profiling
python3 -m memory_profiler main.py
```

### Optimization Checklist

- [ ] Use transposition table for AI caching
- [ ] Implement move ordering for better pruning
- [ ] Cache rendered discs
- [ ] Minimize object creation in tight loops
- [ ] Use list comprehensions over loops where appropriate
- [ ] Profile before optimizing

## Debugging

### Debug Mode

Enable comprehensive logging:
```bash
python3 main.py --debug
```

This logs:
- All game events
- AI decision-making process
- Move validation details
- Performance metrics

### Common Issues

**Issue: Game runs slowly**
- Check AI depth setting (reduce if needed)
- Verify disc cache is working
- Profile to find bottlenecks

**Issue: Invalid moves accepted**
- Check board state integrity
- Verify move validation logic
- Test with smaller board size

**Issue: AI makes poor moves**
- Verify evaluation function weights
- Check transposition table for corruption
- Test with different difficulty levels

### Logging

**Log files location:** `reversi.log`

**Log levels:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages

**Example log output:**
```
2025-11-19 10:30:15,123 - src.Reversi - INFO - Game started
2025-11-19 10:30:15,124 - src.Reversi - DEBUG - Board size: 8x8
2025-11-19 10:30:20,456 - src.Reversi - INFO - AI move: (2, 3)
2025-11-19 10:30:20,457 - src.Reversi - DEBUG - Search depth: 4, time: 0.33s
```

## Future Enhancements

### Planned Features (Priority Order)

1. **Network Multiplayer** (High Priority)
   - TCP/IP-based connection
   - Lobby system
   - Chat functionality
   - ELO rating system

2. **Opening Book** (Medium Priority)
   - Database of common openings
   - Move suggestions from book
   - Learning from played games

3. **Advanced Analysis** (Medium Priority)
   - Position database
   - Statistical analysis across games
   - Move patterns recognition
   - Tactical puzzle mode

4. **UI Improvements** (Medium Priority)
   - 3D board rendering option
   - Customizable piece styles
   - Animation preferences
   - Accessibility features

5. **AI Enhancements** (Low Priority)
   - Neural network evaluation
   - Monte Carlo Tree Search option
   - AI personality profiles
   - Adaptive difficulty

### Technical Improvements Needed

**Code Structure:**
- Split `Reversi.py` into multiple modules
- Separate UI from game logic
- Create dedicated AI package
- Improve type annotations

**Testing:**
- Increase coverage to 95%+
- Add integration tests
- Implement UI automation tests
- Performance regression tests

**Performance:**
- Implement bitboard representation
- Optimize move generation
- Parallel AI search (threading)
- GPU acceleration for evaluation

**Documentation:**
- API documentation with Sphinx
- Video tutorials
- Developer cookbook
- Architecture diagrams

## Contributing

For contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md)

### Development Standards

**Code Style:**
- Follow PEP 8 (with 88-char line length)
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small

**Git Workflow:**
- Create feature branches
- Write descriptive commit messages
- Keep commits atomic
- Rebase before merging

**Documentation:**
- Update docs with code changes
- Add examples for new features
- Keep README current
- Document breaking changes

## Resources

### Reversi Strategy
- [Reversi Strategy Guide](https://www.worldothello.org/strategy)
- [Othello Opening Theory](https://www.radagast.se/othello/howto.html)

### Technical References
- [Minimax Algorithm](https://en.wikipedia.org/wiki/Minimax)
- [Alpha-Beta Pruning](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning)
- [Pygame Documentation](https://www.pygame.org/docs/)

### Similar Projects
- [Edax](https://github.com/abulmo/edax-reversi) - Strong Reversi engine
- [NTest](https://github.com/ntest/ntest) - Othello test suite

---

**Last Updated:** November 19, 2025  
**Version:** 2.0.0  
**Maintainer:** James "HoneyBadger"
