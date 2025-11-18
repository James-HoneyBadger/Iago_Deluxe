#!/usr/bin/env python3
"""
Configuration module for Reversi Deluxe
Centralized configuration for easier modification and maintenance
"""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class GameConfig:
    """Game logic configuration"""

    # Board settings
    DEFAULT_BOARD_SIZE: int = 8
    MIN_BOARD_SIZE: int = 4
    MAX_BOARD_SIZE: int = 16
    VALID_BOARD_SIZES: Tuple[int, ...] = (4, 6, 8, 10, 12, 14, 16)

    # AI settings
    DEFAULT_AI_DEPTH: int = 4
    MIN_AI_DEPTH: int = 1
    MAX_AI_DEPTH: int = 6
    MAX_TRANSPOSITION_SIZE: int = 10000

    # AI timing
    AI_DELAY_MS: int = 1000  # Delay before AI move (milliseconds)
    AI_VS_AI_DELAY_MS: int = 500  # Faster for AI vs AI

    # Game state
    SAVE_FILE_VERSION: str = "2.0"


@dataclass
class UIConfig:
    """User interface configuration"""

    # Window settings
    DEFAULT_WIDTH: int = 1000
    DEFAULT_HEIGHT: int = 800
    MIN_WIDTH: int = 800
    MIN_HEIGHT: int = 600
    FPS: int = 60

    # Layout
    HUD_HEIGHT: int = 60
    MENU_BAR_HEIGHT: int = 30
    MARGIN: int = 10

    # Visual effects
    GRID_LINE_WIDTH: int = 2
    BORDER_RADIUS: int = 14
    INNER_SHADOW_LAYERS: int = 12
    DISC_SIZE_RATIO: float = 0.42
    SHADOW_OFFSET: int = 3
    SHADOW_RADIUS: int = 3

    # Particles
    CONFETTI_COUNT: int = 10
    CONFETTI_MIN_SPEED: int = 60
    CONFETTI_MAX_SPEED: int = 180
    CONFETTI_MIN_LIFE: float = 0.6
    CONFETTI_MAX_LIFE: float = 1.2
    GRAVITY: int = 180

    # Menu
    MENU_ITEM_HEIGHT: int = 25
    MENU_PADDING: int = 12
    DROPDOWN_WIDTH: int = 150


@dataclass
class FileConfig:
    """File paths and names"""

    SETTINGS_FILE: str = "reversi-settings.json"
    ICON_PNG: str = "reversi-icon.png"
    LOG_FILE: str = "reversi.log"
    SAVE_GAME_EXTENSION: str = ".rsv"


# Color definitions
class Colors:
    """Color constants"""

    # Game pieces
    EMPTY: int = 0
    BLACK: int = 1
    WHITE: int = 2

    # Wood background
    WOOD: Tuple[int, int, int] = (70, 45, 30)
    HINT: Tuple[int, int, int] = (255, 220, 100)
    HOVER: Tuple[int, int, int] = (255, 255, 255)

    # Black disc colors
    BLACK_DISC_BASE: Tuple[int, int, int] = (20, 20, 20)
    BLACK_DISC_HIGHLIGHT: Tuple[int, int, int] = (80, 80, 80)
    BLACK_DISC_RIM: Tuple[int, int, int] = (10, 10, 10)

    # White disc colors
    WHITE_DISC_BASE: Tuple[int, int, int] = (245, 245, 245)
    WHITE_DISC_HIGHLIGHT: Tuple[int, int, int] = (255, 255, 255)
    WHITE_DISC_RIM: Tuple[int, int, int] = (180, 180, 180)


# Theme definitions
THEMES: Dict[str, Dict] = {
    "classic": {
        "name": "classic",
        "display": "Classic Green",
        "felt": (32, 108, 62),
        "grid": (10, 70, 38),
        "hud": (252, 252, 254),
        "text": (40, 40, 45),
        "accent": (70, 130, 235),
        "danger": (235, 70, 70),
    },
    "ocean": {
        "name": "ocean",
        "display": "Ocean Blue",
        "felt": (25, 78, 132),
        "grid": (15, 50, 85),
        "hud": (240, 248, 255),
        "text": (30, 50, 80),
        "accent": (50, 150, 255),
        "danger": (255, 100, 100),
    },
    "sunset": {
        "name": "sunset",
        "display": "Sunset Orange",
        "felt": (156, 78, 25),
        "grid": (120, 50, 15),
        "hud": (255, 248, 240),
        "text": (80, 40, 20),
        "accent": (255, 120, 50),
        "danger": (220, 70, 70),
    },
    "midnight": {
        "name": "midnight",
        "display": "Midnight Dark",
        "felt": (25, 35, 50),
        "grid": (15, 25, 40),
        "hud": (35, 35, 40),
        "text": (220, 220, 230),
        "accent": (120, 180, 255),
        "danger": (255, 120, 120),
    },
    "forest": {
        "name": "forest",
        "display": "Forest Green",
        "felt": (45, 85, 35),
        "grid": (25, 55, 20),
        "hud": (248, 252, 248),
        "text": (30, 60, 25),
        "accent": (80, 160, 70),
        "danger": (200, 80, 80),
    },
}


# Direction vectors for move checking
DIRECTIONS: Tuple[Tuple[int, int], ...] = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


# Logging configuration
@dataclass
class LogConfig:
    """Logging configuration"""

    LOG_LEVEL_CONSOLE: str = "INFO"  # Console log level
    LOG_LEVEL_FILE: str = "DEBUG"  # File log level
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    MAX_LOG_SIZE_MB: int = 10
    LOG_BACKUP_COUNT: int = 3


# Create singleton instances
game_config = GameConfig()
ui_config = UIConfig()
file_config = FileConfig()
log_config = LogConfig()
colors = Colors()
