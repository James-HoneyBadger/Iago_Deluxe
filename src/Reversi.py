#!/usr/bin/env python3
"""
Reversi / Othello - Deluxe Pygame Edition

A polished, feature-rich implementation of the classic Reversi/Othello board game.

Features:
- Clean, modern UI with organized button layout
- Traditional checker-style game pieces with authentic patterns
- Smooth animations and visual effects
- AI opponent with adjustable difficulty (1-6 levels)
- Game state management (save/load, undo/redo)
- Hints system and interactive feedback
- Sound effects and theme customization
- Modular, maintainable code architecture

Technical Features:
- Minimax AI with alpha-beta pruning
- Efficient disc rendering with caching
- Responsive UI with hover effects
- Settings persistence
- Cross-platform compatibility

Dependencies:
    sudo apt-get install python3 python3-pygame
    # Optional for enhanced icon generation:
    pip install Pillow

Usage:
    python3 reversi.py [board_size]

Examples:
    python3 reversi.py      # Uses saved board size (default 8x8)
    python3 reversi.py 6    # 6x6 board
    python3 reversi.py 8    # Standard 8x8 board
    python3 reversi.py 10   # 10x10 board
    python3 reversi.py 16   # Large 16x16 board

Board Size Options: 4x4, 6x6, 8x8, 10x10, 12x12, 14x14, 16x16
Change board size in-game via Game menu → Board Size option

Author: Enhanced and refactored for maintainability
Version: 2.0 - Refactored Edition
"""
from __future__ import annotations
import json
import math
import os
import random
import struct
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Dict

import pygame as pg

# ----------------------------- Core game state ----------------------------- #
EMPTY, BLACK, WHITE = 0, 1, 2
OPP = {BLACK: WHITE, WHITE: BLACK}
NAME = {BLACK: "Black", WHITE: "White"}
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


@dataclass
class Move:
    row: int
    col: int
    flips: List[Tuple[int, int]]


@dataclass
class Board:
    size: int = 8
    grid: List[List[int]] = field(default_factory=list)
    to_move: int = BLACK
    history: List[Tuple[List[List[int]], int]] = field(default_factory=list)
    redo_stack: List[Tuple[List[List[int]], int]] = field(default_factory=list)
    move_list: List[Tuple[int, int, int]] = field(
        default_factory=list
    )  # (color,r,c) pass=>(-1,-1)

    def __post_init__(self):
        if not self.grid:
            self.grid = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
            m = self.size // 2
            self.grid[m - 1][m - 1] = WHITE
            self.grid[m][m] = WHITE
            self.grid[m - 1][m] = BLACK
            self.grid[m][m - 1] = BLACK

    def copy_grid(self):
        return [row[:] for row in self.grid]

    def inside(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def legal_moves(self, color: Optional[int] = None) -> List[Move]:
        """Get all legal moves for the specified color.

        Args:
            color: The player color (BLACK or WHITE). Defaults to current player.

        Returns:
            List of Move objects representing valid moves.
        """
        color = color or self.to_move
        opp = OPP[color]
        out: List[Move] = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != EMPTY:
                    continue
                flips: List[Tuple[int, int]] = []
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    line = []
                    while self.inside(rr, cc) and self.grid[rr][cc] == opp:
                        line.append((rr, cc))
                        rr += dr
                        cc += dc
                    if line and self.inside(rr, cc) and self.grid[rr][cc] == color:
                        flips.extend(line)
                if flips:
                    out.append(Move(r, c, flips))
        return out

    def make_move(self, mv: Move):
        self.history.append((self.copy_grid(), self.to_move))
        self.redo_stack.clear()
        r, c = mv.row, mv.col
        self.grid[r][c] = self.to_move
        for rr, cc in mv.flips:
            self.grid[rr][cc] = self.to_move
        self.move_list.append((self.to_move, r, c))
        self.to_move = OPP[self.to_move]

    def pass_turn(self):
        self.history.append((self.copy_grid(), self.to_move))
        self.redo_stack.clear()
        self.move_list.append((self.to_move, -1, -1))
        self.to_move = OPP[self.to_move]

    def undo(self):
        if not self.history:
            return False
        self.redo_stack.append((self.copy_grid(), self.to_move))
        grid, tomove = self.history.pop()
        self.grid = [row[:] for row in grid]
        self.to_move = tomove
        if self.move_list:
            self.move_list.pop()
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        self.history.append((self.copy_grid(), self.to_move))
        grid, tomove = self.redo_stack.pop()
        self.grid = [row[:] for row in grid]
        self.to_move = tomove
        return True

    def score(self):
        b = sum(cell == BLACK for row in self.grid for cell in row)
        w = sum(cell == WHITE for row in self.grid for cell in row)
        return b, w

    def game_over(self):
        return not self.legal_moves(BLACK) and not self.legal_moves(WHITE)

    def serialize(self):
        return {
            "size": self.size,
            "grid": self.grid,
            "to_move": self.to_move,
            "move_list": self.move_list,
        }

    @staticmethod
    def deserialize(obj: dict) -> "Board":
        b = Board(size=obj.get("size", 8))
        b.grid = [row[:] for row in obj["grid"]]
        b.to_move = obj["to_move"]
        b.move_list = [tuple(x) for x in obj.get("move_list", [])]
        b.history.clear()
        b.redo_stack.clear()
        return b


# ----------------------------- AI ----------------------------------------- #
# Position value tables for different board sizes
PST_TEMPLATES = {
    4: [
        [200, -50, -50, 200],
        [-50, -100, -100, -50],
        [-50, -100, -100, -50],
        [200, -50, -50, 200],
    ],
    6: [
        [120, -20, 20, 20, -20, 120],
        [-20, -40, -5, -5, -40, -20],
        [20, -5, 15, 15, -5, 20],
        [20, -5, 15, 15, -5, 20],
        [-20, -40, -5, -5, -40, -20],
        [120, -20, 20, 20, -20, 120],
    ],
    8: [
        [120, -20, 20, 5, 5, 20, -20, 120],
        [-20, -40, -5, -5, -5, -5, -40, -20],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [-20, -40, -5, -5, -5, -5, -40, -20],
        [120, -20, 20, 5, 5, 20, -20, 120],
    ],
    10: [
        [150, -25, 25, 10, 5, 5, 10, 25, -25, 150],
        [-25, -50, -8, -8, -8, -8, -8, -8, -50, -25],
        [25, -8, 20, 5, 3, 3, 5, 20, -8, 25],
        [10, -8, 5, 5, 3, 3, 5, 5, -8, 10],
        [5, -8, 3, 3, 3, 3, 3, 3, -8, 5],
        [5, -8, 3, 3, 3, 3, 3, 3, -8, 5],
        [10, -8, 5, 5, 3, 3, 5, 5, -8, 10],
        [25, -8, 20, 5, 3, 3, 5, 20, -8, 25],
        [-25, -50, -8, -8, -8, -8, -8, -8, -50, -25],
        [150, -25, 25, 10, 5, 5, 10, 25, -25, 150],
    ],
    12: [
        [180, -30, 30, 15, 8, 5, 5, 8, 15, 30, -30, 180],
        [-30, -60, -10, -10, -10, -8, -8, -10, -10, -10, -60, -30],
        [30, -10, 25, 8, 5, 3, 3, 5, 8, 25, -10, 30],
        [15, -10, 8, 8, 5, 3, 3, 5, 8, 8, -10, 15],
        [8, -10, 5, 5, 3, 3, 3, 3, 5, 5, -10, 8],
        [5, -8, 3, 3, 3, 3, 3, 3, 3, 3, -8, 5],
        [5, -8, 3, 3, 3, 3, 3, 3, 3, 3, -8, 5],
        [8, -10, 5, 5, 3, 3, 3, 3, 5, 5, -10, 8],
        [15, -10, 8, 8, 5, 3, 3, 5, 8, 8, -10, 15],
        [30, -10, 25, 8, 5, 3, 3, 5, 8, 25, -10, 30],
        [-30, -60, -10, -10, -10, -8, -8, -10, -10, -10, -60, -30],
        [180, -30, 30, 15, 8, 5, 5, 8, 15, 30, -30, 180],
    ],
}


class AI:
    """Enhanced AI with improved evaluation, move ordering, and adaptive strategies"""

    def __init__(self, max_depth: int = 4, rng: Optional[random.Random] = None):
        self.max_depth = max_depth
        self.rng = rng or random.Random()
        self.transposition_table = {}
        self.nodes_searched = 0

    def get_pst(self, board_size: int):
        """Get position-specific table for board size"""
        if board_size in PST_TEMPLATES:
            return PST_TEMPLATES[board_size]

        # Generate dynamic PST for other sizes
        pst = []
        for r in range(board_size):
            row = []
            for c in range(board_size):
                # Corners are extremely valuable
                if (r == 0 or r == board_size - 1) and (c == 0 or c == board_size - 1):
                    value = 150
                # Squares adjacent to corners are dangerous
                elif (
                    (r == 0 or r == board_size - 1) and (c == 1 or c == board_size - 2)
                ) or (
                    (c == 0 or c == board_size - 1) and (r == 1 or r == board_size - 2)
                ):
                    value = -40
                # Diagonal squares next to corners are also risky
                elif (
                    (r == 1 and c == 1)
                    or (r == 1 and c == board_size - 2)
                    or (r == board_size - 2 and c == 1)
                    or (r == board_size - 2 and c == board_size - 2)
                ):
                    value = -20
                # Other edge squares are good
                elif r == 0 or r == board_size - 1 or c == 0 or c == board_size - 1:
                    value = 25
                # Interior squares - value based on distance from center
                else:
                    center = board_size // 2
                    dist_from_center = max(abs(r - center), abs(c - center))
                    value = max(0, 10 - dist_from_center * 2)
                row.append(value)
            pst.append(row)
        return pst

    def evaluate(self, board: Board, color: int) -> int:
        """Enhanced evaluation function with multiple strategic factors"""
        b_count, w_count = board.score()
        total_pieces = b_count + w_count
        max_pieces = board.size * board.size
        game_phase = total_pieces / max_pieces  # 0 = opening, 1 = endgame

        # Material advantage
        material = (b_count - w_count) if color == BLACK else (w_count - b_count)

        # Mobility (legal moves available)
        my_moves = len(board.legal_moves(color))
        opp_moves = len(board.legal_moves(OPP[color]))
        mobility = my_moves - opp_moves

        # Positional evaluation using PST
        pst = self.get_pst(board.size)
        positional = 0
        corner_count = 0

        for r in range(board.size):
            for c in range(board.size):
                piece = board.grid[r][c]
                if piece != EMPTY:
                    value = pst[r][c] if r < len(pst) and c < len(pst[0]) else 0
                    if piece == color:
                        positional += value
                        if self.is_corner(r, c, board.size):
                            corner_count += 1
                    else:
                        positional -= value
                        if self.is_corner(r, c, board.size):
                            corner_count -= 1

        # Frontier discs (pieces adjacent to empty squares - generally bad)
        frontier_penalty = self.count_frontier_discs(board, color)

        # Phase-based evaluation weights
        if game_phase < 0.25:  # Early game - focus on mobility and position
            score = (
                positional * 4
                + mobility * 15
                + corner_count * 100
                - frontier_penalty * 2
            )
        elif game_phase < 0.75:  # Mid game - balanced approach
            score = (
                positional * 3
                + mobility * 8
                + corner_count * 150
                + material * 5
                - frontier_penalty
            )
        else:  # End game - material is king
            score = material * 100 + corner_count * 50 + positional

        return int(score)

    def is_corner(self, r: int, c: int, size: int) -> bool:
        """Check if position is a corner"""
        return (r == 0 or r == size - 1) and (c == 0 or c == size - 1)

    def count_frontier_discs(self, board: Board, color: int) -> int:
        """Count frontier discs (pieces next to empty squares)"""
        frontier = 0
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for r in range(board.size):
            for c in range(board.size):
                if board.grid[r][c] == color:
                    # Check if adjacent to empty square
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < board.size and 0 <= nc < board.size:
                            if board.grid[nr][nc] == EMPTY:
                                frontier += 1
                                break
        return frontier

    def choose(self, board: Board, color: int) -> Optional[Move]:
        """Choose best move using enhanced minimax with optimizations"""
        moves = board.legal_moves(color)
        if not moves:
            return None

        # Adaptive depth based on game state
        total_pieces = sum(board.score())
        max_pieces = board.size * board.size
        game_phase = total_pieces / max_pieces
        move_count = len(moves)

        # Increase depth in endgame or when few moves available
        adaptive_depth = self.max_depth
        if game_phase > 0.8 or move_count <= 4:
            adaptive_depth = min(self.max_depth + 2, 8)
        elif move_count > 15:  # Many moves - reduce depth to avoid timeout
            adaptive_depth = max(self.max_depth - 1, 3)

        # Clear search state
        self.nodes_searched = 0
        if len(self.transposition_table) > 10000:  # Prevent memory bloat
            self.transposition_table.clear()

        # Evaluate all moves
        best_score = -float("inf")
        best_moves = []
        alpha = -float("inf")
        beta = float("inf")

        # Enhanced move ordering for better pruning
        scored_moves = []
        for move in moves:
            quick_score = self.quick_move_eval(board, move, color)
            scored_moves.append((quick_score, move))
        scored_moves.sort(key=lambda x: x[0], reverse=True)

        for _, move in scored_moves:
            board_copy = Board.deserialize(board.serialize())
            board_copy.to_move = color
            board_copy.make_move(move)

            score = -self.search(
                board_copy, adaptive_depth - 1, -beta, -alpha, OPP[color]
            )

            if score > best_score:
                best_score = score
                best_moves = [move]
                alpha = max(alpha, score)
            elif score == best_score:
                best_moves.append(move)

        return self.rng.choice(best_moves) if best_moves else moves[0]

    def quick_move_eval(self, board: Board, move: Move, color: int) -> int:
        """Quick heuristic evaluation for move ordering"""
        pst = self.get_pst(board.size)
        r, c = move.row, move.col

        # Position value
        score = pst[r][c] if r < len(pst) and c < len(pst[0]) else 0

        # Pieces captured
        score += len(move.flips) * 10

        # Corner bonus
        if self.is_corner(r, c, board.size):
            score += 2000

        # Avoid dangerous squares (adjacent to corners)
        elif self.is_dangerous_square(r, c, board.size, board):
            score -= 500

        return score

    def is_dangerous_square(self, r: int, c: int, size: int, board: Board) -> bool:
        """Check if square gives opponent corner access"""
        corners = [(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)]

        for corner_r, corner_c in corners:
            # Skip if corner is already occupied
            if board.grid[corner_r][corner_c] != EMPTY:
                continue

            # Check if this move is adjacent to an empty corner
            if (
                abs(r - corner_r) <= 1
                and abs(c - corner_c) <= 1
                and (r != corner_r or c != corner_c)
            ):
                return True
        return False

    def search(
        self, board: Board, depth: int, alpha: float, beta: float, color: int
    ) -> float:
        """Enhanced minimax search with optimizations"""
        self.nodes_searched += 1

        # Terminal node evaluation
        if depth <= 0 or board.game_over():
            return self.evaluate(board, color)

        # Transposition table lookup (use string representation as key)
        board_key = str(board.serialize())
        if board_key in self.transposition_table:
            cached_depth, cached_score = self.transposition_table[board_key]
            if cached_depth >= depth:
                return cached_score

        moves = board.legal_moves(color)
        if not moves:
            # No legal moves - must pass
            if not board.legal_moves(OPP[color]):
                # Game over - return final evaluation
                b, w = board.score()
                if color == BLACK:
                    return 100000 if b > w else (-100000 if w > b else 0)
                else:
                    return 100000 if w > b else (-100000 if b > w else 0)
            # Pass turn to opponent
            return -self.search(board, depth - 1, -beta, -alpha, OPP[color])

        # Move ordering for better alpha-beta pruning
        if depth > 2:  # Only sort for deeper searches to save time
            scored_moves = [
                (self.quick_move_eval(board, move, color), move) for move in moves
            ]
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            moves = [move for _, move in scored_moves]

        best_value = -float("inf")
        for move in moves:
            board_copy = Board.deserialize(board.serialize())
            board_copy.to_move = color
            board_copy.make_move(move)

            value = -self.search(board_copy, depth - 1, -beta, -alpha, OPP[color])
            best_value = max(best_value, value)
            alpha = max(alpha, value)

            if alpha >= beta:
                break  # Alpha-beta pruning

        # Cache result
        self.transposition_table[board_key] = (depth, best_value)
        return best_value


# ----------------------------- Settings & SFX ------------------------------ #
SETTINGS_FILE = "config/reversi-settings.json"
ICON_PNG = "assets/reversi-icon.png"


@dataclass
class Settings:
    theme: str = "classic"  # classic / midnight
    sound: bool = True
    hints: bool = True
    ai_black: bool = False
    ai_white: bool = True
    ai_depth: int = 4
    board_size: int = 8
    stats: Optional[PlayerStats] = None
    # New visual settings
    show_grid: bool = True
    piece_style: str = "traditional"  # traditional, modern, emoji
    font_size_multiplier: float = 1.0  # 0.8 to 1.5
    zoom_level: float = 1.0  # 0.5 to 2.0
    board_rotation: int = 0  # 0, 90, 180, 270 degrees
    show_move_preview: bool = True
    show_hint_intensity: bool = True
    per_difficulty_stats: Optional[Dict[int, PlayerStats]] = None

    def __post_init__(self):
        if self.stats is None:
            self.stats = PlayerStats()
        if self.per_difficulty_stats is None:
            self.per_difficulty_stats = {}
            for depth in range(1, 7):
                self.per_difficulty_stats[depth] = PlayerStats()

    @staticmethod
    def load() -> "Settings":
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            # Handle stats data specially since it's a complex object
            stats_data = d.pop("stats", None)
            per_diff_stats_data = d.pop("per_difficulty_stats", None)

            # Remove deprecated time control fields
            deprecated_fields = ["time_enabled", "time_limit", "time_increment"]
            for fld in deprecated_fields:
                d.pop(fld, None)

            settings = Settings(**d)
            if stats_data:
                # Convert recent_results back to GameResult objects
                recent_results = []
                for result_data in stats_data.get("recent_results", []):
                    recent_results.append(GameResult(**result_data))
                stats_data["recent_results"] = recent_results
                settings.stats = PlayerStats(**stats_data)

            if per_diff_stats_data:
                # Convert per-difficulty stats
                settings.per_difficulty_stats = {}
                for depth_str, pds_data in per_diff_stats_data.items():
                    recent_results = []
                    for result_data in pds_data.get("recent_results", []):
                        recent_results.append(GameResult(**result_data))
                    pds_data["recent_results"] = recent_results
                    settings.per_difficulty_stats[int(depth_str)] = PlayerStats(
                        **pds_data
                    )

            return settings
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return Settings()

    def save(self):
        try:
            # Convert to dict manually to handle complex objects
            data = self.__dict__.copy()
            if self.stats:
                # Convert stats to serializable format
                stats_dict = self.stats.__dict__.copy()
                # Convert GameResult objects to dicts
                stats_dict["recent_results"] = [
                    result.__dict__ for result in self.stats.recent_results
                ]
                data["stats"] = stats_dict

            if self.per_difficulty_stats:
                # Convert per-difficulty stats to serializable format
                per_diff_dict = {}
                for depth, pds in self.per_difficulty_stats.items():
                    pds_dict = pds.__dict__.copy()
                    pds_dict["recent_results"] = [
                        result.__dict__ for result in pds.recent_results
                    ]
                    per_diff_dict[str(depth)] = pds_dict
                data["per_difficulty_stats"] = per_diff_dict

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except (PermissionError, OSError, ValueError) as e:
            print(f"Warning: Could not save settings: {e}")


class SFX:
    def __init__(self, enabled=True):
        self.enabled = enabled
        try:
            pg.mixer.init()
        except (pg.error, OSError):
            self.enabled = False
            return
        self.sounds = {
            "place": self.tone(440, 0.06),
            "flip": self.tone(660, 0.04),
            "pass": self.tone(300, 0.12),
            "bad": self.tone(110, 0.18),
            "win": self.chord([523, 659, 783], 0.35),
        }

    def play(self, key: str):
        if self.enabled and key in self.sounds:
            self.sounds[key].play()

    def tone(self, freq, dur):
        rate = 22050
        n = int(rate * dur)
        buf = bytearray()
        for i in range(n):
            t = i / rate
            val = int(32767 * 0.4 * math.sin(2 * math.pi * freq * t))
            buf += struct.pack("<h", val)
        snd = pg.mixer.Sound(buffer=bytes(buf))
        return snd

    def chord(self, freqs, dur):
        rate = 22050
        n = int(rate * dur)
        buf = bytearray()
        for i in range(n):
            t = i / rate
            v = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
            val = int(32767 * 0.35 * v)
            buf += struct.pack("<h", val)
        return pg.mixer.Sound(buffer=bytes(buf))


# ----------------------------- Visual constants ---------------------------- #
W, H = 1024, 720
MARGIN = 30
HUD_HEIGHT = 60  # Clean header with proper spacing
MENU_BAR_HEIGHT = 30
GRID_LINE_WIDTH = 2
BORDER_RADIUS = 14
INNER_SHADOW_LAYERS = 12

# Game piece constants
DISC_SIZE_RATIO = 0.42
SHADOW_OFFSET = 3
SHADOW_RADIUS = 3

# Animation constants
CONFETTI_COUNT = 10
CONFETTI_MIN_SPEED = 60
CONFETTI_MAX_SPEED = 180
CONFETTI_MIN_LIFE = 0.6
CONFETTI_MAX_LIFE = 1.2
GRAVITY = 180

# Menu constants
MENU_ITEM_HEIGHT = 25
MENU_PADDING = 12
DROPDOWN_WIDTH = 180

THEMES = {
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
    "colorblind_friendly": {
        "name": "colorblind_friendly",
        "display": "Colorblind (Blue/Orange)",
        "felt": (65, 90, 120),
        "grid": (40, 60, 85),
        "hud": (245, 245, 250),
        "text": (30, 30, 40),
        "accent": (230, 140, 30),  # Orange
        "danger": (200, 60, 60),
    },
    "high_contrast": {
        "name": "high_contrast",
        "display": "High Contrast",
        "felt": (0, 0, 0),
        "grid": (255, 255, 255),
        "hud": (255, 255, 255),
        "text": (0, 0, 0),
        "accent": (0, 120, 255),
        "danger": (255, 0, 0),
    },
}
WOOD = (70, 45, 30)
HINT = (255, 220, 100)  # Warmer, more visible hint color
HOVER = (255, 255, 255)

# Traditional checker piece colors
BLACK_DISC_BASE = (20, 20, 20)  # Solid black
BLACK_DISC_HIGHLIGHT = (80, 80, 80)
BLACK_DISC_RIM = (10, 10, 10)

WHITE_DISC_BASE = (245, 245, 245)  # Solid white
WHITE_DISC_HIGHLIGHT = (255, 255, 255)
WHITE_DISC_RIM = (180, 180, 180)


# ----------------------------- UI & Game ---------------------------------- #
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    age: float
    color_id: int


@dataclass
class MenuItem:
    label: str
    handler: Callable[[], None]
    enabled: bool = True
    submenu: Optional[List["MenuItem"]] = None


@dataclass
class Menu:
    title: str
    items: List[MenuItem]
    rect: pg.Rect = field(default_factory=lambda: pg.Rect(0, 0, 0, 0))
    is_open: bool = False


@dataclass
class FlipAnimation:
    row: int
    col: int
    start_time: float
    duration: float = 0.3
    from_color: int = BLACK
    to_color: int = WHITE


@dataclass
class MoveHistoryEntry:
    move_number: int
    player: int  # BLACK or WHITE
    row: int
    col: int
    pieces_flipped: int
    board_state: Optional[List[List[int]]] = None  # For replay functionality


@dataclass
class MoveAnalysis:
    move_number: int
    player: int
    row: int
    col: int
    pieces_captured: int
    board_control_before: float  # Percentage of board controlled
    board_control_after: float
    corner_moves: int  # Number of corners controlled after move
    edge_moves: int  # Number of edge pieces after move
    mobility_change: int  # Change in available moves
    move_quality: str  # "Excellent", "Good", "Fair", "Poor"


class MoveAnalysisDisplay:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.current_analysis = None
        self.scroll_offset = 0

    def show_analysis(self, move_analysis: MoveAnalysis):
        """Show move analysis window"""
        self.active = True
        self.current_analysis = move_analysis
        self.scroll_offset = 0

    def hide_analysis(self):
        """Hide move analysis window"""
        self.active = False
        self.current_analysis = None

    def handle_scroll(self, delta):
        """Handle scrolling in the analysis window"""
        if self.active:
            self.scroll_offset = max(0, self.scroll_offset + delta * 20)

    def draw(self, screen, theme):
        """Draw the move analysis window"""
        if not self.active or not self.current_analysis:
            return

        analysis = self.current_analysis

        # Get board layout to position window to the right
        board_rect, hud_rect, cell = self.game.layout()

        # Window dimensions and position (to the right of the board)
        window_width = 350
        window_height = min(400, screen.get_height() - hud_rect.height - 40)

        # Position to the right of the board with some margin
        margin = 20
        window_x = board_rect.right + margin
        window_y = board_rect.top

        # If there's not enough space on the right, position on the left
        if window_x + window_width > screen.get_width() - margin:
            window_x = max(margin, board_rect.left - window_width - margin)

        # Draw window background
        window_rect = pg.Rect(window_x, window_y, window_width, window_height)
        pg.draw.rect(screen, theme["hud"], window_rect)
        pg.draw.rect(screen, theme["grid"], window_rect, 2)

        # Title bar
        title_rect = pg.Rect(window_x, window_y, window_width, 30)
        pg.draw.rect(screen, theme["grid"], title_rect)

        # Title text
        font = pg.font.Font(None, 24)
        player_name = "Black" if analysis.player == 1 else "White"
        move_pos = f"{analysis.row + 1}{chr(ord('A') + analysis.col)}"
        title = f"Move Analysis: {player_name} {move_pos}"
        title_surface = font.render(title, True, theme["text"])
        screen.blit(title_surface, (window_x + 10, window_y + 5))

        # Close button
        close_rect = pg.Rect(window_x + window_width - 25, window_y + 5, 20, 20)
        pg.draw.rect(screen, (200, 50, 50), close_rect)
        close_text = font.render("×", True, (255, 255, 255))
        screen.blit(close_text, (window_x + window_width - 20, window_y + 3))

        # Content area
        content_y = window_y + 35
        content_height = window_height - 40
        line_height = 20
        font_small = pg.font.Font(None, 18)

        # Analysis content
        lines = [
            f"Move Quality: {analysis.move_quality}",
            f"Pieces Captured: {analysis.pieces_captured}",
            "",
            f"Board Control Before: {analysis.board_control_before:.1f}%",
            f"Board Control After: {analysis.board_control_after:.1f}%",
            (
                f"Control Change: "
                f"{analysis.board_control_after - analysis.board_control_before:+.1f}%"
            ),
            "",
            f"Corners Controlled: {analysis.corner_moves}",
            f"Edge Pieces: {analysis.edge_moves}",
            f"Mobility Change: {analysis.mobility_change:+d}",
            "",
            "Quality Rating:",
            "• Excellent: Outstanding strategic move",
            "• Good: Solid choice with clear benefits",
            "• Fair: Reasonable but not optimal",
            "• Poor: Weak move, better options available",
        ]

        # Draw content with scrolling
        y = content_y - self.scroll_offset
        for line in lines:
            if y > content_y + content_height:
                break
            if y >= content_y - line_height:
                if line.startswith("Move Quality:"):
                    # Highlight move quality
                    color = {
                        "Excellent": (50, 200, 50),
                        "Good": (100, 150, 100),
                        "Fair": (200, 200, 100),
                        "Poor": (200, 100, 100),
                    }.get(analysis.move_quality, theme["text"] or (255, 255, 255))
                elif line.startswith("Control Change:"):
                    # Color control change based on positive/negative
                    change = (
                        analysis.board_control_after - analysis.board_control_before
                    )
                    color = (
                        (100, 200, 100)
                        if change > 0
                        else (200, 100, 100) if change < 0 else theme["text"]
                    )
                else:
                    color = theme["text"]

                text_surface = font_small.render(line, True, color)
                screen.blit(text_surface, (window_x + 10, y))
            y += line_height

    def handle_click(self, pos):
        """Handle clicks in the move analysis window"""
        if not self.active:
            return False

        # Use same positioning logic as draw method
        screen = pg.display.get_surface()
        board_rect, hud_rect, cell = self.game.layout()

        # Window dimensions and position (to the right of the board)
        window_width = 350
        window_height = min(400, screen.get_height() - hud_rect.height - 40)

        # Position to the right of the board with some margin
        margin = 20
        window_x = board_rect.right + margin
        window_y = board_rect.top

        # If there's not enough space on the right, position on the left
        if window_x + window_width > screen.get_width() - margin:
            window_x = max(margin, board_rect.left - window_width - margin)

        close_rect = pg.Rect(window_x + window_width - 25, window_y + 5, 20, 20)
        if close_rect.collidepoint(pos):
            self.hide_analysis()
            return True

        # Check if click is within window (consume event)
        window_rect = pg.Rect(window_x, window_y, window_width, window_height)
        return window_rect.collidepoint(pos)


@dataclass
class GameResult:
    timestamp: float
    board_size: int
    human_color: int  # BLACK or WHITE
    ai_color: int
    winner: int  # BLACK, WHITE, or EMPTY for tie
    final_score_human: int
    final_score_ai: int
    total_moves: int
    game_duration: float  # in seconds
    ai_depth: int
    move_analysis: List[MoveAnalysis] = field(default_factory=list)
    opening_type: str = "Standard"  # "Standard", "Diagonal", "Parallel"
    endgame_performance: float = 0.0  # How well player did in endgame (0-1)
    strategic_mistakes: int = 0  # Number of major strategic errors


@dataclass
class PlayerStats:
    games_played: int = 0
    games_won: int = 0
    games_lost: int = 0
    games_tied: int = 0
    total_moves: int = 0
    total_time: float = 0.0
    best_score: int = 0
    average_score: float = 0.0
    average_game_length: float = 0.0
    recent_results: List[GameResult] = field(default_factory=list)  # Last 10 games

    @property
    def win_rate(self) -> float:
        return self.games_won / max(1, self.games_played)

    @property
    def average_moves_per_game(self) -> float:
        return self.total_moves / max(1, self.games_played)

    def add_game_result(self, result: GameResult):
        self.games_played += 1
        self.total_moves += result.total_moves
        self.total_time += result.game_duration

        if result.winner == result.human_color:
            self.games_won += 1
            self.best_score = max(self.best_score, result.final_score_human)
        elif result.winner == result.ai_color:
            self.games_lost += 1
        else:
            self.games_tied += 1

        # Update averages
        self.average_score = (
            self.average_score * (self.games_played - 1) + result.final_score_human
        ) / self.games_played
        self.average_game_length = self.total_time / self.games_played

        # Keep only last 10 games for recent results
        self.recent_results.append(result)
        if len(self.recent_results) > 10:
            self.recent_results.pop(0)


@dataclass
class TutorialStep:
    title: str
    description: str
    board_highlight: Optional[List[Tuple[int, int]]] = None  # Squares to highlight
    move_suggestion: Optional[Tuple[int, int]] = None  # Suggested move
    explanation: str = ""  # Detailed explanation


class StrategyTutorial:
    """Interactive strategy tutorial system"""

    def __init__(self):
        self.current_step = 0
        self.active = False
        self.steps = [
            TutorialStep(
                title="Corner Strategy",
                description=(
                    "Corners are the most valuable squares - "
                    "they can never be flipped!"
                ),
                board_highlight=[(0, 0), (0, 7), (7, 0), (7, 7)],
                explanation=(
                    "Always try to capture corners when possible. "
                    "They provide permanent control."
                ),
            ),
            TutorialStep(
                title="Edge Control",
                description=(
                    "Edges are also valuable - "
                    "they're harder to flip than center squares."
                ),
                board_highlight=[
                    (0, 1),
                    (0, 2),
                    (1, 0),
                    (2, 0),
                    (0, 5),
                    (0, 6),
                    (5, 0),
                    (6, 0),
                ],
                explanation=(
                    "Control edges to limit your opponent's options "
                    "and build stable positions."
                ),
            ),
            TutorialStep(
                title="Avoid C and X Squares",
                description=(
                    "These squares next to corners often give "
                    "your opponent corner access!"
                ),
                board_highlight=[(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7)],
                explanation=(
                    "Be very careful about playing adjacent to corners - "
                    "it often backfires."
                ),
            ),
            TutorialStep(
                title="Mobility Strategy",
                description=(
                    "Sometimes having fewer pieces gives you " "more move options!"
                ),
                explanation=(
                    "Don't always grab the most pieces. "
                    "Focus on maintaining good move options."
                ),
            ),
            TutorialStep(
                title="Endgame Technique",
                description=(
                    "In the endgame, count carefully and "
                    "force your opponent into bad moves."
                ),
                explanation=(
                    "Practice counting ahead and calculating "
                    "the final score before the game ends."
                ),
            ),
        ]

    def start_tutorial(self):
        """Start the interactive tutorial"""
        self.active = True
        self.current_step = 0

    def next_step(self):
        """Move to next tutorial step"""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            return True
        else:
            self.active = False
            return False

    def get_current_step(self) -> Optional[TutorialStep]:
        """Get current tutorial step"""
        if self.active and 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None


class GameplayAnalyzer:
    """Analyzes player moves and provides strategic feedback"""

    def __init__(self):
        self.move_history = []

    def analyze_move(self, board: Board, move: Move, player: int) -> MoveAnalysis:
        """Analyze a single move for strategic value"""
        r, c = move.row, move.col
        pieces_captured = len(move.flips)

        # Calculate board control
        before_control = self._calculate_board_control(board, player)

        # Simulate the move
        temp_board = Board.deserialize(board.serialize())
        temp_board.to_move = player
        temp_board.make_move(move)

        after_control = self._calculate_board_control(temp_board, player)

        # Count strategic positions
        corner_moves = self._count_corners(temp_board, player)
        edge_moves = self._count_edges(temp_board, player)

        # Calculate mobility change
        mobility_before = len(board.legal_moves(player))
        mobility_after = len(temp_board.legal_moves(player))
        mobility_change = mobility_after - mobility_before

        # Determine move quality
        move_quality = self._evaluate_move_quality(
            r, c, pieces_captured, corner_moves, mobility_change, board.size
        )

        return MoveAnalysis(
            move_number=len(self.move_history) + 1,
            player=player,
            row=r,
            col=c,
            pieces_captured=pieces_captured,
            board_control_before=before_control,
            board_control_after=after_control,
            corner_moves=corner_moves,
            edge_moves=edge_moves,
            mobility_change=mobility_change,
            move_quality=move_quality,
        )

    def _calculate_board_control(self, board: Board, player: int) -> float:
        """Calculate percentage of board controlled by player"""
        player_pieces = sum(row.count(player) for row in board.grid)
        total_pieces = sum(row.count(BLACK) + row.count(WHITE) for row in board.grid)
        return (player_pieces / max(1, total_pieces)) * 100

    def _count_corners(self, board: Board, player: int) -> int:
        """Count corners controlled by player"""
        corners = [
            (0, 0),
            (0, board.size - 1),
            (board.size - 1, 0),
            (board.size - 1, board.size - 1),
        ]
        return sum(1 for r, c in corners if board.grid[r][c] == player)

    def _count_edges(self, board: Board, player: int) -> int:
        """Count edge pieces controlled by player"""
        count = 0
        size = board.size
        for r in range(size):
            for c in range(size):
                if board.grid[r][c] == player:
                    if r == 0 or r == size - 1 or c == 0 or c == size - 1:
                        count += 1
        return count

    def _evaluate_move_quality(
        self,
        r: int,
        c: int,
        pieces_captured: int,
        corners: int,
        mobility: int,
        board_size: int,
    ) -> str:
        """Evaluate the strategic quality of a move"""
        # Corner move is always excellent
        if (r == 0 or r == board_size - 1) and (c == 0 or c == board_size - 1):
            return "Excellent"

        # Adjacent to corner is usually poor (unless corner is already taken)
        corner_adjacent = [
            (0, 1),
            (1, 0),
            (1, 1),  # Top-left corner adjacents
            (0, board_size - 2),
            (1, board_size - 1),
            (1, board_size - 2),  # Top-right
            (board_size - 2, 0),
            (board_size - 1, 1),
            (board_size - 2, 1),  # Bottom-left
            (board_size - 2, board_size - 1),
            (board_size - 1, board_size - 2),
            (board_size - 2, board_size - 2),  # Bottom-right
        ]
        if (r, c) in corner_adjacent:
            return "Poor"

        # Edge moves are generally good
        if r == 0 or r == board_size - 1 or c == 0 or c == board_size - 1:
            return "Good"

        # Evaluate based on pieces captured and mobility
        if pieces_captured >= 6 and mobility >= 0:
            return "Good"
        elif pieces_captured >= 3 and mobility >= -1:
            return "Fair"
        else:
            return "Fair"


@dataclass
class UIState:
    status: str = ""
    last_save: Optional[str] = None
    last_move: Optional[Tuple[int, int]] = None
    particles: List[Particle] = field(default_factory=list)
    flip_animations: List[FlipAnimation] = field(default_factory=list)
    move_history: List[MoveHistoryEntry] = field(default_factory=list)
    last_move_analysis: Optional["MoveAnalysis"] = None
    history_scroll: int = 0
    game_start_time: Optional[float] = None
    game_end_time: Optional[float] = None
    show_stats: bool = False
    show_tutorial: bool = False
    show_analytics: bool = False
    show_game_analysis: bool = False
    show_move_analysis: bool = False
    tutorial: StrategyTutorial = field(default_factory=StrategyTutorial)
    analyzer: GameplayAnalyzer = field(default_factory=GameplayAnalyzer)
    # New replay mode fields
    replay_mode: bool = False
    replay_index: int = 0
    replay_playing: bool = False
    replay_speed: float = 1.0  # Moves per second
    replay_last_step: float = 0.0
    # AI thinking indicator
    ai_thinking: bool = False
    ai_think_start: float = 0.0
    # Move preview
    hover_pos: Optional[Tuple[int, int]] = None


class MenuSystem:
    """Clean menu system for the game with keyboard navigation"""

    def __init__(self, game):
        self.game = game
        self.menus: List[Menu] = []
        self.active_menu: Optional[Menu] = None
        self.selected_menu_index: int = 0  # For keyboard navigation
        self.selected_item_index: int = 0  # For dropdown navigation
        self.active_submenu_items: Optional[List[MenuItem]] = None
        self.selected_submenu_index: int = 0
        self.font = pg.font.SysFont("Arial", 14)
        self.setup_menus()

    def setup_menus(self):
        """Create the menu structure"""
        # Game menu
        game_items = [
            MenuItem("New Game", self.game.on_new),
            MenuItem(
                f"Board Size ({self.game.board.size}×{self.game.board.size})",
                self.game.on_cycle_board_size,
            ),
            MenuItem("Undo Move", self.game.on_undo),
            MenuItem("Redo Move", self.game.on_redo),
            MenuItem("Save Game", self.game.on_save),
            MenuItem("Load Game", self.game.on_load),
            MenuItem("Export PGN", self.game.on_export_pgn),
            MenuItem("Export JSON", self.game.on_export_json),
        ]

        # AI menu with submenu for difficulty levels
        ai_level_submenu = [
            MenuItem("Level 1 - Beginner", lambda: self.game.set_ai_depth(1)),
            MenuItem("Level 2 - Easy", lambda: self.game.set_ai_depth(2)),
            MenuItem("Level 3 - Medium", lambda: self.game.set_ai_depth(3)),
            MenuItem("Level 4 - Hard", lambda: self.game.set_ai_depth(4)),
            MenuItem("Level 5 - Expert", lambda: self.game.set_ai_depth(5)),
            MenuItem("Level 6 - Master", lambda: self.game.set_ai_depth(6)),
        ]

        black_player = "AI" if self.game.settings.ai_black else "Human"
        white_player = "AI" if self.game.settings.ai_white else "Human"
        hints_status = "✓" if self.game.hint_system.show_hints else " "

        ai_items = [
            MenuItem(
                f"Black Player: {black_player}",
                self.game.on_toggle_ai_black,
            ),
            MenuItem(
                f"White Player: {white_player}",
                self.game.on_toggle_ai_white,
            ),
            MenuItem(
                f"AI Difficulty (Level {self.game.settings.ai_depth})",
                None,
                submenu=ai_level_submenu,
            ),
            MenuItem(
                f"[{hints_status}] Show Hints",
                self.game.on_toggle_move_hints,
            ),
        ]

        # View menu with submenu for themes
        theme_submenu = [
            MenuItem(
                THEMES["classic"]["display"],
                lambda: self.game.set_theme("classic"),
            ),
            MenuItem(
                THEMES["ocean"]["display"],
                lambda: self.game.set_theme("ocean"),
            ),
            MenuItem(
                THEMES["sunset"]["display"],
                lambda: self.game.set_theme("sunset"),
            ),
            MenuItem(
                THEMES["midnight"]["display"],
                lambda: self.game.set_theme("midnight"),
            ),
            MenuItem(
                THEMES["forest"]["display"],
                lambda: self.game.set_theme("forest"),
            ),
            MenuItem(
                THEMES["colorblind_friendly"]["display"],
                lambda: self.game.set_theme("colorblind_friendly"),
            ),
            MenuItem(
                THEMES["high_contrast"]["display"],
                lambda: self.game.set_theme("high_contrast"),
            ),
        ]

        font_size_submenu = [
            MenuItem("Small", lambda: self.game.set_font_size(0.8)),
            MenuItem("Normal", lambda: self.game.set_font_size(1.0)),
            MenuItem("Large", lambda: self.game.set_font_size(1.2)),
            MenuItem("Extra Large", lambda: self.game.set_font_size(1.5)),
        ]

        piece_style_submenu = [
            MenuItem("Traditional", lambda: self.game.set_piece_style("traditional")),
            MenuItem("Modern", lambda: self.game.set_piece_style("modern")),
            MenuItem("Emoji", lambda: self.game.set_piece_style("emoji")),
        ]

        # Format current theme name nicely
        current_theme = THEMES[self.game.settings.theme]["display"]
        font_pct = int(self.game.settings.font_size_multiplier * 100)
        grid_status = "✓" if self.game.settings.show_grid else " "
        preview_status = "✓" if self.game.settings.show_move_preview else " "
        sound_status = "✓" if self.game.settings.sound else " "

        view_items = [
            MenuItem(
                f"Theme: {current_theme}",
                None,
                submenu=theme_submenu,
            ),
            MenuItem(
                f"Font Size ({font_pct}%)",
                None,
                submenu=font_size_submenu,
            ),
            MenuItem(
                f"Piece Style: {self.game.settings.piece_style.title()}",
                None,
                submenu=piece_style_submenu,
            ),
            MenuItem(
                f"[{grid_status}] Show Grid",
                self.game.on_toggle_grid,
            ),
            MenuItem(
                f"[{preview_status}] Move Preview",
                self.game.on_toggle_move_preview,
            ),
            MenuItem(
                f"[{sound_status}] Sound Effects",
                self.game.on_toggle_sound,
            ),
        ]

        # Help menu
        help_items = [
            MenuItem("Strategy Tutorial", self.game.on_show_tutorial),
            MenuItem(
                "Game Analysis",
                self.game.on_show_game_analysis,
                enabled=self.game.board.game_over(),
            ),
            MenuItem("Toggle Move Analysis", self.game.on_toggle_move_analysis),
            MenuItem(
                "Replay Mode",
                self.game.on_toggle_replay,
                enabled=len(self.game.ui.move_history) > 0,
            ),
            MenuItem("Difficulty Statistics", self.game.on_show_difficulty_stats),
            MenuItem("About Reversi Deluxe", self.game.on_show_about),
        ]

        self.menus = [
            Menu("Game", game_items),
            Menu("AI", ai_items),
            Menu("View", view_items),
            Menu("Help", help_items),
        ]

        # Position menus
        x = MENU_PADDING
        for menu in self.menus:
            text_width = self.font.size(menu.title)[0]
            menu.rect = pg.Rect(x, 0, text_width + MENU_PADDING * 2, MENU_BAR_HEIGHT)
            x += menu.rect.width + MENU_PADDING // 2

    def draw_menu_bar(self, screen, theme):
        """Draw the clean menu bar with enhanced hover feedback"""
        # Menu bar background with subtle gradient effect
        if theme["name"] in ["midnight"]:
            menu_bg = (45, 45, 50)
            border_color = (65, 65, 75)
        else:
            menu_bg = theme["hud"]
            border_color = tuple(max(0, c - 40) for c in theme["hud"])
        # Clean menu bar background
        menu_rect = pg.Rect(0, 0, screen.get_width(), MENU_BAR_HEIGHT)
        pg.draw.rect(screen, menu_bg, menu_rect)

        # Subtle bottom border
        pg.draw.line(
            screen,
            border_color,
            (0, MENU_BAR_HEIGHT - 1),
            (screen.get_width(), MENU_BAR_HEIGHT - 1),
        )

        # Draw menu titles with refined styling
        mouse_pos = pg.mouse.get_pos()
        for i, menu in enumerate(self.menus):
            is_hover = menu.rect.collidepoint(mouse_pos) or menu == self.active_menu
            is_selected = i == self.selected_menu_index and self.active_menu

            if is_hover or is_selected:
                # Highlight active/selected menu
                hover_color = tuple(
                    min(255, c + 10) if theme["name"] == "midnight" else max(0, c - 10)
                    for c in menu_bg
                )
                pg.draw.rect(screen, hover_color, menu.rect, border_radius=4)

                # Draw indicator bar under active menu
                if is_selected:
                    indicator_y = menu.rect.bottom - 2
                    pg.draw.line(
                        screen,
                        theme["accent"],
                        (menu.rect.left, indicator_y),
                        (menu.rect.right, indicator_y),
                        2,
                    )

            text_color = theme["text"]
            text = self.font.render(menu.title, True, text_color)
            text_rect = text.get_rect(center=menu.rect.center)
            screen.blit(text, text_rect)

        # Dropdown will be drawn separately at the end to ensure it's on top

    def draw_dropdown(self, screen, theme):
        """Draw dropdown menu with better visual feedback"""
        menu = self.active_menu
        if not menu or not menu.items:
            return

        # Calculate dropdown position and size
        dropdown_rect = pg.Rect(
            menu.rect.x,
            menu.rect.bottom,
            DROPDOWN_WIDTH,
            len(menu.items) * MENU_ITEM_HEIGHT + MENU_PADDING * 2,
        )

        # Dropdown background and shadow
        shadow_rect = dropdown_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pg.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=5)

        dropdown_bg = theme["hud"]
        border_color = tuple(max(0, c - 40) for c in theme["hud"])

        pg.draw.rect(screen, dropdown_bg, dropdown_rect, border_radius=5)
        pg.draw.rect(screen, border_color, dropdown_rect, 1, border_radius=5)

        # Draw menu items with enhanced visuals
        mouse_pos = pg.mouse.get_pos()
        y = dropdown_rect.y + MENU_PADDING

        for i, item in enumerate(menu.items):
            item_rect = pg.Rect(
                dropdown_rect.x + 5, y, dropdown_rect.width - 10, MENU_ITEM_HEIGHT
            )

            # Highlight selected item (keyboard) or hovered item (mouse)
            is_selected = i == self.selected_item_index
            is_hovered = item_rect.collidepoint(mouse_pos)

            # Auto-show submenu on hover
            if is_hovered and item.submenu:
                if self.active_submenu_items != item.submenu:
                    self.active_submenu_items = item.submenu
                    self.selected_item_index = i

            if (is_selected or is_hovered) and item.enabled:
                # Different colors for keyboard vs mouse selection
                if is_selected and not is_hovered:
                    # Keyboard selection - accent color
                    select_color = tuple(
                        min(255, int(c * 0.3 + theme["accent"][i] * 0.7))
                        for i, c in enumerate(theme["hud"])
                    )
                    pg.draw.rect(screen, select_color, item_rect, border_radius=3)
                    # Draw selection indicator
                    indicator_rect = pg.Rect(
                        item_rect.x - 2, item_rect.y + 2, 3, item_rect.height - 4
                    )
                    pg.draw.rect(
                        screen, theme["accent"], indicator_rect, border_radius=2
                    )
                elif is_hovered:
                    # Mouse hover - lighter background
                    hover_color = tuple(max(0, c - 20) for c in theme["hud"])
                    pg.draw.rect(screen, hover_color, item_rect, border_radius=3)

            # Text with better contrast
            if item.enabled:
                text_color = theme["text"]
                # Make selected text slightly brighter
                if is_selected and not is_hovered:
                    text_color = tuple(min(255, c + 20) for c in theme["text"])
            else:
                text_color = (120, 120, 120)

            text = self.font.render(item.label, True, text_color)
            screen.blit(
                text, (item_rect.x + 8, item_rect.centery - text.get_height() // 2)
            )

            # Draw submenu indicator if item has submenu
            if item.submenu:
                arrow = self.font.render("▸", True, text_color)
                arrow_x = item_rect.right - arrow.get_width() - 8
                arrow_y = item_rect.centery - arrow.get_height() // 2
                screen.blit(arrow, (arrow_x, arrow_y))

            y += MENU_ITEM_HEIGHT

    def handle_click(self, pos):
        """Handle menu clicks with mouse"""
        # Check menu bar clicks
        for i, menu in enumerate(self.menus):
            if menu.rect.collidepoint(pos):
                if self.active_menu == menu:
                    self.active_menu = None
                else:
                    self.active_menu = menu
                    self.selected_menu_index = i
                    self.selected_item_index = 0  # Reset item selection
                    # Refresh menu items to show current state
                    self.setup_menus()
                return True

        # Check dropdown clicks
        if self.active_menu:
            dropdown_rect = pg.Rect(
                self.active_menu.rect.x,
                self.active_menu.rect.bottom,
                DROPDOWN_WIDTH,
                len(self.active_menu.items) * MENU_ITEM_HEIGHT + MENU_PADDING * 2,
            )

            # Check if clicking on submenu first (submenu is outside dropdown)
            if self.active_submenu_items:
                submenu_rect = self._get_submenu_rect(dropdown_rect)
                if submenu_rect.collidepoint(pos):
                    # Find clicked submenu item
                    y = submenu_rect.y + MENU_PADDING
                    for i, item in enumerate(self.active_submenu_items):
                        item_rect = pg.Rect(
                            submenu_rect.x + 5,
                            y,
                            submenu_rect.width - 10,
                            MENU_ITEM_HEIGHT,
                        )
                        if item_rect.collidepoint(pos) and item.enabled:
                            if item.handler:
                                item.handler()
                            self.active_menu = None
                            self.active_submenu_items = None
                            self.setup_menus()
                            return True
                        y += MENU_ITEM_HEIGHT

            if dropdown_rect.collidepoint(pos):
                # Find clicked item in main dropdown
                y = dropdown_rect.y + MENU_PADDING
                for i, item in enumerate(self.active_menu.items):
                    item_rect = pg.Rect(
                        dropdown_rect.x + 5,
                        y,
                        dropdown_rect.width - 10,
                        MENU_ITEM_HEIGHT,
                    )
                    if item_rect.collidepoint(pos) and item.enabled:
                        self.selected_item_index = i
                        if item.submenu:
                            # Show submenu
                            self.active_submenu_items = item.submenu
                            self.selected_submenu_index = 0
                        else:
                            # Execute handler
                            self._execute_selected_item()
                        return True
                    y += MENU_ITEM_HEIGHT
            else:
                # Click outside dropdown - close it
                self.active_menu = None
                self.active_submenu_items = None

        return False

    def handle_keyboard(self, key):
        """Handle keyboard navigation in menus"""
        from src.logger import get_logger

        logger = get_logger(__name__)

        # Alt key to open first menu
        if key == pg.K_LALT or key == pg.K_RALT:
            if self.active_menu is None:
                self.active_menu = self.menus[0]
                self.selected_menu_index = 0
                self.selected_item_index = 0
                logger.debug("Menu activated via Alt key")
                return True

        # If no menu is open, don't handle other keys
        if self.active_menu is None:
            return False

        # Left/Right arrows - navigate between menus
        if key == pg.K_LEFT:
            self.selected_menu_index = (self.selected_menu_index - 1) % len(self.menus)
            self.active_menu = self.menus[self.selected_menu_index]
            self.selected_item_index = 0
            logger.debug(f"Menu left to {self.active_menu.title}")
            return True

        elif key == pg.K_RIGHT:
            self.selected_menu_index = (self.selected_menu_index + 1) % len(self.menus)
            self.active_menu = self.menus[self.selected_menu_index]
            self.selected_item_index = 0
            logger.debug(f"Menu right to {self.active_menu.title}")
            return True

        # Up/Down arrows - navigate menu items
        elif key == pg.K_UP:
            # Move up, skip disabled items
            for _ in range(len(self.active_menu.items)):
                self.selected_item_index = (self.selected_item_index - 1) % len(
                    self.active_menu.items
                )
                if self.active_menu.items[self.selected_item_index].enabled:
                    break
            logger.debug(f"Menu item up: {self.selected_item_index}")
            return True

        elif key == pg.K_DOWN:
            # Move down, skip disabled items
            for _ in range(len(self.active_menu.items)):
                self.selected_item_index = (self.selected_item_index + 1) % len(
                    self.active_menu.items
                )
                if self.active_menu.items[self.selected_item_index].enabled:
                    break
            logger.debug(f"Menu item down: {self.selected_item_index}")
            return True

        # Enter/Return - execute selected item or show submenu
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            item = self.active_menu.items[self.selected_item_index]
            if item.submenu:
                # Show submenu
                self.active_submenu_items = item.submenu
                self.selected_submenu_index = 0
            else:
                self._execute_selected_item()
            logger.debug("Menu item executed via Enter")
            return True

        # Escape - close menu or submenu
        elif key == pg.K_ESCAPE:
            if self.active_submenu_items:
                self.active_submenu_items = None
            else:
                self.active_menu = None
            logger.debug("Menu closed via Escape")
            return True

        return False

    def _execute_selected_item(self):
        """Execute the currently selected menu item"""
        if self.active_menu and 0 <= self.selected_item_index < len(
            self.active_menu.items
        ):
            item = self.active_menu.items[self.selected_item_index]
            if item.enabled and item.handler:
                try:
                    item.handler()
                    self.active_menu = None  # Close menu after action
                    self.active_submenu_items = None
                    self.setup_menus()  # Refresh menu state
                except (AttributeError, TypeError) as e:
                    from src.logger import get_logger

                    logger = get_logger(__name__)
                    logger.error(f"Menu handler error: {e}")
                    print(f"Menu handler error: {e}")

    def _get_submenu_rect(self, parent_rect):
        """Calculate submenu rectangle position"""
        if not self.active_submenu_items:
            return pg.Rect(0, 0, 0, 0)

        # Position submenu to the right of parent dropdown
        submenu_height = (
            len(self.active_submenu_items) * MENU_ITEM_HEIGHT + MENU_PADDING * 2
        )
        return pg.Rect(
            parent_rect.right - 5,
            parent_rect.y + MENU_PADDING + self.selected_item_index * MENU_ITEM_HEIGHT,
            DROPDOWN_WIDTH - 20,
            submenu_height,
        )

    def draw_dropdown_overlay(self, screen, theme):
        """Draw dropdown menu on top of everything else"""
        if self.active_menu:
            self.draw_dropdown(screen, theme)

            # Draw submenu if active
            if self.active_submenu_items:
                dropdown_rect = pg.Rect(
                    self.active_menu.rect.x,
                    self.active_menu.rect.bottom,
                    DROPDOWN_WIDTH,
                    len(self.active_menu.items) * MENU_ITEM_HEIGHT + MENU_PADDING * 2,
                )
                self.draw_submenu(screen, theme, dropdown_rect)

    def draw_submenu(self, screen, theme, parent_rect):
        """Draw submenu for the selected item"""
        if not self.active_submenu_items:
            return

        submenu_rect = self._get_submenu_rect(parent_rect)

        # Shadow
        shadow_rect = submenu_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pg.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=5)

        # Background
        submenu_bg = theme["hud"]
        border_color = tuple(max(0, c - 40) for c in theme["hud"])
        pg.draw.rect(screen, submenu_bg, submenu_rect, border_radius=5)
        pg.draw.rect(screen, border_color, submenu_rect, 1, border_radius=5)

        # Draw submenu items
        mouse_pos = pg.mouse.get_pos()
        y = submenu_rect.y + MENU_PADDING

        for i, item in enumerate(self.active_submenu_items):
            item_rect = pg.Rect(
                submenu_rect.x + 5,
                y,
                submenu_rect.width - 10,
                MENU_ITEM_HEIGHT,
            )

            # Highlight hovered item
            is_hovered = item_rect.collidepoint(mouse_pos)
            if is_hovered and item.enabled:
                hover_color = theme["accent"]
                pg.draw.rect(screen, hover_color, item_rect, border_radius=3)

            # Draw text
            text_color = theme["text"] if item.enabled else (120, 120, 120)
            text = self.font.render(item.label, True, text_color)
            screen.blit(
                text, (item_rect.x + 8, item_rect.centery - text.get_height() // 2)
            )

            y += MENU_ITEM_HEIGHT


class SelectionDialog:
    """Dialog for selecting from a list of options"""

    def __init__(self):
        self.active = False
        self.title = ""
        self.options = []  # List of (label, value) tuples
        self.selected_index = 0
        self.callback = None
        self.font = pg.font.SysFont("Arial", 16)
        self.title_font = pg.font.SysFont("Arial", 18, bold=True)

    def show(self, title, options, current_value, callback):
        """Show the selection dialog

        Args:
            title: Dialog title
            options: List of (label, value) tuples
            current_value: Currently selected value
            callback: Function to call with selected value
        """
        self.active = True
        self.title = title
        self.options = options
        self.callback = callback

        # Find current selection
        self.selected_index = 0
        for i, (label, value) in enumerate(options):
            if value == current_value:
                self.selected_index = i
                break

    def hide(self):
        """Hide the dialog"""
        self.active = False

    def handle_click(self, pos):
        """Handle mouse clicks in the dialog"""
        if not self.active:
            return False

        # Get dialog rect
        screen_w, screen_h = pg.display.get_surface().get_size()
        dialog_w = 400
        dialog_h = 80 + len(self.options) * 40
        dialog_x = (screen_w - dialog_w) // 2
        dialog_y = (screen_h - dialog_h) // 2
        dialog_rect = pg.Rect(dialog_x, dialog_y, dialog_w, dialog_h)

        # Check if clicked inside dialog
        if not dialog_rect.collidepoint(pos):
            self.hide()
            return True

        # Check option clicks
        y = dialog_y + 60
        for i, (label, value) in enumerate(self.options):
            option_rect = pg.Rect(dialog_x + 20, y, dialog_w - 40, 35)
            if option_rect.collidepoint(pos):
                self.selected_index = i
                if self.callback:
                    self.callback(value)
                self.hide()
                return True
            y += 40

        return True

    def handle_keyboard(self, key):
        """Handle keyboard input in the dialog"""
        if not self.active:
            return False

        if key == pg.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            return True
        elif key == pg.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return True
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            if self.callback:
                _, value = self.options[self.selected_index]
                self.callback(value)
            self.hide()
            return True
        elif key == pg.K_ESCAPE:
            self.hide()
            return True

        return False

    def draw(self, screen, theme):
        """Draw the selection dialog"""
        if not self.active:
            return

        # Semi-transparent overlay
        overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        # Dialog box
        screen_w, screen_h = screen.get_size()
        dialog_w = 400
        dialog_h = 80 + len(self.options) * 40
        dialog_x = (screen_w - dialog_w) // 2
        dialog_y = (screen_h - dialog_h) // 2

        # Draw dialog background with border
        dialog_rect = pg.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
        pg.draw.rect(screen, theme["hud"], dialog_rect, border_radius=10)
        pg.draw.rect(screen, theme["accent"], dialog_rect, 2, border_radius=10)

        # Draw title
        title_surf = self.title_font.render(self.title, True, theme["text"])
        title_x = dialog_x + (dialog_w - title_surf.get_width()) // 2
        screen.blit(title_surf, (title_x, dialog_y + 15))

        # Draw separator line
        line_y = dialog_y + 50
        pg.draw.line(
            screen,
            theme["accent"],
            (dialog_x + 20, line_y),
            (dialog_x + dialog_w - 20, line_y),
            2,
        )

        # Draw options
        mouse_pos = pg.mouse.get_pos()
        y = dialog_y + 60

        for i, (label, value) in enumerate(self.options):
            option_rect = pg.Rect(dialog_x + 20, y, dialog_w - 40, 35)

            # Highlight selected or hovered option
            is_selected = i == self.selected_index
            is_hovered = option_rect.collidepoint(mouse_pos)

            if is_selected or is_hovered:
                highlight_color = (
                    theme["accent"]
                    if is_selected
                    else tuple(max(0, c - 30) for c in theme["hud"])
                )
                pg.draw.rect(screen, highlight_color, option_rect, border_radius=5)

            # Draw option text
            text_color = (
                theme["text"]
                if is_selected
                else tuple(max(80, c - 40) for c in theme["text"])
            )
            text_surf = self.font.render(label, True, text_color)
            text_x = option_rect.x + 15
            text_y = option_rect.centery - text_surf.get_height() // 2
            screen.blit(text_surf, (text_x, text_y))

            y += 40


@dataclass
class PostGameAnalysis:
    """Comprehensive analysis of a completed game"""

    total_moves: int
    game_duration: float
    black_stats: dict
    white_stats: dict
    move_history: List[MoveAnalysis]
    opening_classification: str
    critical_moments: List[Tuple[int, str]]  # (move_number, description)
    improvement_suggestions: List[str]
    final_score: Tuple[int, int]  # (black, white)
    winner: str


class GameAnalysisDisplay:
    """Display comprehensive post-game analysis"""

    def __init__(self, game):
        self.game = game
        self.active = False
        self.scroll_y = 0
        self.font = pg.font.SysFont("Arial", 16)
        self.title_font = pg.font.SysFont("Arial", 20, bold=True)
        self.small_font = pg.font.SysFont("Arial", 14)

    def show_analysis(self):
        """Show the post-game analysis"""
        if not self.game.board.game_over():
            return

        self.active = True
        self.scroll_y = 0

    def hide_analysis(self):
        """Hide the analysis display"""
        self.active = False

    def generate_analysis(self) -> PostGameAnalysis:
        """Generate comprehensive analysis of the completed game"""
        black_score, white_score = self.game.board.score()

        # Determine winner
        if black_score > white_score:
            winner = "Black"
        elif white_score > black_score:
            winner = "White"
        else:
            winner = "Draw"

        # Calculate game duration
        if (
            self.game.ui.game_start_time is not None
            and self.game.ui.game_end_time is not None
        ):
            game_duration = self.game.ui.game_end_time - self.game.ui.game_start_time
        elif self.game.ui.game_start_time is not None:
            # Fallback if end time not set yet
            game_duration = time.time() - self.game.ui.game_start_time
        else:
            game_duration = 0.0  # Fallback for missing start time

        # Analyze move history
        move_analyses = []
        critical_moments = []

        board_size = self.game.board.size
        max_index = board_size - 1

        # Create a simplified analysis for each move using available data
        for i, entry in enumerate(self.game.ui.move_history):
            # Create a simplified move analysis from available data
            move_analysis = MoveAnalysis(
                move_number=entry.move_number,
                player=entry.player,
                row=entry.row,
                col=entry.col,
                pieces_captured=entry.pieces_flipped,
                board_control_before=50.0,  # Simplified - assume balanced
                board_control_after=50.0 + (entry.pieces_flipped * 2),
                corner_moves=(
                    1
                    if (entry.row in [0, max_index] and entry.col in [0, max_index])
                    else 0
                ),
                edge_moves=(
                    1
                    if (entry.row in [0, max_index] or entry.col in [0, max_index])
                    else 0
                ),
                mobility_change=0,  # Simplified
                move_quality=self._evaluate_simple_move_quality(entry),
            )
            move_analyses.append(move_analysis)

            # Identify critical moments
            if move_analysis.move_quality in ["Excellent", "Brilliant"]:
                critical_moments.append(
                    (i + 1, f"Excellent {move_analysis.move_quality.lower()} move")
                )
            elif move_analysis.move_quality == "Poor":
                critical_moments.append((i + 1, "Missed opportunity"))

        # Generate player statistics
        black_moves = [a for i, a in enumerate(move_analyses) if i % 2 == 0]
        white_moves = [a for i, a in enumerate(move_analyses) if i % 2 == 1]

        black_stats = self._calculate_player_stats(black_moves)
        white_stats = self._calculate_player_stats(white_moves)

        # Classify opening
        opening = self._classify_opening()

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            move_analyses, black_stats, white_stats
        )

        return PostGameAnalysis(
            total_moves=len(self.game.ui.move_history),
            game_duration=game_duration,
            black_stats=black_stats,
            white_stats=white_stats,
            move_history=move_analyses,
            opening_classification=opening,
            critical_moments=critical_moments,
            improvement_suggestions=suggestions,
            final_score=(black_score, white_score),
            winner=winner,
        )

    def _calculate_player_stats(self, moves: List[MoveAnalysis]):
        """Calculate statistics for a player's moves"""
        if not moves:
            return {
                "moves_played": 0,
                "pieces_captured": 0,
                "corners_taken": 0,
                "edge_moves": 0,
                "excellent_moves": 0,
                "good_moves": 0,
                "avg_pieces_per_move": 0.0,
                "avg_mobility_change": 0.0,
                "avg_control_change": 0.0,
            }

        total_pieces = sum(m.pieces_captured for m in moves)
        corner_moves = sum(m.corner_moves for m in moves)
        edge_moves = sum(m.edge_moves for m in moves)

        quality_counts = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0}
        for move in moves:
            if move.move_quality in quality_counts:
                quality_counts[move.move_quality] += 1

        avg_pieces = total_pieces / len(moves) if moves else 0
        avg_mobility = (
            sum(m.mobility_change for m in moves) / len(moves) if moves else 0
        )
        avg_control = (
            sum((m.board_control_after - m.board_control_before) for m in moves)
            / len(moves)
            if moves
            else 0
        )

        return {
            "moves_played": len(moves),
            "pieces_captured": total_pieces,
            "corners_taken": corner_moves,
            "edge_moves": edge_moves,
            "excellent_moves": quality_counts["Excellent"],
            "good_moves": quality_counts["Good"],
            "avg_pieces_per_move": avg_pieces,
            "avg_mobility_change": avg_mobility,
            "avg_control_change": avg_control,
        }

    def _classify_opening(self) -> str:
        """Classify the game opening based on first few moves"""
        if len(self.game.ui.move_history) < 4:
            return "Insufficient moves"

        board_size = self.game.board.size
        center_start = board_size // 2 - 1
        center_end = board_size // 2 + 1

        # Simple opening classification based on first 4 moves
        first_moves = [
            (entry.row, entry.col) for entry in self.game.ui.move_history[:4]
        ]

        # Center-focused opening (in the 4 center squares)
        center_squares = [
            (r, c)
            for r in range(center_start, center_end)
            for c in range(center_start, center_end)
        ]
        center_moves = sum(1 for move in first_moves if move in center_squares)

        if center_moves >= 3:
            return "Center Control Opening"

        # Edge-focused opening
        max_index = board_size - 1
        edge_moves = sum(
            1
            for r, c in first_moves
            if r == 0 or r == max_index or c == 0 or c == max_index
        )

        if edge_moves >= 2:
            return "Edge Attack Opening"

        return "Balanced Opening"

    def _generate_suggestions(
        self, moves: List[MoveAnalysis], black_stats: dict, white_stats: dict
    ) -> List[str]:
        """Generate improvement suggestions based on game analysis"""
        suggestions = []

        # Analyze move quality patterns
        poor_moves = sum(1 for m in moves if m.move_quality == "Poor")
        total_moves = len(moves)

        if poor_moves / total_moves > 0.3:
            suggestions.append(
                "Focus on strategic planning - consider mobility and board control"
            )

        # Corner strategy
        total_corners = black_stats["corners_taken"] + white_stats["corners_taken"]
        if total_corners < 2:
            suggestions.append(
                "Pay more attention to corner opportunities - they're worth many pieces"
            )

        # Mobility awareness
        avg_mobility = (
            black_stats["avg_mobility_change"] + white_stats["avg_mobility_change"]
        ) / 2
        if avg_mobility < 0:
            suggestions.append(
                "Consider moves that preserve your future options (mobility)"
            )

        # Opening improvement
        if len(moves) > 8:
            early_poor = sum(1 for m in moves[:8] if m.move_quality == "Poor")
            if early_poor >= 3:
                suggestions.append(
                    "Work on opening principles - control center, maintain mobility"
                )

        # Endgame improvement
        if len(moves) > 12:
            late_poor = sum(1 for m in moves[-8:] if m.move_quality == "Poor")
            if late_poor >= 3:
                suggestions.append(
                    "Practice endgame tactics - every piece counts in the final moves"
                )

        return suggestions[:5]  # Limit to top 5 suggestions

    def draw(self, screen, theme):
        """Draw the analysis display"""
        if not self.active:
            return

        # Semi-transparent background
        overlay = pg.Surface(screen.get_size())
        overlay.set_alpha(240)
        overlay.fill((20, 20, 25))
        screen.blit(overlay, (0, 0))

        # Analysis panel
        panel_width = 600
        panel_height = 500
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2

        panel_rect = pg.Rect(panel_x, panel_y, panel_width, panel_height)
        pg.draw.rect(screen, theme["hud"], panel_rect, border_radius=12)
        pg.draw.rect(screen, theme["accent"], panel_rect, 3, border_radius=12)

        # Generate analysis
        analysis = self.generate_analysis()

        # Title
        title = self.title_font.render("Game Analysis", True, theme["text"])
        screen.blit(title, (panel_x + 20, panel_y + 15))

        # Close hint
        close_hint = self.small_font.render(
            "Press 'G' or ESC to close", True, theme["text"]
        )
        screen.blit(
            close_hint,
            (panel_x + panel_width - close_hint.get_width() - 20, panel_y + 15),
        )

        # Content area
        content_y = panel_y + 50
        content_height = panel_height - 60
        line_height = 22

        lines = self._format_analysis_text(analysis)

        # Draw scrollable content
        visible_lines = content_height // line_height
        start_line = max(0, min(self.scroll_y, len(lines) - visible_lines))

        for i, line in enumerate(lines[start_line : start_line + visible_lines]):
            y = content_y + i * line_height
            if line.startswith("##"):  # Section header
                text = self.title_font.render(line[2:], True, theme["accent"])
            elif line.startswith("**"):  # Bold text
                text = self.font.render(line[2:], True, theme["text"])
            else:  # Regular text
                text = self.font.render(line, True, theme["text"])

            screen.blit(text, (panel_x + 20, y))

        # Scroll indicators
        if start_line > 0:
            pg.draw.polygon(
                screen,
                theme["accent"],
                [
                    (panel_x + panel_width - 30, content_y + 10),
                    (panel_x + panel_width - 20, content_y),
                    (panel_x + panel_width - 10, content_y + 10),
                ],
            )

        if start_line + visible_lines < len(lines):
            bottom_y = content_y + content_height - 10
            pg.draw.polygon(
                screen,
                theme["accent"],
                [
                    (panel_x + panel_width - 30, bottom_y),
                    (panel_x + panel_width - 20, bottom_y + 10),
                    (panel_x + panel_width - 10, bottom_y),
                ],
            )

    def _format_analysis_text(self, analysis: PostGameAnalysis) -> List[str]:
        """Format analysis data into display lines"""
        lines = []

        # Game summary
        lines.append("## Game Summary")
        minutes = int(analysis.game_duration // 60)
        seconds = int(analysis.game_duration % 60)
        lines.append(f"Duration: {minutes}:{seconds:02d}")
        lines.append(f"Total moves: {analysis.total_moves}")
        lines.append(
            f"Final score: Black {analysis.final_score[0]} - "
            f"{analysis.final_score[1]} White"
        )
        lines.append(f"Winner: {analysis.winner}")
        lines.append(f"Opening: {analysis.opening_classification}")
        lines.append("")

        # Player statistics
        lines.append("## Player Performance")
        lines.append("**Black Player:")
        lines.append(f"  Moves: {analysis.black_stats['moves_played']}")
        lines.append(f"  Pieces captured: {analysis.black_stats['pieces_captured']}")
        lines.append(f"  Corners taken: {analysis.black_stats['corners_taken']}")
        lines.append(f"  Excellent moves: {analysis.black_stats['excellent_moves']}")
        lines.append(f"  Good moves: {analysis.black_stats['good_moves']}")
        lines.append("")

        lines.append("**White Player:")
        lines.append(f"  Moves: {analysis.white_stats['moves_played']}")
        lines.append(f"  Pieces captured: {analysis.white_stats['pieces_captured']}")
        lines.append(f"  Corners taken: {analysis.white_stats['corners_taken']}")
        lines.append(f"  Excellent moves: {analysis.white_stats['excellent_moves']}")
        lines.append(f"  Good moves: {analysis.white_stats['good_moves']}")
        lines.append("")

        # Critical moments
        if analysis.critical_moments:
            lines.append("## Key Moments")
            for move_num, description in analysis.critical_moments[:5]:
                lines.append(f"Move {move_num}: {description}")
            lines.append("")

        # Improvement suggestions
        if analysis.improvement_suggestions:
            lines.append("## Suggestions for Improvement")
            for suggestion in analysis.improvement_suggestions:
                lines.append(f"• {suggestion}")

        return lines

    def _evaluate_simple_move_quality(self, entry: MoveHistoryEntry) -> str:
        """Evaluate move quality based on available data"""
        pieces_flipped = entry.pieces_flipped
        board_size = self.game.board.size
        max_index = board_size - 1

        # Check if corner (using actual board size)
        is_corner = entry.row in [0, max_index] and entry.col in [0, max_index]

        # Simple heuristic based on pieces captured and position
        if is_corner:
            return "Excellent"  # Corner moves are always good
        elif pieces_flipped >= 6:
            return "Excellent"  # High capture moves
        elif pieces_flipped >= 4:
            return "Good"
        elif pieces_flipped >= 2:
            return "Fair"
        else:
            return "Poor"  # Low impact moves

    def handle_scroll(self, direction: int):
        """Handle scrolling of the analysis content"""
        if self.active:
            self.scroll_y = max(0, self.scroll_y + direction * 3)


class ReplayMode:
    """Handle game replay mode with timeline scrubbing"""

    def __init__(self, game):
        self.game = game
        self.font = pg.font.Font(None, 16)
        self.title_font = pg.font.Font(None, 20)

    def enter_replay_mode(self):
        """Enter replay mode"""
        if not self.game.ui.move_history:
            self.game.ui.status = "No moves to replay"
            return

        self.game.ui.replay_mode = True
        self.game.ui.replay_index = 0
        self.game.ui.replay_playing = False
        self.restore_board_state(0)
        self.game.ui.status = "Replay mode - Use ◀/▶ or click timeline"

    def exit_replay_mode(self):
        """Exit replay mode and restore current board"""
        self.game.ui.replay_mode = False
        self.game.ui.replay_playing = False
        # Restore current board by replaying all moves
        if self.game.ui.move_history:
            self.restore_board_state(len(self.game.ui.move_history))
        self.game.ui.status = "Exited replay mode"

    def restore_board_state(self, move_index: int):
        """Restore board to a specific move index"""
        # Reset board to initial state
        self.game.board = Board(self.game.board.size)

        # Replay moves up to the index
        for i, entry in enumerate(self.game.ui.move_history[:move_index]):
            legal = {
                (m.row, m.col): m
                for m in self.game.board.legal_moves(self.game.board.to_move)
            }
            mv = legal.get((entry.row, entry.col))
            if mv:
                self.game.board.make_move(mv)

        self.game.ui.replay_index = move_index

    def step_forward(self):
        """Step one move forward in replay"""
        if self.game.ui.replay_index < len(self.game.ui.move_history):
            self.game.ui.replay_index += 1
            self.restore_board_state(self.game.ui.replay_index)
            self.update_status()

    def step_backward(self):
        """Step one move backward in replay"""
        if self.game.ui.replay_index > 0:
            self.game.ui.replay_index -= 1
            self.restore_board_state(self.game.ui.replay_index)
            self.update_status()

    def toggle_play(self):
        """Toggle play/pause in replay"""
        self.game.ui.replay_playing = not self.game.ui.replay_playing
        if self.game.ui.replay_playing:
            self.game.ui.replay_last_step = time.time()

    def update(self):
        """Update replay playback"""
        if self.game.ui.replay_playing and self.game.ui.replay_index < len(
            self.game.ui.move_history
        ):
            now = time.time()
            if now - self.game.ui.replay_last_step >= (1.0 / self.game.ui.replay_speed):
                self.step_forward()
                self.game.ui.replay_last_step = now
                if self.game.ui.replay_index >= len(self.game.ui.move_history):
                    self.game.ui.replay_playing = False

    def update_status(self):
        """Update status message for current replay position"""
        total = len(self.game.ui.move_history)
        current = self.game.ui.replay_index
        if current < total:
            entry = self.game.ui.move_history[current]
            player = "Black" if entry.player == BLACK else "White"
            self.game.ui.status = f"Replay: Move {current}/{total} - {player}'s turn"
        else:
            self.game.ui.status = f"Replay: End of game ({total} moves)"

    def draw_timeline(self, screen, theme):
        """Draw the replay timeline control"""
        if not self.game.ui.replay_mode:
            return

        # Timeline bar at bottom
        timeline_height = 80
        timeline_rect = pg.Rect(
            MARGIN, H - timeline_height - MARGIN, W - MARGIN * 2, timeline_height
        )

        # Background
        pg.draw.rect(screen, theme["hud"], timeline_rect, border_radius=8)
        pg.draw.rect(screen, theme["grid"], timeline_rect, 2, border_radius=8)

        # Title
        title = self.title_font.render("Game Replay", True, theme["text"])
        screen.blit(title, (timeline_rect.x + 10, timeline_rect.y + 5))

        # Timeline slider
        slider_y = timeline_rect.y + 35
        slider_start_x = timeline_rect.x + 100
        slider_width = timeline_rect.width - 220
        slider_height = 8

        slider_rect = pg.Rect(slider_start_x, slider_y, slider_width, slider_height)

        # Slider background
        pg.draw.rect(screen, theme["grid"], slider_rect, border_radius=4)

        # Progress bar
        total_moves = len(self.game.ui.move_history)
        if total_moves > 0:
            progress = self.game.ui.replay_index / total_moves
            progress_width = int(slider_width * progress)
            progress_rect = pg.Rect(
                slider_start_x, slider_y, progress_width, slider_height
            )
            pg.draw.rect(screen, theme["accent"], progress_rect, border_radius=4)

            # Scrubber handle
            handle_x = slider_start_x + progress_width
            handle_rect = pg.Rect(handle_x - 6, slider_y - 4, 12, 16)
            pg.draw.rect(screen, theme["accent"], handle_rect, border_radius=6)
            pg.draw.rect(screen, theme["text"], handle_rect, 2, border_radius=6)

        # Move counter
        counter_text = f"{self.game.ui.replay_index} / {total_moves}"
        counter = self.font.render(counter_text, True, theme["text"])
        screen.blit(
            counter,
            (timeline_rect.right - counter.get_width() - 10, timeline_rect.y + 5),
        )

        # Controls
        controls_y = slider_y + 20
        button_width = 60
        button_height = 24
        button_spacing = 10

        buttons = [
            ("⏮", self.go_to_start, "Start"),
            ("◀", self.step_backward, "Back"),
            (
                "⏯" if not self.game.ui.replay_playing else "⏸",
                self.toggle_play,
                "Play/Pause",
            ),
            ("▶", self.step_forward, "Forward"),
            ("⏭", self.go_to_end, "End"),
            ("✕", self.exit_replay_mode, "Exit"),
        ]

        start_x = (
            timeline_rect.centerx
            - ((button_width + button_spacing) * len(buttons) - button_spacing) // 2
        )

        mouse_pos = pg.mouse.get_pos()

        for i, (icon, handler, tooltip) in enumerate(buttons):
            btn_x = start_x + i * (button_width + button_spacing)
            btn_rect = pg.Rect(btn_x, controls_y, button_width, button_height)

            is_hover = btn_rect.collidepoint(mouse_pos)
            btn_color = theme["accent"] if is_hover else theme["grid"]

            pg.draw.rect(screen, btn_color, btn_rect, border_radius=4)
            pg.draw.rect(screen, theme["text"], btn_rect, 1, border_radius=4)

            # Button text
            btn_text = self.font.render(icon, True, theme["text"])
            text_rect = btn_text.get_rect(center=btn_rect.center)
            screen.blit(btn_text, text_rect)

    def go_to_start(self):
        """Jump to start of game"""
        self.game.ui.replay_index = 0
        self.restore_board_state(0)
        self.update_status()

    def go_to_end(self):
        """Jump to end of game"""
        self.game.ui.replay_index = len(self.game.ui.move_history)
        self.restore_board_state(self.game.ui.replay_index)
        self.update_status()

    def handle_timeline_click(self, pos: Tuple[int, int]) -> bool:
        """Handle clicks on the timeline. Returns True if handled"""
        if not self.game.ui.replay_mode:
            return False

        # Check timeline slider area
        timeline_height = 80
        timeline_rect = pg.Rect(
            MARGIN, H - timeline_height - MARGIN, W - MARGIN * 2, timeline_height
        )

        if not timeline_rect.collidepoint(pos):
            return False

        # Check slider
        slider_y = timeline_rect.y + 35
        slider_start_x = timeline_rect.x + 100
        slider_width = timeline_rect.width - 220
        slider_height = 20  # Larger hit area

        slider_rect = pg.Rect(slider_start_x, slider_y - 6, slider_width, slider_height)

        if slider_rect.collidepoint(pos):
            # Calculate clicked position
            rel_x = pos[0] - slider_start_x
            progress = max(0.0, min(1.0, rel_x / slider_width))
            new_index = int(progress * len(self.game.ui.move_history))
            self.game.ui.replay_index = new_index
            self.restore_board_state(new_index)
            self.update_status()
            return True

        # Check control buttons
        controls_y = slider_y + 20
        button_width = 60
        button_height = 24
        button_spacing = 10

        buttons = [
            self.go_to_start,
            self.step_backward,
            self.toggle_play,
            self.step_forward,
            self.go_to_end,
            self.exit_replay_mode,
        ]

        start_x = (
            timeline_rect.centerx
            - ((button_width + button_spacing) * len(buttons) - button_spacing) // 2
        )

        for i, handler in enumerate(buttons):
            btn_x = start_x + i * (button_width + button_spacing)
            btn_rect = pg.Rect(btn_x, controls_y, button_width, button_height)

            if btn_rect.collidepoint(pos):
                handler()
                return True

        return True  # Consume click even if not on specific element


class HintSystem:
    """Provide move hints using AI analysis"""

    def __init__(self, game):
        self.game = game
        self.font = pg.font.Font(None, 16)
        self.hints = []
        self.show_hints = False

    def generate_hints(self):
        """Generate top 3 move suggestions"""
        if self.game.board.game_over():
            self.hints = []
            return

        legal_moves = list(self.game.board.legal_moves(self.game.board.to_move))
        if not legal_moves:
            self.hints = []
            return

        # Use smart depth: better than opponent but not too slow
        # Depth 4-5 gives good hints while staying responsive
        opponent_depth = self.game.settings.ai_depth
        hint_depth = min(5, max(4, opponent_depth + 1))

        move_scores = []
        for move in legal_moves:
            board_copy = Board.deserialize(self.game.board.serialize())
            board_copy.to_move = self.game.board.to_move
            board_copy.make_move(move)

            # Evaluate using smart depth for quality hints with good performance
            score = -self.game.ai.search(
                board_copy,
                hint_depth,
                -float("inf"),
                float("inf"),
                OPP[self.game.board.to_move],
            )
            move_scores.append((score, move))

        # Sort by score and take top 3
        move_scores.sort(reverse=True, key=lambda x: x[0])
        self.hints = [
            {
                "move": move,
                "row": move.row,
                "col": move.col,
                "quality": self._score_to_quality(score, move_scores[0][0]),
                "score": score,
            }
            for score, move in move_scores[:3]
        ]

    def _score_to_quality(self, score: float, best_score: float) -> str:
        """Convert score to quality rating"""
        if score >= best_score * 0.95:
            return "Excellent"
        elif score >= best_score * 0.8:
            return "Good"
        else:
            return "Fair"

    def toggle(self):
        """Toggle hint display"""
        self.show_hints = not self.show_hints
        if self.show_hints:
            self.game.ui.status = "Calculating hints..."
            self.generate_hints()
            opponent_depth = self.game.settings.ai_depth
            hint_depth = min(5, max(4, opponent_depth + 1))
            self.game.ui.status = f"Hints enabled (depth {hint_depth})"
        else:
            self.game.ui.status = "Hints disabled"

    def draw_hints(self, screen, board_rect, cell, theme):
        """Draw hint indicators on board"""
        if not self.show_hints or not self.hints:
            return

        for i, hint in enumerate(self.hints):
            row, col = hint["row"], hint["col"]

            # Skip if this cell is not empty (safety check)
            if self.game.board.grid[row][col] != EMPTY:
                continue

            x = board_rect.x + col * cell + cell // 2
            y = board_rect.y + row * cell + cell // 2

            # Color based on quality
            quality_colors = {
                "Excellent": (100, 255, 100),
                "Good": (100, 200, 255),
                "Fair": (255, 200, 100),
            }
            color = quality_colors.get(hint["quality"], (255, 255, 255))

            # Draw circle with number
            radius = min(cell // 6, 15)
            pg.draw.circle(screen, color, (x, y), radius)
            pg.draw.circle(screen, theme["text"], (x, y), radius, 2)

            # Draw rank number
            rank_text = self.font.render(str(i + 1), True, theme["text"])
            text_rect = rank_text.get_rect(center=(x, y))
            screen.blit(rank_text, text_rect)


class GameExporter:
    """Export games to PGN/JSON formats"""

    @staticmethod
    def export_to_pgn(game) -> str:
        """Export game to PGN format"""
        pgn_lines = []

        # Header
        pgn_lines.append('[Event "Reversi Deluxe Game"]')
        pgn_lines.append(f'[Date "{time.strftime("%Y.%m.%d")}"]')
        pgn_lines.append('[Round "-"]')

        black_player = "Computer" if game.settings.ai_black else "Human"
        white_player = "Computer" if game.settings.ai_white else "Human"
        pgn_lines.append(f'[Black "{black_player}"]')
        pgn_lines.append(f'[White "{white_player}"]')

        black_score, white_score = game.board.score()
        if black_score > white_score:
            result = "1-0"
        elif white_score > black_score:
            result = "0-1"
        else:
            result = "1/2-1/2"
        pgn_lines.append(f'[Result "{result}"]')
        pgn_lines.append(f'[BoardSize "{game.board.size}x{game.board.size}"]')
        pgn_lines.append(f'[FinalScore "{black_score}-{white_score}"]')
        pgn_lines.append("")

        # Moves
        moves = []
        for i, entry in enumerate(game.ui.move_history):
            move_notation = f"{chr(97 + entry.col)}{entry.row + 1}"
            if i % 2 == 0:
                moves.append(f"{i//2 + 1}. {move_notation}")
            else:
                moves[-1] += f" {move_notation}"

        # Wrap moves at reasonable length
        move_text = " ".join(moves) + f" {result}"
        pgn_lines.append(move_text)

        return "\n".join(pgn_lines)

    @staticmethod
    def export_to_json(game) -> str:
        """Export game to JSON format"""
        export_data = {
            "metadata": {
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "board_size": game.board.size,
                "black_player": "Computer" if game.settings.ai_black else "Human",
                "white_player": "Computer" if game.settings.ai_white else "Human",
                "ai_depth": game.settings.ai_depth,
                "theme": game.settings.theme,
            },
            "moves": [
                {
                    "move_number": entry.move_number,
                    "player": "Black" if entry.player == BLACK else "White",
                    "position": f"{chr(97 + entry.col)}{entry.row + 1}",
                    "row": entry.row,
                    "col": entry.col,
                    "pieces_flipped": entry.pieces_flipped,
                    "timestamp": (
                        entry.timestamp if hasattr(entry, "timestamp") else None
                    ),
                }
                for entry in game.ui.move_history
            ],
            "result": {
                "black_score": game.board.score()[0],
                "white_score": game.board.score()[1],
                "winner": (
                    "Black"
                    if game.board.score()[0] > game.board.score()[1]
                    else (
                        "White"
                        if game.board.score()[1] > game.board.score()[0]
                        else "Draw"
                    )
                ),
            },
        }

        return json.dumps(export_data, indent=2)

    @staticmethod
    def save_game(game, format_type: str = "pgn"):
        """Save game to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if format_type == "pgn":
            filename = f"data/reversi_game_{timestamp}.pgn"
            content = GameExporter.export_to_pgn(game)
        else:  # json
            filename = f"data/reversi_game_{timestamp}.json"
            content = GameExporter.export_to_json(game)

        try:
            with open(filename, "w") as f:
                f.write(content)
            game.ui.status = f"Game exported to {filename}"
            return filename
        except Exception as e:
            game.ui.status = f"Export failed: {e}"
            return None


class Game:
    def __init__(self, board: Board, settings: Settings):
        pg.init()
        pg.display.set_caption("Reversi Deluxe")
        self.screen = pg.display.set_mode((W, H), pg.RESIZABLE)
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("Arial", 18)
        self.big_font = pg.font.SysFont("Arial", 24)
        self.board = board
        self.settings = settings
        self.ui = UIState()
        self.ui.game_start_time = time.time()  # Initialize game start time
        self.ai = AI(max_depth=self.settings.ai_depth)
        self.selection_dialog = SelectionDialog()
        self.sfx = SFX(enabled=self.settings.sound)
        self.gameplay_analyzer = GameplayAnalyzer()
        self.game_analysis = GameAnalysisDisplay(self)
        self.move_analysis = MoveAnalysisDisplay(self)
        # New enhancement systems (must be before menu_system)
        self.replay_mode = ReplayMode(self)
        self.hint_system = HintSystem(self)
        self.exporter = GameExporter()
        # Menu system must be initialized after hint_system
        self.menu_system = MenuSystem(self)
        self.ensure_icon()
        self.wood_cache = None
        self.disc_cache = {}  # Cache for pre-rendered discs
        self.was_game_over = False  # Track game state for auto-analysis

    # ---------------------- Assets & helpers ---------------------- #
    def ensure_icon(self):
        if os.path.exists(ICON_PNG):
            return
        try:
            # Simple generated icon
            import PIL.Image
            import PIL.ImageDraw

            img = PIL.Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            d = PIL.ImageDraw.Draw(img)
            d.rectangle(
                [16, 16, 240, 240], fill=(29, 102, 57), outline=(10, 60, 30), width=8
            )
            d.ellipse(
                [60, 60, 196, 196], fill=(240, 240, 240), outline=(0, 0, 0), width=6
            )
            d.ellipse([36, 36, 172, 172], fill=(30, 30, 30), outline=(0, 0, 0), width=6)
            img.save(ICON_PNG)
        except ImportError:
            # Fallback: create a simple icon using pygame
            self._create_pygame_icon()
        except Exception as e:
            print(f"Warning: Could not create icon: {e}")

    def _create_pygame_icon(self):
        """Create a simple icon using pygame when PIL is not available"""
        try:
            surf = pg.Surface((64, 64))
            surf.fill((29, 102, 57))  # Board color
            pg.draw.rect(surf, (10, 60, 30), surf.get_rect(), 4)
            pg.draw.circle(surf, (240, 240, 240), (32, 32), 20)
            pg.draw.circle(surf, (30, 30, 30), (32, 32), 15)
            pg.image.save(surf, ICON_PNG)
        except Exception as e:
            print(f"Warning: Could not create fallback icon: {e}")

    def layout(self):
        w, h = self.screen.get_size()

        # Use full available space for the board (no side panel)
        available_width = w - 2 * MARGIN
        available_height = h - HUD_HEIGHT - 2 * MARGIN

        size = min(available_width, available_height)
        size = max(360, size)
        bx = (w - size) // 2
        by = HUD_HEIGHT + (available_height - size) // 2
        cell = size // self.board.size
        board_rect = pg.Rect(bx, by, cell * self.board.size, cell * self.board.size)
        hud_rect = pg.Rect(0, 0, w, HUD_HEIGHT)

        return board_rect, hud_rect, cell

    def clear_disc_cache(self):
        """Clear the disc cache - useful when window is resized"""
        self.disc_cache.clear()

    # ---------------------- Drawing ------------------------------- #
    def draw(self):
        """Main drawing method - coordinates all rendering"""
        theme = THEMES[self.settings.theme]
        board_rect, hud_rect, cell = self.layout()

        self.draw_wood_bg()
        self.draw_hud(hud_rect, theme)
        self.draw_board(board_rect, cell, theme)
        self.draw_game_pieces(board_rect, cell)
        self.draw_ui_overlays(board_rect, cell, theme)

        # Draw tutorial panel if active
        if self.ui.show_tutorial and self.ui.tutorial.active:
            w, h = self.screen.get_size()
            tutorial_rect = pg.Rect(w - 300, HUD_HEIGHT + 10, 290, 200)
            self.draw_tutorial(tutorial_rect, theme)

        # Draw analytics panel if active
        if self.ui.show_analytics:
            w, h = self.screen.get_size()
            analytics_rect = pg.Rect(w - 300, HUD_HEIGHT + 220, 290, 250)
            self.draw_analytics(analytics_rect, theme)

        self.update_particles()

        # Draw game analysis overlay
        self.game_analysis.draw(self.screen, theme)

        # Draw move analysis overlay
        self.move_analysis.draw(self.screen, theme)

        # Draw AI thinking indicator
        if self.ui.ai_thinking:
            self.draw_ai_thinking_indicator(theme)

        # Draw replay mode timeline
        if self.ui.replay_mode:
            self.replay_mode.draw_timeline(self.screen, theme)

        # Draw dropdown menus on top of everything (must be last)
        self.menu_system.draw_dropdown_overlay(self.screen, theme)

        # Draw selection dialog on top of everything else
        self.selection_dialog.draw(self.screen, theme)

        pg.display.flip()

    def draw_hud(self, hud_rect, theme):
        """Draw the clean header UI area"""
        # Clean background with subtle gradient
        pg.draw.rect(self.screen, theme["hud"], hud_rect)

        # Menu bar
        self.menu_system.draw_menu_bar(self.screen, theme)

        # Status area below menu bar with better spacing
        status_y = MENU_BAR_HEIGHT + 8
        status_height = hud_rect.height - MENU_BAR_HEIGHT - 16

        # Current score and turn indicator
        b, w = self.board.score()

        if not self.board.game_over():
            current_player = NAME[self.board.to_move]
            player_type = ""
            if self.board.to_move == BLACK and self.settings.ai_black:
                player_type = " (Computer)"
            elif self.board.to_move == WHITE and self.settings.ai_white:
                player_type = " (Computer)"

            # Simple elegant display
            turn_text = f"{current_player}'s Turn{player_type}"
            score_text = f"Black {b} — {w} White"

            turn_surface = self.font.render(turn_text, True, theme["text"])
            score_surface = self.font.render(score_text, True, theme["text"])

            # Center both elements
            total_width = turn_surface.get_width() + 20 + score_surface.get_width()
            start_x = (hud_rect.width - total_width) // 2

            self.screen.blit(
                turn_surface,
                (start_x, status_y + (status_height - turn_surface.get_height()) // 2),
            )
            self.screen.blit(
                score_surface,
                (
                    start_x + turn_surface.get_width() + 20,
                    status_y + (status_height - score_surface.get_height()) // 2,
                ),
            )

        else:
            # Game over - elegant final score display
            if b == w:
                result_text = f"DRAW — Black {b}, White {w}"
                result_color = theme["text"]
            elif b > w:
                result_text = f"BLACK WINS — {b} to {w}"
                result_color = theme["accent"]
            else:
                result_text = f"WHITE WINS — {w} to {b}"
                result_color = theme["accent"]

            result_surface = self.big_font.render(result_text, True, result_color)
            result_x = (hud_rect.width - result_surface.get_width()) // 2
            result_y = status_y + (status_height - result_surface.get_height()) // 2
            self.screen.blit(result_surface, (result_x, result_y))

            # Show post-game analysis hint
            analysis_hint = self.font.render(
                "Press 'G' for game analysis", True, theme["text"]
            )
            hint_x = (hud_rect.width - analysis_hint.get_width()) // 2
            hint_y = result_y + result_surface.get_height() + 8
            self.screen.blit(analysis_hint, (hint_x, hint_y))

        # Subtle "AUTO" indicator when both players are AI
        if (
            self.settings.ai_black
            and self.settings.ai_white
            and not self.board.game_over()
        ):
            auto_font = pg.font.SysFont("Arial", 11, bold=True)
            auto_text = auto_font.render(
                "AUTO", True, tuple(c // 2 for c in theme["accent"])
            )
            auto_x = hud_rect.width - auto_text.get_width() - 12
            auto_y = status_y + 2
            self.screen.blit(auto_text, (auto_x, auto_y))

    def draw_board(self, board_rect, cell, theme):
        """Draw the clean game board background and grid"""
        # Clean board background with subtle depth
        pg.draw.rect(
            self.screen, theme["felt"], board_rect, border_radius=BORDER_RADIUS
        )

        # Add subtle inner shadow for depth
        shadow_color = tuple(max(0, c - 15) for c in theme["felt"])
        shadow_rect = board_rect.inflate(-4, -4)
        pg.draw.rect(
            self.screen, shadow_color, shadow_rect, 2, border_radius=BORDER_RADIUS - 2
        )

        # Clean, minimal grid lines (only if enabled)
        if self.settings.show_grid:
            grid_color = theme["grid"]
            line_width = 1
            for i in range(1, self.board.size):  # Skip outer border lines
                x = board_rect.left + i * cell
                y = board_rect.top + i * cell
                pg.draw.line(
                    self.screen,
                    grid_color,
                    (x, board_rect.top + 2),
                    (x, board_rect.bottom - 2),
                    line_width,
                )
                pg.draw.line(
                    self.screen,
                    grid_color,
                    (board_rect.left + 2, y),
                    (board_rect.right - 2, y),
                    line_width,
                )

    def draw_game_pieces(self, board_rect, cell):
        """Draw all game pieces on the board with animations"""
        current_time = time.time()

        for r in range(self.board.size):
            for c in range(self.board.size):
                if self.board.grid[r][c] != EMPTY:
                    rect = pg.Rect(
                        board_rect.left + c * cell,
                        board_rect.top + r * cell,
                        cell,
                        cell,
                    )

                    # Check if this piece is animating
                    animating = False
                    for anim in self.ui.flip_animations:
                        if anim.row == r and anim.col == c:
                            progress = min(
                                1.0, (current_time - anim.start_time) / anim.duration
                            )
                            self.draw_flipping_disc(
                                rect, anim.from_color, anim.to_color, progress
                            )
                            animating = True
                            break

                    if not animating:
                        self.draw_disc(rect, self.board.grid[r][c])

        # Clean up finished animations
        self.ui.flip_animations = [
            anim
            for anim in self.ui.flip_animations
            if current_time - anim.start_time < anim.duration
        ]

    def draw_ui_overlays(self, board_rect, cell, theme):
        """Draw interactive overlays: hints, hover, last move indicator"""
        mouse = pg.mouse.get_pos()
        hover = self.xy_to_rc(mouse, board_rect, cell)
        legal = {(m.row, m.col): m for m in self.board.legal_moves(self.board.to_move)}

        # Store hover position for move preview
        self.ui.hover_pos = hover if hover in legal else None

        # Hints from AI system (top 3 moves with quality)
        if self.hint_system.show_hints:
            self.hint_system.draw_hints(self.screen, board_rect, cell, theme)
        elif self.settings.hints:
            # Standard hints (all legal moves)
            self.draw_hints(board_rect, cell, legal)

        # Tutorial highlighting
        if self.ui.tutorial.active:
            current_step = self.ui.tutorial.get_current_step()
            if current_step and current_step.board_highlight:
                for r, c in current_step.board_highlight:
                    if 0 <= r < self.board.size and 0 <= c < self.board.size:
                        rect = pg.Rect(
                            board_rect.left + c * cell,
                            board_rect.top + r * cell,
                            cell,
                            cell,
                        )
                        # Tutorial highlight - bright yellow border
                        pg.draw.rect(self.screen, (255, 255, 0), rect, 3)
                        # Subtle inner glow
                        inner_rect = rect.inflate(-6, -6)
                        pg.draw.rect(self.screen, (255, 255, 100, 40), inner_rect)

        # Hover effect and move preview
        if hover and hover in legal:
            self.draw_hover_effect(board_rect, cell, hover)
            # Show piece preview
            if self.settings.show_move_preview and not self.ui.replay_mode:
                self.draw_move_preview(board_rect, cell, hover)

    def draw_hints(self, board_rect, cell, legal_moves):
        """Draw elegant hint indicators for legal moves"""
        for r, c in legal_moves.keys():
            rect = pg.Rect(
                board_rect.left + c * cell, board_rect.top + r * cell, cell, cell
            )
            hint_radius = max(3, cell // 15)

            # Elegant, subtle hint with soft glow
            # Outer glow
            pg.draw.circle(
                self.screen, (255, 235, 120, 60), rect.center, hint_radius + 2
            )
            # Main hint dot
            pg.draw.circle(self.screen, (255, 245, 140), rect.center, hint_radius)
            # Inner highlight
            pg.draw.circle(
                self.screen,
                (255, 255, 200),
                (rect.centerx - 1, rect.centery - 1),
                max(1, hint_radius // 2),
            )

    def draw_hover_effect(self, board_rect, cell, hover_pos):
        """Draw minimal hover effect - just small corner dots"""
        r, c = hover_pos
        rect = pg.Rect(
            board_rect.left + c * cell, board_rect.top + r * cell, cell, cell
        )

        # Tiny corner indicators - much more subtle
        dot_size = 2
        margin = cell // 6

        # Four small corner dots
        corners = [
            (rect.left + margin, rect.top + margin),  # Top-left
            (rect.right - margin, rect.top + margin),  # Top-right
            (rect.left + margin, rect.bottom - margin),  # Bottom-left
            (rect.right - margin, rect.bottom - margin),  # Bottom-right
        ]

        for x, y in corners:
            pg.draw.circle(self.screen, (220, 220, 220), (x, y), dot_size)

    def draw_move_preview(self, board_rect, cell, hover_pos):
        """Draw semi-transparent piece preview at hover position"""
        r, c = hover_pos
        center_x = board_rect.left + c * cell + cell // 2
        center_y = board_rect.top + r * cell + cell // 2
        radius = int(cell * DISC_SIZE_RATIO)

        # Draw semi-transparent preview piece
        preview_surf = pg.Surface((radius * 2 + 10, radius * 2 + 10), pg.SRCALPHA)
        preview_center = (radius + 5, radius + 5)

        # Determine piece color
        if self.board.to_move == BLACK:
            color = (*BLACK_DISC_BASE, 128)  # Semi-transparent black
        else:
            color = (*WHITE_DISC_BASE, 128)  # Semi-transparent white

        pg.draw.circle(preview_surf, color, preview_center, radius)
        pg.draw.circle(preview_surf, (100, 100, 100, 128), preview_center, radius, 2)

        # Blit to screen
        self.screen.blit(preview_surf, (center_x - radius - 5, center_y - radius - 5))

    def draw_ai_thinking_indicator(self, theme):
        """Draw spinner/progress indicator when AI is thinking"""
        # Small spinner in top right corner
        spinner_x = self.screen.get_width() - 50
        spinner_y = HUD_HEIGHT // 2
        spinner_radius = 15

        # Calculate rotation based on time
        elapsed = time.time() - self.ui.ai_think_start
        angle = (elapsed * 3) % (2 * math.pi)

        # Draw spinner circle
        pg.draw.circle(
            self.screen, theme["grid"], (spinner_x, spinner_y), spinner_radius, 3
        )

        # Draw arc segments
        num_segments = 8
        for i in range(num_segments):
            segment_angle = angle + (i * 2 * math.pi / num_segments)
            alpha = int(255 * (1 - i / num_segments))

            end_x = spinner_x + int(spinner_radius * 0.7 * math.cos(segment_angle))
            end_y = spinner_y + int(spinner_radius * 0.7 * math.sin(segment_angle))

            color = (
                (*theme["accent"][:3], alpha)
                if len(theme["accent"]) == 3
                else theme["accent"]
            )
            if len(color) == 4:
                # Draw with alpha
                dot_surf = pg.Surface((6, 6), pg.SRCALPHA)
                pg.draw.circle(dot_surf, color, (3, 3), 3)
                self.screen.blit(dot_surf, (end_x - 3, end_y - 3))
            else:
                pg.draw.circle(self.screen, color, (end_x, end_y), 3)

        # "AI thinking..." text
        text = self.font.render("AI thinking...", True, theme["text"])
        self.screen.blit(
            text,
            (spinner_x - text.get_width() - 25, spinner_y - text.get_height() // 2),
        )

    def draw_wood_bg(self):
        # Refined procedural wood background (cached for performance)
        if self.wood_cache and self.wood_cache.get_size() == self.screen.get_size():
            self.screen.blit(self.wood_cache, (0, 0))
            return
        w, h = self.screen.get_size()
        surf = pg.Surface((w, h))
        rng = random.Random(42)  # Consistent seed for repeatable pattern

        # Create elegant wood grain with smoother variation
        base_color = (65, 42, 28)
        for y in range(h):
            # Smoother wood grain pattern
            grain = math.sin(y * 0.008) * 15 + math.sin(y * 0.03) * 8
            variation = rng.randint(-2, 2)
            tone = int(grain + variation)

            color = (
                min(255, max(0, base_color[0] + tone)),
                min(255, max(0, base_color[1] + tone // 2)),
                min(255, max(0, base_color[2] + tone // 3)),
            )
            pg.draw.line(surf, color, (0, y), (w, y))

        # Add subtle wood knots and grain details
        for _ in range(40):  # Fewer, more refined grain circles
            x = rng.randint(0, w)
            y = rng.randint(0, h)
            r = rng.randint(15, 45)
            # More subtle grain rings
            grain_color = (base_color[0] + 15, base_color[1] + 10, base_color[2] + 8)
            pg.draw.circle(surf, grain_color, (x, y), r, 1)
            if r > 25:  # Add inner ring for larger knots
                pg.draw.circle(surf, grain_color, (x, y), r // 2, 1)

        self.wood_cache = surf
        self.screen.blit(surf, (0, 0))

    def draw_inner_shadow(self, rect, radius):
        s = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        for i in range(INNER_SHADOW_LAYERS):
            a = int(INNER_SHADOW_LAYERS - i) * 3
            pg.draw.rect(
                s,
                (0, 0, 0, a),
                pg.Rect(i, i, rect.width - 2 * i, rect.height - 2 * i),
                border_radius=radius,
            )
        self.screen.blit(s, rect.topleft)

    def _create_textured_disc(self, radius, color):
        """Create a textured checker piece with the specified radius and color"""
        size = radius * 2 + 6  # Extra space for shadow
        surf = pg.Surface((size, size), pg.SRCALPHA)
        center_x = center_y = size // 2

        # Drop shadow
        pg.draw.circle(surf, (0, 0, 0, 60), (center_x + 2, center_y + 3), radius + 1)

        style = self.settings.piece_style

        if style == "emoji":
            # Emoji style - use text rendering for emoji-like pieces
            emoji = "⚫" if color == BLACK else "⚪"
            font_size = int(radius * 2.2)  # Scale to fit
            try:
                emoji_font = pg.font.SysFont(
                    "seguiemoji,applesymbolsfb,notocoloremoji", font_size
                )
                emoji_surf = emoji_font.render(emoji, True, (0, 0, 0))
                emoji_rect = emoji_surf.get_rect(center=(center_x, center_y))
                surf.blit(emoji_surf, emoji_rect)
            except (OSError, pg.error):
                # Fallback if emoji font not available
                base_color = (20, 20, 20) if color == BLACK else (245, 245, 245)
                pg.draw.circle(surf, base_color, (center_x, center_y), radius)

        elif style == "modern":
            # Modern flat design - simple gradients and clean look
            if color == BLACK:
                # Black modern piece with subtle gradient
                for i in range(radius, 0, -1):
                    gradient_intensity = 20 + int((radius - i) / radius * 40)
                    pg.draw.circle(
                        surf,
                        (gradient_intensity, gradient_intensity, gradient_intensity),
                        (center_x, center_y),
                        i,
                    )
                # Clean outer ring
                pg.draw.circle(surf, (10, 10, 10), (center_x, center_y), radius, 3)
            else:
                # White modern piece with subtle gradient
                for i in range(radius, 0, -1):
                    gradient_intensity = 245 - int((radius - i) / radius * 30)
                    pg.draw.circle(
                        surf,
                        (gradient_intensity, gradient_intensity, gradient_intensity),
                        (center_x, center_y),
                        i,
                    )
                # Clean outer ring
                pg.draw.circle(surf, (180, 180, 180), (center_x, center_y), radius, 3)

        else:  # traditional
            if color == BLACK:
                # Black checker piece with classic patterns
                base_color = (20, 20, 20)

                # Main disc body
                pg.draw.circle(surf, base_color, (center_x, center_y), radius)

                # Classic checker patterns - radial lines from center
                pattern_color = (65, 65, 65)  # Lighter for better visibility on black
                num_lines = 16  # Number of radial lines

                for i in range(num_lines):
                    angle = (2 * math.pi * i) / num_lines
                    # Draw radial lines from center outward
                    start_x = center_x + math.cos(angle) * (radius * 0.2)
                    start_y = center_y + math.sin(angle) * (radius * 0.2)
                    end_x = center_x + math.cos(angle) * (radius * 0.85)
                    end_y = center_y + math.sin(angle) * (radius * 0.85)
                    pg.draw.line(
                        surf, pattern_color, (start_x, start_y), (end_x, end_y), 1
                    )

                # Add concentric circles for classic checker look
                for ring in range(1, 4):
                    ring_radius = radius * (0.3 + ring * 0.2)
                    pg.draw.circle(
                        surf, pattern_color, (center_x, center_y), int(ring_radius), 1
                    )

            else:  # WHITE
                # White checker piece with classic patterns
                base_color = (245, 245, 245)

                # Main disc body
                pg.draw.circle(surf, base_color, (center_x, center_y), radius)

                # Classic checker patterns - radial lines from center
                pattern_color = (200, 200, 200)  # Darker gray for visibility on white
                num_lines = 16  # Number of radial lines

                for i in range(num_lines):
                    angle = (2 * math.pi * i) / num_lines
                    # Draw radial lines from center outward
                    start_x = center_x + math.cos(angle) * (radius * 0.2)
                    start_y = center_y + math.sin(angle) * (radius * 0.2)
                    end_x = center_x + math.cos(angle) * (radius * 0.85)
                    end_y = center_y + math.sin(angle) * (radius * 0.85)
                    pg.draw.line(
                        surf, pattern_color, (start_x, start_y), (end_x, end_y), 1
                    )

                # Add concentric circles for classic checker look
                for ring in range(1, 4):
                    ring_radius = radius * (0.3 + ring * 0.2)
                    pg.draw.circle(
                        surf, pattern_color, (center_x, center_y), int(ring_radius), 1
                    )

            # Clean rim for definition
            rim_color = (0, 0, 0) if color == BLACK else (180, 180, 180)
            pg.draw.circle(surf, rim_color, (center_x, center_y), radius, 2)

        # Subtle bevel edge for 3D effect
        if color == BLACK:
            # Light edge on top-left
            pg.draw.arc(
                surf,
                (60, 60, 60),
                (center_x - radius, center_y - radius, radius * 2, radius * 2),
                math.pi,
                math.pi * 1.5,
                1,
            )
        else:
            # Soft shadow on bottom-right
            pg.draw.arc(
                surf,
                (200, 200, 200),
                (center_x - radius, center_y - radius, radius * 2, radius * 2),
                0,
                math.pi * 0.5,
                1,
            )

        return surf

    def draw_disc(self, rect, color, alpha: Optional[int] = None):
        r = int(min(rect.width, rect.height) * DISC_SIZE_RATIO)

        # Use cached disc if available (include style in cache key)
        cache_key = (r, color, self.settings.piece_style)
        if cache_key not in self.disc_cache:
            self.disc_cache[cache_key] = self._create_textured_disc(r, color)

        disc_surf = self.disc_cache[cache_key]

        # Position the pre-rendered disc
        disc_rect = disc_surf.get_rect()
        disc_rect.center = rect.center

        if alpha is not None:
            temp_surf = disc_surf.copy()
            temp_surf.set_alpha(alpha)
            self.screen.blit(temp_surf, disc_rect)
        else:
            self.screen.blit(disc_surf, disc_rect)

    def draw_flipping_disc(self, rect, from_color, to_color, progress):
        """Draw a disc in the middle of flipping animation"""
        r = int(min(rect.width, rect.height) * DISC_SIZE_RATIO)

        # Animation phases: 0.0-0.5 = shrink old, 0.5-1.0 = grow new
        if progress < 0.5:
            # First half - show old color shrinking
            scale = 1.0 - (progress * 1.6)  # Faster shrink
            scaled_r = max(1, int(r * scale))

            cache_key = (scaled_r, from_color, self.settings.piece_style)
            if cache_key not in self.disc_cache:
                self.disc_cache[cache_key] = self._create_textured_disc(
                    scaled_r, from_color
                )

            disc_surf = self.disc_cache[cache_key]
            disc_rect = disc_surf.get_rect(center=rect.center)
            self.screen.blit(disc_surf, disc_rect)
        else:
            # Second half - show new color growing
            scale = (progress - 0.5) * 1.6  # Faster grow
            scaled_r = max(1, int(r * scale))

            cache_key = (scaled_r, to_color, self.settings.piece_style)
            if cache_key not in self.disc_cache:
                self.disc_cache[cache_key] = self._create_textured_disc(
                    scaled_r, to_color
                )

            disc_surf = self.disc_cache[cache_key]
            disc_rect = disc_surf.get_rect(center=rect.center)
            self.screen.blit(disc_surf, disc_rect)

    def draw_move_history(self, history_rect, theme):
        """Draw the move history panel"""
        # Panel background
        pg.draw.rect(self.screen, theme["felt"], history_rect)
        pg.draw.rect(self.screen, theme["grid"], history_rect, 2)

        # Title
        font = pg.font.Font(None, 24)
        title_text = font.render("Move History", True, theme["text"])
        title_rect = title_text.get_rect(
            centerx=history_rect.centerx, top=history_rect.top + 10
        )
        self.screen.blit(title_text, title_rect)

        # History content area
        content_rect = pg.Rect(
            history_rect.left + 10,
            title_rect.bottom + 10,
            history_rect.width - 20,
            history_rect.height - title_rect.height - 30,
        )

        if not self.ui.move_history:
            # No moves yet
            no_moves_text = pg.font.Font(None, 18).render(
                "No moves yet", True, theme["text"]
            )
            text_rect = no_moves_text.get_rect(center=content_rect.center)
            self.screen.blit(no_moves_text, text_rect)
            return

        # Calculate visible moves based on scroll
        font_small = pg.font.Font(None, 18)
        line_height = 22
        visible_lines = content_rect.height // line_height

        start_idx = max(
            0, len(self.ui.move_history) - visible_lines + self.ui.history_scroll
        )
        end_idx = min(len(self.ui.move_history), start_idx + visible_lines)

        # Draw move entries
        y = content_rect.top
        for i in range(start_idx, end_idx):
            entry = self.ui.move_history[i]

            # Format move text
            player_symbol = "●" if entry.player == BLACK else "○"
            position = f"{chr(ord('A') + entry.col)}{entry.row + 1}"
            flipped = f" ({entry.pieces_flipped})" if entry.pieces_flipped > 0 else ""
            move_text = f"{entry.move_number:2d}. {player_symbol} {position}{flipped}"

            # Render move text
            text_color = theme["text"]
            if i == len(self.ui.move_history) - 1:  # Highlight last move
                text_color = theme["accent"]

            text_surf = font_small.render(move_text, True, text_color)
            self.screen.blit(text_surf, (content_rect.left, y))
            y += line_height

    def draw_statistics(self, stats_rect, theme):
        """Draw the performance statistics panel"""
        # Panel background
        pg.draw.rect(self.screen, theme["felt"], stats_rect)
        pg.draw.rect(self.screen, theme["grid"], stats_rect, 2)

        # Title
        font = pg.font.Font(None, 24)
        title_text = font.render("Player Statistics", True, theme["text"])
        title_rect = title_text.get_rect(
            centerx=stats_rect.centerx, top=stats_rect.top + 10
        )
        self.screen.blit(title_text, title_rect)

        # Content area
        content_rect = pg.Rect(
            stats_rect.left + 10,
            title_rect.bottom + 10,
            stats_rect.width - 20,
            stats_rect.height - title_rect.height - 30,
        )

        if not self.settings.stats or self.settings.stats.games_played == 0:
            # No games yet
            no_games_text = pg.font.Font(None, 18).render(
                "No games played yet", True, theme["text"]
            )
            text_rect = no_games_text.get_rect(center=content_rect.center)
            self.screen.blit(no_games_text, text_rect)
            return

        stats = self.settings.stats
        font_small = pg.font.Font(None, 16)
        line_height = 20
        y = content_rect.top

        # Statistics to display
        stat_lines = [
            f"Games Played: {stats.games_played}",
            f"Win Rate: {stats.win_rate:.1%}",
            (
                f"Wins: {stats.games_won} | Losses: {stats.games_lost} | "
                f"Ties: {stats.games_tied}"
            ),
            f"Best Score: {stats.best_score}",
            f"Avg Score: {stats.average_score:.1f}",
            f"Avg Game Length: {stats.average_game_length:.1f} min",
            f"Avg Moves/Game: {stats.average_moves_per_game:.1f}",
            "",
            "Recent Results:",
        ]

        # Draw main statistics
        for line in stat_lines:
            if line:
                text_surf = font_small.render(line, True, theme["text"])
                self.screen.blit(text_surf, (content_rect.left, y))
            y += line_height

        # Draw recent results
        for result in stats.recent_results[-5:]:  # Show last 5 games
            if y + line_height > content_rect.bottom:
                break

            # Format result
            winner_text = (
                "Win"
                if result.winner == result.human_color
                else "Loss" if result.winner == result.ai_color else "Tie"
            )
            score_text = f"{result.final_score_human}-{result.final_score_ai}"
            date_text = time.strftime("%m/%d", time.localtime(result.timestamp))
            result_line = f"{date_text}: {winner_text} ({score_text})"

            # Color code wins/losses
            color = (
                theme["accent"]
                if result.winner == result.human_color
                else (
                    theme["danger"]
                    if result.winner == result.ai_color
                    else theme["text"]
                )
            )

            text_surf = font_small.render(result_line, True, color)
            self.screen.blit(text_surf, (content_rect.left + 10, y))
            y += line_height

    def draw_tutorial(self, tutorial_rect, theme):
        """Draw the strategy tutorial panel"""
        # Panel background
        pg.draw.rect(self.screen, theme["hud"], tutorial_rect)
        pg.draw.rect(self.screen, theme["grid"], tutorial_rect, 2)

        current_step = self.ui.tutorial.get_current_step()
        if not current_step:
            return

        # Title
        title_font = pg.font.Font(None, 22)
        title_text = title_font.render(
            f"Strategy Tip {self.ui.tutorial.current_step + 1}", True, theme["accent"]
        )
        title_rect = title_text.get_rect(
            centerx=tutorial_rect.centerx, top=tutorial_rect.top + 10
        )
        self.screen.blit(title_text, title_rect)

        # Step title
        step_font = pg.font.Font(None, 18)
        step_title = step_font.render(current_step.title, True, theme["text"])
        step_rect = step_title.get_rect(
            centerx=tutorial_rect.centerx, top=title_rect.bottom + 10
        )
        self.screen.blit(step_title, step_rect)

        # Description
        desc_font = pg.font.Font(None, 14)
        y_pos = step_rect.bottom + 15

        # Word wrap the description
        words = current_step.description.split(" ")
        lines = []
        current_line = ""
        max_width = tutorial_rect.width - 20

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if desc_font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for line in lines:
            if y_pos + 16 > tutorial_rect.bottom - 40:
                break
            line_surf = desc_font.render(line, True, theme["text"])
            self.screen.blit(line_surf, (tutorial_rect.left + 10, y_pos))
            y_pos += 16

        # Explanation
        if current_step.explanation:
            y_pos += 10
            explain_lines = []
            words = current_step.explanation.split(" ")
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if desc_font.size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        explain_lines.append(current_line)
                    current_line = word
            if current_line:
                explain_lines.append(current_line)

            for line in explain_lines:
                if y_pos + 16 > tutorial_rect.bottom - 20:
                    break
                line_surf = desc_font.render(line, True, theme["accent"])
                self.screen.blit(line_surf, (tutorial_rect.left + 10, y_pos))
                y_pos += 16

        # Navigation hint
        nav_text = desc_font.render(
            "Press T for next tip, ESC to close",
            True,
            tuple(c // 2 for c in theme["text"]),
        )
        nav_rect = nav_text.get_rect(
            centerx=tutorial_rect.centerx, bottom=tutorial_rect.bottom - 5
        )
        self.screen.blit(nav_text, nav_rect)

    def draw_analytics(self, analytics_rect, theme):
        """Draw the gameplay analytics panel"""
        # Panel background
        pg.draw.rect(self.screen, theme["hud"], analytics_rect)
        pg.draw.rect(self.screen, theme["grid"], analytics_rect, 2)

        # Title
        title_font = pg.font.Font(None, 20)
        title_text = title_font.render("Move Analysis", True, theme["accent"])
        title_rect = title_text.get_rect(
            centerx=analytics_rect.centerx, top=analytics_rect.top + 10
        )
        self.screen.blit(title_text, title_rect)

        # Show analysis of recent moves
        if self.ui.analyzer.move_history:
            content_y = title_rect.bottom + 15
            font_small = pg.font.Font(None, 14)
            line_height = 16

            # Show last few moves
            recent_moves = self.ui.analyzer.move_history[-8:]
            for analysis in recent_moves:
                if content_y + line_height > analytics_rect.bottom - 10:
                    break

                # Format move info
                col_letter = chr(ord("A") + analysis.col)
                move_text = (
                    f"Move {analysis.move_number}: " f"{col_letter}{analysis.row + 1}"
                )
                quality_color = {
                    "Excellent": theme["accent"],
                    "Good": (100, 200, 100),
                    "Fair": (200, 200, 100),
                    "Poor": theme["danger"],
                }.get(analysis.move_quality, theme["text"])

                # Move info
                move_surf = font_small.render(move_text, True, theme["text"])
                self.screen.blit(move_surf, (analytics_rect.left + 10, content_y))

                # Quality indicator
                quality_surf = font_small.render(
                    f"({analysis.move_quality})", True, quality_color
                )
                self.screen.blit(quality_surf, (analytics_rect.left + 100, content_y))

                # Pieces captured
                pieces_surf = font_small.render(
                    f"+{analysis.pieces_captured}", True, theme["text"]
                )
                self.screen.blit(pieces_surf, (analytics_rect.left + 160, content_y))

                content_y += line_height
        else:
            no_data_text = pg.font.Font(None, 16).render(
                "No move data yet", True, theme["text"]
            )
            no_data_rect = no_data_text.get_rect(
                center=(analytics_rect.centerx, analytics_rect.centery)
            )
            self.screen.blit(no_data_text, no_data_rect)

    # ---------------------- Input & actions ----------------------- #
    def xy_to_rc(self, pos, board_rect, cell):
        """Convert screen coordinates to board row/column, with bounds checking"""
        if not pos or cell <= 0:
            return None

        x, y = pos
        if not board_rect.collidepoint(x, y):
            return None

        c = (x - board_rect.left) // cell
        r = (y - board_rect.top) // cell

        if 0 <= r < self.board.size and 0 <= c < self.board.size:
            return (int(r), int(c))
        return None

    def play(self, r, c):
        legal = {(m.row, m.col): m for m in self.board.legal_moves(self.board.to_move)}
        mv = legal.get((r, c))
        if not mv:
            self.ui.status = "Illegal move"
            self.sfx.play("bad")
            return False
        t = pg.time.get_ticks() / 1000.0

        # Analyze the move before making it
        move_analysis = self.gameplay_analyzer.analyze_move(
            self.board, mv, self.board.to_move
        )

        # Record move in history before making the move
        move_number = len(self.ui.move_history) + 1
        current_player = self.board.to_move
        pieces_flipped = len(mv.flips)

        # Save current board state for replay (deep copy)
        board_state = [row[:] for row in self.board.grid]

        history_entry = MoveHistoryEntry(
            move_number=move_number,
            player=current_player,
            row=r,
            col=c,
            pieces_flipped=pieces_flipped,
            board_state=board_state,
        )
        self.ui.move_history.append(history_entry)

        # Create flip animations for pieces that will change color
        for rr, cc in mv.flips:
            from_color = self.board.grid[rr][cc]  # Current color before flip
            to_color = self.board.to_move  # Color it will become
            self.ui.flip_animations.append(
                FlipAnimation(
                    row=rr,
                    col=cc,
                    start_time=t,
                    from_color=from_color,
                    to_color=to_color,
                )
            )
            self.spawn_confetti(rr, cc)

        self.board.make_move(mv)
        self.ui.last_move = (r, c)

        # Create move status with optional analysis
        base_status = f"{NAME[OPP[self.board.to_move]]} played {(r+1)}{chr(ord('A')+c)}"
        if self.ui.show_move_analysis and move_analysis:
            analysis_text = (
                f" - {move_analysis.move_quality} move "
                f"({move_analysis.pieces_captured} pieces)"
            )
            self.ui.status = base_status + analysis_text
        else:
            self.ui.status = base_status

        # Store the move analysis for later use
        self.ui.last_move_analysis = move_analysis

        # Update move analysis window if it's active
        if self.move_analysis.active and move_analysis:
            self.move_analysis.show_analysis(move_analysis)

        # Regenerate hints if they're currently shown
        if self.hint_system.show_hints:
            self.hint_system.generate_hints()

        self.sfx.play("place")
        self.sfx.play("flip")
        if self.board.game_over():
            self.sfx.play("win")
            self.record_game_result()
        return True

    def maybe_pass(self):
        if not self.board.legal_moves(self.board.to_move):
            self.board.pass_turn()
            self.ui.status = f"{NAME[OPP[self.board.to_move]]} passes"
            self.sfx.play("pass")

    def ai_turn_if_needed(self):
        if (self.board.to_move == BLACK and self.settings.ai_black) or (
            self.board.to_move == WHITE and self.settings.ai_white
        ):
            # Start thinking indicator
            self.ui.ai_thinking = True
            self.ui.ai_think_start = time.time()
            self.ui.status = f"{NAME[self.board.to_move]} (Computer) thinking…"
            pg.display.flip()

            mv = self.ai.choose(self.board, self.board.to_move)

            # Stop thinking indicator
            self.ui.ai_thinking = False

            if mv:
                self.play(mv.row, mv.col)
            else:
                self.board.pass_turn()
                self.ui.status = f"{NAME[OPP[self.board.to_move]]} (Computer) passes"
                self.sfx.play("pass")

            # Handle automatic pass if needed
            self.maybe_pass()

    # Particles (confetti)
    def spawn_confetti(self, r, c):
        board_rect, _, cell = self.layout()
        x = board_rect.left + c * cell + cell / 2
        y = board_rect.top + r * cell + cell / 2
        for _ in range(CONFETTI_COUNT):
            ang = random.random() * 2 * math.pi
            sp = CONFETTI_MIN_SPEED + random.random() * (
                CONFETTI_MAX_SPEED - CONFETTI_MIN_SPEED
            )
            vx = math.cos(ang) * sp
            vy = math.sin(ang) * sp
            life = CONFETTI_MIN_LIFE + random.random() * (
                CONFETTI_MAX_LIFE - CONFETTI_MIN_LIFE
            )
            particle = Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                life=life,
                age=0.0,
                color_id=random.randint(0, 2),
            )
            self.ui.particles.append(particle)

    def update_particles(self):
        dt = self.clock.get_time() / 1000.0
        for p in self.ui.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += GRAVITY * dt  # gravity
            p.age += dt
        self.ui.particles = [p for p in self.ui.particles if p.age < p.life]
        for p in self.ui.particles:
            a = int(255 * (1 - p.age / p.life))
            colors = [(250, 240, 90), (120, 190, 255), (255, 120, 140)]
            col = colors[p.color_id]
            pg.draw.circle(self.screen, (*col, a), (int(p.x), int(p.y)), 3)

    # Button handlers
    def on_undo(self):
        if not self.board.undo():
            self.ui.status = "Nothing to undo"

    def on_redo(self):
        if not self.board.redo():
            self.ui.status = "Nothing to redo"

    def set_ai_depth(self, depth: int):
        """Set AI difficulty level"""
        self.settings.ai_depth = depth
        try:
            self.ai = AI(max_depth=depth)
            self.settings.save()
            self.ui.status = f"AI difficulty set to level {depth}"
            self.menu_system.setup_menus()  # Refresh menu labels
            self.menu_system.active_submenu_items = None  # Close submenu
        except Exception as e:
            print(f"Error setting AI depth: {e}")
            self.ui.status = "Error changing AI difficulty"

    def set_theme(self, theme_key: str):
        """Set the game theme"""
        self.settings.theme = theme_key
        # Clear caches to refresh with new theme colors
        self.wood_cache = None
        self.clear_disc_cache()
        self.settings.save()
        self.ui.status = f"Theme changed to {THEMES[theme_key]['display']}"
        self.menu_system.setup_menus()  # Refresh menu labels
        self.menu_system.active_submenu_items = None  # Close submenu
        if not self.board.redo():
            self.ui.status = "Nothing to redo"

    def on_toggle_hints(self):
        self.settings.hints = not self.settings.hints
        self.settings.save()

    def on_toggle_ai_black(self):
        self.settings.ai_black = not self.settings.ai_black
        self.settings.save()

    def on_toggle_ai_white(self):
        self.settings.ai_white = not self.settings.ai_white
        self.settings.save()

    def on_cycle_depth(self):
        """Show AI difficulty level selection dialog"""
        # Define AI levels with descriptions
        ai_levels = [
            ("Beginner (Level 1)", 1),
            ("Easy (Level 2)", 2),
            ("Medium (Level 3)", 3),
            ("Hard (Level 4)", 4),
            ("Expert (Level 5)", 5),
            ("Master (Level 6)", 6),
        ]

        def set_ai_depth(depth):
            """Callback to set AI depth"""
            self.settings.ai_depth = depth
            try:
                self.ai = AI(max_depth=depth)
                self.settings.save()
                self.ui.status = f"AI difficulty set to level {depth}"
                self.menu_system.setup_menus()  # Refresh menu labels
            except Exception as e:
                print(f"Error setting AI depth: {e}")
                self.ui.status = "Error changing AI difficulty"

        self.selection_dialog.show(
            "Select AI Difficulty",
            ai_levels,
            self.settings.ai_depth,
            set_ai_depth,
        )

    def on_cycle_board_size(self):
        """Cycle through different board sizes and start new game"""
        size_options = [4, 6, 8, 10, 12, 14, 16]
        current_index = (
            size_options.index(self.board.size)
            if self.board.size in size_options
            else 2
        )  # Default to 8x8
        new_index = (current_index + 1) % len(size_options)
        new_size = size_options[new_index]

        # Create new board with new size
        self.board = Board(size=new_size)
        self.settings.board_size = new_size
        self.settings.save()

        # Clear game state
        self.ui.last_move = None
        self.ui.flip_animations.clear()
        self.ui.particles.clear()
        self.ui.move_history.clear()
        self.ui.history_scroll = 0
        self.clear_disc_cache()  # Clear cached discs for new size
        self.wood_cache = None  # Clear wood background cache

        self.ui.status = f"New {new_size}x{new_size} game started"

    def on_cycle_theme(self):
        """Show theme selection dialog"""
        # Define all available themes
        theme_options = [
            (THEMES[theme_key]["display"], theme_key) for theme_key in THEMES.keys()
        ]

        def set_theme(theme_key):
            """Callback to set theme"""
            self.settings.theme = theme_key
            # Clear caches to refresh with new theme colors
            self.wood_cache = None
            self.clear_disc_cache()
            self.settings.save()
            self.ui.status = f"Theme changed to {THEMES[theme_key]['display']}"
            self.menu_system.setup_menus()  # Refresh menu labels

        self.selection_dialog.show(
            "Select Theme",
            theme_options,
            self.settings.theme,
            set_theme,
        )

    def on_toggle_sound(self):
        self.settings.sound = not self.settings.sound
        self.sfx.enabled = self.settings.sound
        self.settings.save()

    def on_toggle_stats(self):
        """Toggle the statistics panel display"""
        self.ui.show_stats = not self.ui.show_stats
        self.ui.status = f"Statistics {'shown' if self.ui.show_stats else 'hidden'}"

    def record_game_result(self):
        """Record the current game result for statistics tracking"""
        if not self.ui.game_start_time or not self.board.game_over():
            return

        # Record the game end time
        self.ui.game_end_time = time.time()

        # Determine human and AI colors
        human_color = BLACK if not self.settings.ai_black else WHITE
        ai_color = WHITE if not self.settings.ai_black else BLACK

        # Calculate scores
        black_score, white_score = self.board.score()
        human_score = black_score if human_color == BLACK else white_score
        ai_score = white_score if human_color == BLACK else black_score

        # Determine winner
        if black_score > white_score:
            winner = BLACK
        elif white_score > black_score:
            winner = WHITE
        else:
            winner = EMPTY  # Tie

        # Create game result
        result = GameResult(
            timestamp=time.time(),
            board_size=self.board.size,
            human_color=human_color,
            ai_color=ai_color,
            winner=winner,
            final_score_human=human_score,
            final_score_ai=ai_score,
            total_moves=len(self.ui.move_history),
            game_duration=time.time() - self.ui.game_start_time,
            ai_depth=self.settings.ai_depth,
        )

        # Update statistics
        if not self.settings.stats:
            self.settings.stats = PlayerStats()
        self.settings.stats.add_game_result(result)

        # Also update per-difficulty stats
        if self.settings.per_difficulty_stats is None:
            self.settings.per_difficulty_stats = {}

        current_depth = self.settings.ai_depth
        if current_depth not in self.settings.per_difficulty_stats:
            self.settings.per_difficulty_stats[current_depth] = PlayerStats()

        self.settings.per_difficulty_stats[current_depth].add_game_result(result)
        self.settings.save()

    def on_new(self):
        # Preserve user preferences that should persist across games
        show_move_analysis = self.ui.show_move_analysis

        self.board = Board(size=self.board.size)
        self.ui.last_move = None
        self.ui.flip_animations.clear()
        self.ui.move_history.clear()
        self.ui.history_scroll = 0
        self.ui.game_start_time = time.time()
        self.ui.game_end_time = None

        # Restore preserved preferences
        self.ui.show_move_analysis = show_move_analysis

        self.ui.status = "New game"

    def on_save(self):
        ts = time.strftime("%Y%m%d-%H%M%S")
        fn = self.ui.last_save or f"reversi-{ts}.json"
        try:
            # Ensure directory exists
            save_dir = os.path.dirname(fn) if os.path.dirname(fn) else "."
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            with open(fn, "w", encoding="utf-8") as f:
                json.dump(self.board.serialize(), f, indent=2)
            self.ui.last_save = fn
            self.ui.status = f"Saved to {fn}"
        except PermissionError:
            self.ui.status = "Save failed: Permission denied"
        except OSError as e:
            self.ui.status = f"Save failed: File system error - {e}"
        except ValueError as e:
            self.ui.status = f"Save failed: Invalid data - {e}"

    def on_load(self):
        try:
            if not os.path.exists("."):
                self.ui.status = "Load failed: Current directory not accessible"
                return

            cands = [
                x for x in os.listdir(".") if x.endswith(".json") and os.path.isfile(x)
            ]
            if not cands:
                self.ui.status = "No .json save files found in current directory"
                return

            fn = sorted(cands)[-1]  # Load most recent
            with open(fn, "r", encoding="utf-8") as f:
                obj = json.load(f)

            # Validate the loaded data
            if not isinstance(obj, dict) or "grid" not in obj:
                self.ui.status = f"Load failed: Invalid save file format in {fn}"
                return

            self.board = Board.deserialize(obj)
            self.ui.last_move = None
            self.ui.flip_animations.clear()
            self.ui.particles.clear()
            self.ui.move_history.clear()
            self.ui.history_scroll = 0
            self.ui.status = f"Loaded {fn}"
        except json.JSONDecodeError:
            self.ui.status = f"Load failed: Invalid JSON format in {fn}"
        except PermissionError:
            self.ui.status = "Load failed: Permission denied"
        except FileNotFoundError:
            self.ui.status = "Load failed: Save file not found"
        except (IOError, ValueError) as e:
            self.ui.status = f"Load failed: {e}"

    def on_show_tutorial(self):
        """Show the strategy tutorial"""
        self.ui.show_tutorial = not self.ui.show_tutorial
        if self.ui.show_tutorial:
            self.ui.tutorial.start_tutorial()
            self.ui.status = "Strategy tutorial started - press T to advance"
        else:
            self.ui.status = "Tutorial closed"

    def on_show_analytics(self):
        """Toggle analytics display"""
        self.ui.show_analytics = not self.ui.show_analytics
        self.ui.status = f"Analytics {'shown' if self.ui.show_analytics else 'hidden'}"

    def on_show_game_analysis(self):
        """Show game analysis (only available when game is over)"""
        if self.board.game_over():
            if self.game_analysis.active:
                self.game_analysis.hide_analysis()
                self.ui.status = "Game analysis closed"
            else:
                self.game_analysis.show_analysis()
                self.ui.status = "Game analysis shown - press G or ESC to close"
        else:
            self.ui.status = "Game analysis only available after game ends"

    def on_toggle_move_analysis(self):
        """Toggle move-by-move analysis display"""
        if self.move_analysis.active:
            self.move_analysis.hide_analysis()
            self.ui.status = "Move analysis window closed"
        else:
            # Show analysis for the last move if available
            if self.ui.last_move_analysis:
                self.move_analysis.show_analysis(self.ui.last_move_analysis)
                self.ui.status = "Move analysis window opened - press V or ESC to close"
            else:
                self.ui.status = "No moves to analyze yet - make a move first"

    def on_show_about(self):
        """Show the About dialog with game information"""
        about_text = [
            "Reversi Deluxe v2.0",
            "",
            "A polished, feature-rich implementation of",
            "the classic Reversi/Othello board game.",
            "",
            "Features:",
            "• Advanced AI with 6 difficulty levels",
            "• Multiple visual themes",
            "• Comprehensive game analysis",
            "• Move-by-move analysis",
            "• Strategy tutorial",
            "• Save/Load games",
            "• Undo/Redo moves",
            "• Sound effects",
            "• Variable board sizes (4x4 to 16x16)",
            "",
            "Built with Python & Pygame",
            "",
            "Press ESC or click outside to close",
        ]

        # Create a simple modal dialog
        import pygame as pg

        theme = THEMES[self.settings.theme]
        screen_w, screen_h = self.screen.get_size()

        # Dialog dimensions
        dialog_w = 450
        line_height = 24
        dialog_h = len(about_text) * line_height + 40
        dialog_x = (screen_w - dialog_w) // 2
        dialog_y = (screen_h - dialog_h) // 2

        font = pg.font.SysFont("Arial", 16)
        title_font = pg.font.SysFont("Arial", 20, bold=True)

        # Capture current screen state once
        background = self.screen.copy()

        # Show dialog loop
        showing_about = True
        while showing_about:
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    return
                if ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE:
                    showing_about = False
                if ev.type == pg.MOUSEBUTTONDOWN:
                    dialog_rect = pg.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
                    if not dialog_rect.collidepoint(ev.pos):
                        showing_about = False

            # Restore background (no redrawing)
            self.screen.blit(background, (0, 0))

            # Semi-transparent overlay
            overlay = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            # Dialog background
            dialog_rect = pg.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
            pg.draw.rect(self.screen, theme["hud"], dialog_rect, border_radius=10)
            pg.draw.rect(self.screen, theme["accent"], dialog_rect, 3, border_radius=10)

            # Draw text
            y = dialog_y + 20
            for i, line in enumerate(about_text):
                if i == 0:  # Title
                    text_surf = title_font.render(line, True, theme["accent"])
                else:
                    text_surf = font.render(line, True, theme["text"])
                text_x = dialog_x + (dialog_w - text_surf.get_width()) // 2
                self.screen.blit(text_surf, (text_x, y))
                y += line_height

            pg.display.flip()
            self.clock.tick(60)

        self.ui.status = "About dialog closed"

    # New enhancement handlers
    def on_toggle_replay(self):
        """Toggle replay mode"""
        if self.ui.replay_mode:
            self.replay_mode.exit_replay_mode()
        else:
            self.replay_mode.enter_replay_mode()
        self.menu_system.setup_menus()  # Refresh menu

    def on_toggle_move_hints(self):
        """Toggle move hints display"""
        self.hint_system.toggle()
        self.menu_system.setup_menus()  # Refresh menu

    def on_export_pgn(self):
        """Export game to PGN format"""
        filename = self.exporter.save_game(self, format_type="pgn")
        if filename:
            self.ui.status = f"Exported to {filename}"

    def on_export_json(self):
        """Export game to JSON format"""
        filename = self.exporter.save_game(self, format_type="json")
        if filename:
            self.ui.status = f"Exported to {filename}"

    def on_show_difficulty_stats(self):
        """Show per-difficulty statistics"""
        if not self.settings.per_difficulty_stats:
            self.ui.status = "No difficulty stats available yet"
            return

        # Create a modal dialog showing stats for each difficulty
        import pygame as pg

        theme = THEMES[self.settings.theme]
        screen_w, screen_h = self.screen.get_size()

        # Dialog dimensions
        dialog_w = 500
        dialog_h = 450
        dialog_x = (screen_w - dialog_w) // 2
        dialog_y = (screen_h - dialog_h) // 2

        font = pg.font.SysFont("Arial", 14)
        title_font = pg.font.SysFont("Arial", 18, bold=True)

        background = self.screen.copy()

        showing_stats = True
        scroll_y = 0

        while showing_stats:
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    return
                if ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE:
                    showing_stats = False
                if ev.type == pg.MOUSEBUTTONDOWN:
                    dialog_rect = pg.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
                    if not dialog_rect.collidepoint(ev.pos):
                        showing_stats = False
                if ev.type == pg.MOUSEWHEEL:
                    scroll_y = max(0, scroll_y - ev.y * 20)

            self.screen.blit(background, (0, 0))

            # Overlay
            overlay = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            # Dialog background
            dialog_rect = pg.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
            pg.draw.rect(self.screen, theme["hud"], dialog_rect, border_radius=10)
            pg.draw.rect(self.screen, theme["accent"], dialog_rect, 3, border_radius=10)

            # Title
            title = title_font.render("Per-Difficulty Statistics", True, theme["text"])
            self.screen.blit(title, (dialog_x + 20, dialog_y + 15))

            # Stats content
            y = dialog_y + 50 - scroll_y
            line_height = 20

            difficulty_names = {
                1: "Beginner",
                2: "Easy",
                3: "Medium",
                4: "Hard",
                5: "Expert",
                6: "Master",
            }

            for depth in range(1, 7):
                if depth not in self.settings.per_difficulty_stats:
                    continue

                stats = self.settings.per_difficulty_stats[depth]

                if y > dialog_y + 40 and y < dialog_y + dialog_h - 40:
                    # Difficulty header
                    header = title_font.render(
                        f"Level {depth} - {difficulty_names[depth]}",
                        True,
                        theme["accent"],
                    )
                    self.screen.blit(header, (dialog_x + 20, y))

                y += line_height + 5

                # Stats lines
                stat_lines = [
                    f"  Games played: {stats.games_played}",
                    (
                        f"  Win rate: {stats.win_rate:.1%}"
                        if stats.games_played > 0
                        else "  Win rate: N/A"
                    ),
                    (
                        f"  Wins: {stats.games_won} | "
                        f"Losses: {stats.games_lost} | Ties: {stats.games_tied}"
                    ),
                ]

                for line in stat_lines:
                    if y > dialog_y + 40 and y < dialog_y + dialog_h - 40:
                        text_surf = font.render(line, True, theme["text"])
                        self.screen.blit(text_surf, (dialog_x + 20, y))
                    y += line_height

                y += 10  # Space between difficulties

            # Close hint
            hint = font.render(
                "Press ESC or click outside to close", True, theme["text"]
            )
            self.screen.blit(hint, (dialog_x + 20, dialog_y + dialog_h - 30))

            pg.display.flip()
            self.clock.tick(60)

        self.ui.status = "Stats dialog closed"

    def set_font_size(self, multiplier: float):
        """Set font size multiplier"""
        self.settings.font_size_multiplier = multiplier
        # Reinitialize fonts with new size
        base_size = int(18 * multiplier)
        big_size = int(24 * multiplier)
        self.font = pg.font.SysFont("Arial", base_size)
        self.big_font = pg.font.SysFont("Arial", big_size)
        self.settings.save()
        self.menu_system.setup_menus()
        self.ui.status = f"Font size set to {int(multiplier * 100)}%"

    def set_piece_style(self, style: str):
        """Set piece style"""
        self.settings.piece_style = style
        self.disc_cache.clear()  # Clear cache to force redraw
        self.settings.save()
        self.menu_system.setup_menus()
        self.ui.status = f"Piece style: {style.title()}"

    def on_toggle_grid(self):
        """Toggle grid display"""
        self.settings.show_grid = not self.settings.show_grid
        self.settings.save()
        self.menu_system.setup_menus()
        self.ui.status = f"Grid {'enabled' if self.settings.show_grid else 'disabled'}"

    def on_toggle_move_preview(self):
        """Toggle move preview"""
        self.settings.show_move_preview = not self.settings.show_move_preview
        self.settings.save()
        self.menu_system.setup_menus()
        preview_status = "enabled" if self.settings.show_move_preview else "disabled"
        self.ui.status = f"Move preview {preview_status}"

    def on_make_desktop(self):
        try:
            path = os.path.expanduser(
                "~/.local/share/applications/reversi-deluxe.desktop"
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            exec_path = os.path.abspath(sys.argv[0])
            icon_path = os.path.abspath(ICON_PNG)

            # Ensure the icon exists before creating the desktop entry
            if not os.path.exists(icon_path):
                self.ensure_icon()

            desktop = f"""[Desktop Entry]
Type=Application
Name=Reversi Deluxe
Exec=python3 {exec_path}
Icon={icon_path}
Terminal=false
Categories=Game;BoardGame;
Comment=Classic Reversi/Othello board game with AI
"""
            with open(path, "w", encoding="utf-8") as f:
                f.write(desktop)
            # Make the desktop file executable
            os.chmod(path, 0o755)
            self.ui.status = (
                f"Created launcher at {path} (may need to log out/in to appear in menu)"
            )
        except PermissionError:
            self.ui.status = "Failed to create desktop launcher: Permission denied"
        except OSError as e:
            self.ui.status = f"Failed to create desktop launcher: {e}"

    # ---------------------- Main loop ------------------------------ #
    def run(self):
        ai_timer = 0
        ai_delay = 1000  # 1 second delay between AI moves

        while True:
            dt = self.clock.tick(60)

            # Update replay mode if active
            if self.ui.replay_mode:
                self.replay_mode.update()

            # Check for game over state change to auto-show analysis
            current_game_over = self.board.game_over()
            if current_game_over and not self.was_game_over:
                # Game just ended - auto-show analysis
                if self.ui.game_start_time:
                    self.ui.game_end_time = time.time()
                self.game_analysis.show_analysis()
                self.ui.status = "Game over! Analysis shown - press G or ESC to close"
            self.was_game_over = current_game_over

            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    return
                if ev.type == pg.VIDEORESIZE:
                    self.screen = pg.display.set_mode((ev.w, ev.h), pg.RESIZABLE)
                    self.clear_disc_cache()  # Clear cache when window resizes
                if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                    # Check replay mode timeline first
                    if self.ui.replay_mode:
                        if self.replay_mode.handle_timeline_click(ev.pos):
                            continue

                    # Check selection dialog first (highest priority)
                    if self.selection_dialog.handle_click(ev.pos):
                        continue

                    # Check menu system next (before board clicks)
                    if self.menu_system.handle_click(ev.pos):
                        continue

                    # Check move analysis window
                    if self.move_analysis.handle_click(ev.pos):
                        continue

                    # Finally check board clicks (not in replay mode)
                    if not self.ui.replay_mode:
                        board_rect, _, cell = self.layout()
                        rc = self.xy_to_rc(ev.pos, board_rect, cell)
                        if rc and not self.board.game_over():
                            # Only allow human moves if current player is human
                            current_is_ai = (
                                self.board.to_move == BLACK and self.settings.ai_black
                            ) or (
                                self.board.to_move == WHITE and self.settings.ai_white
                            )
                            if not current_is_ai:
                                if self.play(*rc):
                                    self.maybe_pass()
                                    ai_timer = 0  # Reset AI timer after human move

                # Handle mouse wheel for scrolling in analysis
                if ev.type == pg.MOUSEWHEEL:
                    if self.move_analysis.active:
                        self.move_analysis.handle_scroll(
                            -ev.y
                        )  # Negative for natural scrolling
                    elif self.game_analysis.active:
                        self.game_analysis.handle_scroll(
                            -ev.y
                        )  # Negative for natural scrolling
                if ev.type == pg.KEYDOWN:
                    # Handle replay mode keys
                    if self.ui.replay_mode:
                        if ev.key == pg.K_LEFT:
                            self.replay_mode.step_backward()
                            continue
                        elif ev.key == pg.K_RIGHT:
                            self.replay_mode.step_forward()
                            continue
                        elif ev.key == pg.K_SPACE:
                            self.replay_mode.toggle_play()
                            continue
                        elif ev.key == pg.K_HOME:
                            self.replay_mode.go_to_start()
                            continue
                        elif ev.key == pg.K_END:
                            self.replay_mode.go_to_end()
                            continue
                        elif ev.key == pg.K_ESCAPE:
                            self.replay_mode.exit_replay_mode()
                            continue

                    # Give selection dialog first priority
                    if self.selection_dialog.handle_keyboard(ev.key):
                        continue

                    # Give menu system second priority for keyboard handling
                    if self.menu_system.handle_keyboard(ev.key):
                        continue  # Menu handled it, skip other key handling

                    if ev.key == pg.K_q:
                        return
                    elif ev.key == pg.K_u:
                        self.on_undo()
                    elif ev.key == pg.K_r:
                        self.on_redo()
                    elif ev.key == pg.K_h:
                        self.on_toggle_hints()
                    elif ev.key == pg.K_a:
                        if self.board.to_move == BLACK:
                            self.on_toggle_ai_black()
                        else:
                            self.on_toggle_ai_white()
                    elif ev.key == pg.K_d:
                        self.on_cycle_depth()
                    elif ev.key == pg.K_n:
                        self.on_new()
                    elif ev.key == pg.K_s:
                        self.on_save()
                    elif ev.key == pg.K_l:
                        self.on_load()
                    elif ev.key == pg.K_m:
                        self.on_toggle_sound()
                    elif ev.key == pg.K_p:
                        # Toggle replay mode
                        self.on_toggle_replay()
                    elif ev.key == pg.K_i:
                        # Toggle hint system
                        self.on_toggle_move_hints()
                    elif ev.key == pg.K_g:
                        if self.board.game_over():
                            if self.game_analysis.active:
                                self.game_analysis.hide_analysis()
                            else:
                                self.game_analysis.show_analysis()
                    elif ev.key == pg.K_v:
                        self.on_toggle_move_analysis()
                    elif ev.key == pg.K_t:
                        if self.ui.tutorial.active:
                            if not self.ui.tutorial.next_step():
                                self.ui.status = "Tutorial completed!"
                        else:
                            self.on_show_tutorial()
                    elif ev.key == pg.K_ESCAPE:
                        if self.move_analysis.active:
                            self.move_analysis.hide_analysis()
                        elif self.game_analysis.active:
                            self.game_analysis.hide_analysis()
                        elif self.ui.tutorial.active:
                            self.ui.tutorial.active = False
                            self.ui.show_tutorial = False
                            self.ui.status = "Tutorial closed"

            # Handle AI automation (not in replay mode)
            if not self.board.game_over() and not self.ui.replay_mode:
                current_is_ai = (
                    self.board.to_move == BLACK and self.settings.ai_black
                ) or (self.board.to_move == WHITE and self.settings.ai_white)
                both_ai = self.settings.ai_black and self.settings.ai_white

                if current_is_ai:
                    ai_timer += dt
                    # Use shorter delay for AI vs AI games
                    delay = 500 if both_ai else ai_delay

                    if ai_timer >= delay:
                        self.ai_turn_if_needed()
                        ai_timer = 0

            self.draw()


# ----------------------------- Entrypoint --------------------------------- #


def parse_arguments():
    """Parse command-line arguments with argparse"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Reversi Deluxe - A feature-rich Reversi/Othello game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Start with default settings
  %(prog)s -s 10                # Play on 10x10 board
  %(prog)s -d 5 -t midnight     # Hard AI with dark theme
  %(prog)s --load game.rsv      # Load saved game
  %(prog)s --no-sound --debug   # Silent mode with debug logging
        """,
    )

    parser.add_argument(
        "-s",
        "--size",
        type=int,
        metavar="N",
        help="Board size (4-16, even numbers). Default: 8",
    )

    parser.add_argument(
        "-d",
        "--difficulty",
        type=int,
        choices=range(1, 7),
        metavar="LEVEL",
        help="AI difficulty level (1-6). 1=Beginner, 6=Master. Default: 4",
    )

    parser.add_argument(
        "-t",
        "--theme",
        choices=["classic", "ocean", "sunset", "midnight", "forest"],
        help="Color theme. Default: classic",
    )

    parser.add_argument("--no-sound", action="store_true", help="Disable sound effects")

    parser.add_argument(
        "--load", type=str, metavar="FILE", help="Load saved game from file"
    )

    parser.add_argument(
        "--ai-black", action="store_true", help="Enable AI for black player"
    )

    parser.add_argument(
        "--ai-white", action="store_true", help="Enable AI for white player"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument("--version", action="version", version="Reversi Deluxe v2.0")

    return parser.parse_args()


def main(argv: List[str] = None):
    """Main entry point with enhanced argument parsing and error handling"""
    # Parse arguments
    args = parse_arguments()

    # Setup logging if available
    try:
        from src.logger import GameLogger

        GameLogger.setup_logging(debug=args.debug)
        logger = GameLogger.get_logger(__name__)
        logger.info("Starting Reversi Deluxe v2.0")
    except ImportError:
        logger = None
        if args.debug:
            print("Logging module not available")

    try:
        # Load settings
        settings = Settings.load()

        # Override settings with command-line arguments
        if args.size is not None:
            if args.size < 4 or args.size > 16 or args.size % 2 != 0:
                print(
                    "Error: Board size must be even number between 4 and 16",
                    file=sys.stderr,
                )
                return 2
            settings.board_size = args.size
            if logger:
                logger.info(f"Board size set to {args.size}")

        if args.difficulty is not None:
            settings.ai_depth = args.difficulty
            if logger:
                logger.info(f"AI difficulty set to {args.difficulty}")

        if args.theme is not None:
            settings.theme = args.theme
            if logger:
                logger.info(f"Theme set to {args.theme}")

        if args.no_sound:
            settings.sound = False
            if logger:
                logger.info("Sound disabled")

        if args.ai_black:
            settings.ai_black = True
            if logger:
                logger.info("AI enabled for black")

        if args.ai_white:
            settings.ai_white = True
            if logger:
                logger.info("AI enabled for white")

        # Create board
        size = settings.board_size
        board = Board(size=size)

        # Load saved game if specified
        if args.load:
            try:
                import json

                with open(args.load, "r") as f:
                    data = json.load(f)
                board = Board.deserialize(data)
                if logger:
                    logger.info(f"Loaded game from {args.load}")
                print(f"Loaded game from {args.load}")
            except FileNotFoundError:
                print(f"Error: Save file not found: {args.load}", file=sys.stderr)
                if logger:
                    logger.error(f"Save file not found: {args.load}")
                return 1
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error: Invalid save file: {e}", file=sys.stderr)
                if logger:
                    logger.error(f"Invalid save file: {e}")
                return 1

        # Run game
        if logger:
            logger.info("Starting game")

        game = Game(board, settings)
        game.run()

        # Save settings
        settings.save()

        if logger:
            logger.info("Game ended normally")

        return 0

    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        if logger:
            logger.info("Game interrupted by user")
        return 130

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        if logger:
            logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
