"""
config.py – Constants, colours, and dataclasses for Iago Deluxe.

All magic numbers live here so the rest of the codebase stays clean.
Colour tuples are (R, G, B).  Layout measurements are in pixels.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum

# ── Layout ──────────────────────────────────────────────────────────────────
DEFAULT_BOARD_SIZE = 8
CELL_SIZE = 60          # pixels per board cell
MARGIN = 20             # pixels of blank space around the board
MENUBAR_HEIGHT = 32     # height of the top menu bar strip
UI_HEIGHT = 120         # height of the bottom info/status panel
HISTORY_WIDTH = 165     # width of the move-history sidebar
ANIMATION_SPEED = 0.3   # seconds for a piece placement / flip animation

# ── Named colours (kept for THEMES dict and test_settings.py) ────────────────
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)         # board cell colour
DARK_GREEN = (0, 100, 0)    # board grid lines
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (220, 60, 60)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)

# ── UI palette ───────────────────────────────────────────────────────────────
BG_DARK = (28, 28, 28)          # window background / UI panel fill
TEXT_PRIMARY = (235, 235, 235)  # main UI text
TEXT_DIM = (160, 160, 160)      # secondary / instruction text
TEXT_ACCENT = (255, 195, 50)    # highlights, game-over banner, AI indicator
HINT_DOT = (100, 200, 255)      # valid-move dots (legacy; currently unused)
HISTORY_BG = (38, 38, 44)       # sidebar background
WIN_BAR_BLACK = (55, 55, 65)       # win-probability bar: Black's share
WIN_BAR_WHITE = (215, 215, 210)   # win-probability bar: White's share
WIN_BAR_BG = (75, 75, 75)         # win-probability bar background track
HOVER_FLIP = (180, 230, 180)      # tint colour for hover-preview flip cells
LAST_MOVE_RING = (255, 215, 60)   # gold ring drawn on the last-played cell

# ── Game-piece constants ──────────────────────────────────────────────────────
EMPTY = 0
PLAYER_BLACK = 1
PLAYER_WHITE = 2

# ── Themes (board + accent colour palettes) ──────────────────────────────────
THEMES = {
    "Classic": {
        "board": (34, 139, 34),
        "board_alt": (0, 100, 0),
        "text": BLACK,
        "accent": BLUE,
        "highlight": YELLOW,
        "background": GREEN,
    },
    "Ocean": {
        "board": (25, 25, 112),
        "board_alt": (0, 0, 139),
        "text": WHITE,
        "accent": CYAN,
        "highlight": YELLOW,
        "background": (0, 0, 128),
    },
    "Sunset": {
        "board": (139, 69, 19),
        "board_alt": (160, 82, 45),
        "text": WHITE,
        "accent": (255, 165, 0),
        "highlight": YELLOW,
        "background": (178, 34, 34),
    },
    "Forest": {
        "board": (34, 139, 34),
        "board_alt": (0, 100, 0),
        "text": WHITE,
        "accent": (50, 205, 50),
        "highlight": YELLOW,
        "background": (0, 100, 0),
    },
}


class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    EXPERT = 4


@dataclass
class GameSettings:
    """Persistent user preferences (currently used by test_settings; UI uses
    in-game state directly).  Fields mirror the options exposed in draw_menu()."""

    theme: str = "Classic"
    sound_enabled: bool = True
    show_hints: bool = True
    ai_difficulty: str = "MEDIUM"
    board_size: int = DEFAULT_BOARD_SIZE
    player_color: int = PLAYER_BLACK
    animations: bool = True


@dataclass
class GameStats:
    """Cumulative player statistics, persisted to stats.json between sessions.
    ``current_streak`` is positive for a win streak and negative for a loss streak.
    """

    games_played: int = 0
    games_won: int = 0
    games_lost: int = 0
    games_drawn: int = 0
    total_moves: int = 0
    best_score: int = 0
    win_streak: int = 0
    loss_streak: int = 0
    current_streak: int = 0   # positive = win streak, negative = loss streak


@dataclass
class Animation:
    """One in-flight piece animation (placement scale-in or flip pulse).
    ``start_time`` is absolute seconds from ``pg.time.get_ticks() / 1000``.
    """

    row: int
    col: int
    player: int
    start_time: float
    duration: float
    anim_type: str  # 'place' or 'flip'
    start_scale: float = 0.0
    end_scale: float = 1.0


@dataclass
class GameState:
    """Snapshot of a complete board position used by undo/redo and save/load.
    ``winner`` is None while the game is in progress, 0 for a draw, or the
    PLAYER_* constant of the winning side.
    """

    board_grid: List[List[int]]
    current_player: int
    move_history: List[Dict[str, Any]]
    black_score: int
    white_score: int
    game_over: bool
    winner: Optional[int]
    settings: Dict[str, Any]
