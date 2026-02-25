"""
game.py – Main game class for Iago Deluxe.

Responsibilities:
  * Pygame window setup, main loop (run / handle_events / update / draw)
  * Input routing: mouse clicks on the board, menu bar, options overlay;
    keyboard shortcuts
  * Rendering: board, pieces (3D shaded), valid-move hints, win-probability bar,
    move-history sidebar, top menu bar, options overlay
  * Game logic coordination: delegating board moves to Board, AI turns to AI
  * State management: undo/redo stack, save/load (JSON), replay, statistics
  * Programmatic sound generation (no external audio files required)
"""

import pygame as pg
import pygame.gfxdraw
import sys
import math
import json
import time
from dataclasses import asdict
from typing import Tuple, Optional, List
from board import Board
from ai import AI, MAX_DIFFICULTY, DIFFICULTY_LEVELS
from config import (
    EMPTY, PLAYER_BLACK, PLAYER_WHITE,
    DEFAULT_BOARD_SIZE, CELL_SIZE, MARGIN, MENUBAR_HEIGHT,
    UI_HEIGHT, HISTORY_WIDTH, ANIMATION_SPEED,
    BLACK, GREEN, DARK_GREEN,
    BG_DARK, TEXT_PRIMARY, TEXT_DIM, TEXT_ACCENT, HINT_DOT,
    HISTORY_BG, WIN_BAR_BLACK, WIN_BAR_WHITE, WIN_BAR_BG,
    HOVER_FLIP, LAST_MOVE_RING,
    MODE_HvAI, MODE_HvH, MODE_AvA, MODES, MODE_LABELS,
    _COL_LETTERS,
    GameStats, GameState, Animation,
)
from render import RenderMixin


class Game(RenderMixin):
    """Top-level game object.  Owns the pygame window, all game state, and the
    render/update pipeline.  One instance is created in main.py and its ``run()``
    method starts the 60 Hz event loop.
    """

    def __init__(self):
        """Initialise pygame, create the window, load sounds, and set up the
        initial game state ready for the first move.
        """
        pg.init()
        self.board_size = DEFAULT_BOARD_SIZE
        self.cell_size = CELL_SIZE
        self.margin = MARGIN
        self.ui_height = UI_HEIGHT
        self.board_px = self.board_size * self.cell_size

        self.screen_width = self.board_px + 2 * self.margin + HISTORY_WIDTH
        # pixel Y where board row-0 starts
        self.board_top = MENUBAR_HEIGHT + self.margin
        self.screen_height = (
            MENUBAR_HEIGHT + self.board_px + 2 * self.margin + self.ui_height
        )

        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
        pg.display.set_caption("Iago Deluxe")
        self.clock = pg.time.Clock()
        self.font = pg.font.Font(None, 36)
        self.small_font = pg.font.Font(None, 24)
        self.tiny_font = pg.font.Font(None, 18)

        # Initialize sound system
        pg.mixer.init()
        self.sounds = {}
        self._load_sounds()

        self.board = Board(self.board_size)
        self.ai = AI(difficulty=2)   # AI used for White in HvAI, and Black in AvA
        self.ai2 = AI(difficulty=2)  # second AI used for White in AvA mode
        self.player_color = PLAYER_BLACK
        self.ai_color = PLAYER_WHITE
        self.game_mode = MODE_HvAI
        self.show_valid_moves = True
        self.ai_thinking = False

        # Hover preview cell
        self.hover_cell: Optional[Tuple[int, int]] = None

        # Last move played (for highlight ring)
        self.last_move: Optional[Tuple[int, int]] = None

        # Move notation log: list of (player, row, col) for replay + display
        self.notation_log: List[Tuple[int, int, int]] = []

        # Replay state
        self.replay_mode = False
        self.replay_moves: List[Tuple[int, int, int]] = []  # (player, row, col)
        self.replay_step = 0

        # Game state
        self.game_started = False
        self.selected_square = None

        # Animation state
        self.animations = []
        self.animation_speed = ANIMATION_SPEED

        # Move history for undo/redo
        self.move_history = []
        self.redo_stack = []

        # Statistics tracking
        self.stats = self._load_stats()
        self.current_game_moves = 0

        # Options menu
        self.menu_open = False
        # {key: [(Rect, index), ...]} – rebuilt each frame
        self._menu_rects: dict = {}
        # {key: Rect} – rebuilt each frame
        self._menubar_rects: dict = {}

        # Hint: best-move recommendation (recomputed after each move)
        self.hint_move: Optional[Tuple[int, int]] = None
        self._refresh_hint()

    def _load_sounds(self):
        """Build the sounds dict by generating each effect programmatically.
        No external audio files are required.
        """
        # Create simple sound effects programmatically since we don't have audio files
        self.sounds = {
            "move": self._create_move_sound(),
            "win": self._create_win_sound(),
            "lose": self._create_lose_sound(),
            "draw": self._create_draw_sound(),
        }

    def _create_move_sound(self) -> pg.mixer.Sound:
        """Short 800 Hz beep (100 ms) played when any piece is placed."""
        # Create a short beep sound
        sample_rate = 44100
        duration = 0.1  # 100ms
        frequency = 800  # Hz

        samples = int(sample_rate * duration)
        buffer = bytearray()

        for i in range(samples):
            # Generate sine wave
            sample = int(127 + 50 * math.sin(2 * math.pi * frequency * i / sample_rate))
            buffer.append(sample)

        sound = pg.mixer.Sound(buffer=bytes(buffer))
        sound.set_volume(0.3)
        return sound

    def _create_win_sound(self) -> pg.mixer.Sound:
        """Rising tone (400 → 800 Hz, 500 ms) played on a human victory."""
        sample_rate = 44100
        duration = 0.5
        buffer = bytearray()

        samples = int(sample_rate * duration)
        for i in range(samples):
            # Ascending tone
            freq = 400 + (i / samples) * 400
            sample = int(127 + 60 * math.sin(2 * math.pi * freq * i / sample_rate))
            buffer.append(sample)

        sound = pg.mixer.Sound(buffer=bytes(buffer))
        sound.set_volume(0.4)
        return sound

    def _create_lose_sound(self) -> pg.mixer.Sound:
        """Falling tone (600 → 300 Hz, 500 ms) played on a human defeat."""
        sample_rate = 44100
        duration = 0.5
        buffer = bytearray()

        samples = int(sample_rate * duration)
        for i in range(samples):
            # Descending tone
            freq = 600 - (i / samples) * 300
            sample = int(127 + 40 * math.sin(2 * math.pi * freq * i / sample_rate))
            buffer.append(sample)

        sound = pg.mixer.Sound(buffer=bytes(buffer))
        sound.set_volume(0.3)
        return sound

    def _create_draw_sound(self) -> pg.mixer.Sound:
        """Neutral 500 Hz tone (300 ms) played on a draw."""
        sample_rate = 44100
        duration = 0.3
        buffer = bytearray()

        samples = int(sample_rate * duration)
        for i in range(samples):
            # Neutral tone
            sample = int(127 + 30 * math.sin(2 * math.pi * 500 * i / sample_rate))
            buffer.append(sample)

        sound = pg.mixer.Sound(buffer=bytes(buffer))
        sound.set_volume(0.2)
        return sound

    def play_sound(self, sound_name: str):
        """Play a named sound effect, silently ignoring any pygame audio errors."""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except (pg.error, ValueError, TypeError):
                pass  # Silently fail if sound can't be played

    def _load_stats(self) -> GameStats:
        """Load persisted statistics from stats.json; return defaults on failure."""
        try:
            with open("stats.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return GameStats(**data)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return GameStats()

    def _save_stats(self):
        """Serialise the current GameStats to stats.json, silently on failure."""
        try:
            with open("stats.json", "w", encoding="utf-8") as f:
                json.dump(asdict(self.stats), f, indent=2)
        except (OSError, TypeError):
            pass  # Silently fail

    def update_stats(self):
        """Update statistics based on game result."""
        # Only count stats in human-vs-ai mode
        if self.game_mode != MODE_HvAI:
            return
        self.stats.games_played += 1
        self.stats.total_moves += self.current_game_moves

        if self.board.winner == self.player_color:
            self.stats.games_won += 1
            self.stats.current_streak = max(0, self.stats.current_streak) + 1
            self.stats.win_streak = max(
                self.stats.win_streak, self.stats.current_streak
            )
        elif self.board.winner == self.ai_color:
            self.stats.games_lost += 1
            self.stats.current_streak = min(0, self.stats.current_streak) - 1
            self.stats.loss_streak = max(
                self.stats.loss_streak, -self.stats.current_streak
            )
        else:
            self.stats.games_drawn += 1
            self.stats.current_streak = 0

        black_score, white_score = self.board.get_score()
        if self.player_color == PLAYER_BLACK:
            self.stats.best_score = max(self.stats.best_score, black_score)
        else:
            self.stats.best_score = max(self.stats.best_score, white_score)

        self._save_stats()

    def start_animation(
        self, row: int, col: int, player: int, anim_type: str = "place"
    ):
        """Enqueue an Animation for the piece at (*row*, *col*).
        ``anim_type`` is ``'place'`` (scale-in from 0→1) or ``'flip'`` (pulse).
        """
        animation = Animation(
            row=row,
            col=col,
            player=player,
            start_time=pg.time.get_ticks() / 1000.0,
            duration=self.animation_speed,
            anim_type=anim_type,
        )
        self.animations.append(animation)

    def update_animations(self):
        """Expire animations whose duration has elapsed."""
        current_time = pg.time.get_ticks() / 1000.0
        # Remove completed animations
        self.animations = [
            anim
            for anim in self.animations
            if current_time - anim.start_time < anim.duration
        ]

    def save_game_state(self):
        """Push the current board position onto the undo stack and clear redo.
        Called before every human move so the position can be restored later.
        """
        state = GameState(
            board_grid=[row[:] for row in self.board.grid],
            current_player=self.board.current_player,
            move_history=[],  # handled separately via notation_log
            black_score=self.board.get_score()[0],
            white_score=self.board.get_score()[1],
            game_over=self.board.game_over,
            winner=self.board.winner,
            settings={},
        )
        self.move_history.append(state)
        # Clear redo stack when new move is made
        self.redo_stack.clear()

    def undo_move(self):
        """Restore the board to the state before the last move, pushing the
        current state onto the redo stack.
        """
        if self.move_history:
            # Save current state to redo stack
            current_state = GameState(
                board_grid=[row[:] for row in self.board.grid],
                current_player=self.board.current_player,
                move_history=[],
                black_score=self.board.get_score()[0],
                white_score=self.board.get_score()[1],
                game_over=self.board.game_over,
                winner=self.board.winner,
                settings={},
            )
            self.redo_stack.append(current_state)

            # Restore previous state
            prev_state = self.move_history.pop()
            self.board.grid = [row[:] for row in prev_state.board_grid]
            self.board.current_player = prev_state.current_player
            self.board.game_over = prev_state.game_over
            self.board.winner = prev_state.winner
            self._refresh_hint()

            # Clear animations
            self.animations.clear()

    def redo_move(self):
        """Reapply the last undone move, pushing the current state back onto
        the undo stack.
        """
        if self.redo_stack:
            # Save current state to history
            current_state = GameState(
                board_grid=[row[:] for row in self.board.grid],
                current_player=self.board.current_player,
                move_history=[],
                black_score=self.board.get_score()[0],
                white_score=self.board.get_score()[1],
                game_over=self.board.game_over,
                winner=self.board.winner,
                settings={},
            )
            self.move_history.append(current_state)

            # Restore redo state
            redo_state = self.redo_stack.pop()
            self.board.grid = [row[:] for row in redo_state.board_grid]
            self.board.current_player = redo_state.current_player
            self.board.game_over = redo_state.game_over
            self.board.winner = redo_state.winner
            self._refresh_hint()

            # Clear animations
            self.animations.clear()

    def save_game(self, filename: str = "saved_game.json"):
        """Save current game state to file."""
        try:
            state_dict = {
                "board_grid": [row[:] for row in self.board.grid],
                "current_player": self.board.current_player,
                "black_score": self.board.get_score()[0],
                "white_score": self.board.get_score()[1],
                "game_over": self.board.game_over,
                "winner": self.board.winner,
                "move_log": self.notation_log,
                "settings": {
                    "show_hints": self.show_valid_moves,
                    "ai_difficulty": self.ai.difficulty,
                    "board_size": self.board_size,
                    "player_color": self.player_color,
                    "game_mode": self.game_mode,
                },
                "timestamp": time.time(),
            }
            with open(filename, "w") as f:
                json.dump(state_dict, f, indent=2)
            return True
        except Exception:
            return False

    def load_game(self, filename: str = "saved_game.json"):
        """Load game state from file."""
        try:
            with open(filename, "r") as f:
                state_dict = json.load(f)

            self.board.grid = state_dict["board_grid"]
            self.board.current_player = state_dict["current_player"]
            self.board.game_over = state_dict["game_over"]
            self.board.winner = state_dict["winner"]

            settings = state_dict.get("settings", {})
            self.show_valid_moves = settings.get("show_hints", True)
            self.ai.difficulty = settings.get("ai_difficulty", 2)
            self.ai2.difficulty = self.ai.difficulty
            self.player_color = settings.get("player_color", PLAYER_BLACK)
            self.ai_color = 3 - self.player_color
            self.game_mode = settings.get("game_mode", MODE_HvAI)

            raw_log = state_dict.get("move_log", [])
            self.notation_log = [tuple(m) for m in raw_log]

            self.move_history.clear()
            self.redo_stack.clear()
            self.animations.clear()
            self.last_move = None
            self.ai.reset_log()
            for entry in self.notation_log:
                self.ai.record_move(*entry)
            return True
        except Exception:
            return False

    def get_animation_scale(self, row: int, col: int) -> float:
        """Return the current render scale [0.0, 1.0] for the piece at (*row*, *col*).
        Returns 1.0 when no animation is active for that cell.
        """
        for anim in self.animations:
            if anim.row == row and anim.col == col:
                current_time = pg.time.get_ticks() / 1000.0
                progress = (current_time - anim.start_time) / anim.duration
                progress = min(max(progress, 0.0), 1.0)  # Clamp to [0, 1]

                if anim.anim_type == "place":
                    # Smooth scale in
                    scale_diff = anim.end_scale - anim.start_scale
                    return anim.start_scale + scale_diff * progress
                elif anim.anim_type == "flip":
                    # Pulse effect for flipping
                    if progress < 0.5:
                        return 1.0 - progress * 0.3
                    else:
                        return 0.85 + (progress - 0.5) * 0.3
        return 1.0  # No animation

    def run(self):
        """Start the 60 Hz game loop.  Blocks until the window is closed."""
        running = True
        while running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pg.quit()
        sys.exit()

    def handle_events(self):
        """Pump the pygame event queue, routing each event to the appropriate handler.
        Auto-saves to autosave.json on window close.
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.save_game("autosave.json")   # auto-save on close
                pg.quit()
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_click(event.pos)
            elif event.type == pg.MOUSEMOTION:
                if not self.menu_open:
                    self._update_hover(event.pos)
            elif event.type == pg.KEYDOWN:
                self.handle_key(event.key)

    def handle_click(self, pos: Tuple[int, int]):
        """Route a left-click: options overlay → menu-bar buttons → board cells.
        In replay mode any click on the board area advances one step.
        """
        if self.menu_open:
            self._handle_menu_click(pos)
            return

        # Persistent menu bar buttons
        for key, rect in self._menubar_rects.items():
            if rect.collidepoint(pos):
                if key == "new_game":
                    self._new_game()
                elif key == "undo":
                    self.undo_move()
                elif key == "redo":
                    self.redo_move()
                elif key == "options":
                    self.menu_open = not self.menu_open
                return

        x, y = pos

        # Replay: click anywhere on board advances a step
        if self.replay_mode:
            self.replay_next()
            return

        board_x = x - MARGIN
        board_y = y - self.board_top

        if (
            0 <= board_x < self.board_px
            and 0 <= board_y < self.board_px
        ):
            col = board_x // CELL_SIZE
            row = board_y // CELL_SIZE

            # In HvH mode both colours are human
            if self.game_mode == MODE_HvH:
                current = self.board.current_player
                if self.board.is_valid_move(row, col, current):
                    self.make_player_move(row, col)
            elif self.game_mode == MODE_HvAI:
                if self.board.current_player == self.player_color:
                    if self.board.is_valid_move(row, col, self.player_color):
                        self.make_player_move(row, col)

    def handle_key(self, key):
        """Handle keyboard shortcuts.

        O / Tab   – toggle Options overlay
        ESC       – close overlay, or quit (saves autosave.json)
        R         – new game
        H         – toggle move hints
        D         – cycle AI difficulty
        M         – cycle game mode
        U         – undo
        Y         – redo
        S         – save game
        L         – load game
        Space / P – start or advance replay
        """
        if key == pg.K_o or key == pg.K_TAB:  # Options menu
            self.menu_open = not self.menu_open
            return
        if key == pg.K_ESCAPE:
            if self.menu_open:
                self.menu_open = False
                return
            self.save_game("autosave.json")
            pg.quit()
            sys.exit()
        if key == pg.K_r:  # Reset game
            self._new_game()
        elif key == pg.K_h:  # Toggle hints
            self.show_valid_moves = not self.show_valid_moves
        elif key == pg.K_d:  # Cycle AI difficulty
            self.ai.difficulty = (self.ai.difficulty % MAX_DIFFICULTY) + 1
            self.ai2.difficulty = self.ai.difficulty
            self.ai.reset_log()
        elif key == pg.K_m:  # Cycle game mode
            idx = (MODES.index(self.game_mode) + 1) % len(MODES)
            self.game_mode = MODES[idx]
            self._new_game()
        elif key == pg.K_u:  # Undo move
            self.undo_move()
        elif key == pg.K_y:  # Redo move
            self.redo_move()
        elif key == pg.K_s:  # Save game
            self.save_game()
        elif key == pg.K_l:  # Load game
            self.load_game()
        elif key in (pg.K_SPACE, pg.K_p):  # Replay next step
            if self.replay_mode:
                self.replay_next()
            else:
                self.start_replay()

    def make_player_move(self, row: int, col: int):
        """Execute a human move at (*row*, *col*).

        Saves undo state, places the piece, triggers wave-flip animations, plays the
        move sound, records the move in the notation log and AI history, checks for
        game-over, and sets ``ai_thinking`` flag for the AI's response in HvAI mode.
        """
        self.save_game_state()

        current = self.board.current_player
        flipped = self.board.make_move(row, col, current)
        self.start_animation(row, col, current, "place")
        self._start_wave_flip_animations(row, col, flipped, current)

        self.play_sound("move")
        self.current_game_moves += 1
        self.last_move = (row, col)
        self.notation_log.append((current, row, col))
        if self.game_mode == MODE_HvAI:
            self.ai.record_move(current, row, col)
        self.board.check_game_over()
        self._refresh_hint()

        if self.board.game_over:
            self.update_stats()
            winner = self.board.winner
            if winner == self.player_color:
                self.play_sound("win")
            elif winner == self.ai_color:
                self.play_sound("lose")
            else:
                self.play_sound("draw")

        # Trigger AI turn in HvAI mode
        if self.game_mode == MODE_HvAI and not self.board.game_over \
                and self.board.current_player == self.ai_color:
            self.ai_thinking = True

    def update(self):
        """Per-frame state update: expire animations, then drive AI moves."""
        self.update_animations()

        if self.replay_mode:
            return   # Replay is driven by key/click events

        if self.game_mode == MODE_HvAI:
            self._update_hvai()
        elif self.game_mode == MODE_AvA:
            self._update_ava()
        # HvH needs no automatic AI moves

    def _update_hvai(self):
        """Execute the AI's move when it's the AI's turn in Human-vs-AI mode.
        Sets ``ai_thinking = True`` again if the AI must play consecutive turns
        (e.g. the human has no moves).
        """
        if not (self.ai_thinking and self.board.current_player == self.ai_color):
            return

        move = self.ai.get_move(self.board)
        if move:
            flipped = self.board.make_move(move[0], move[1], self.ai_color)
            self.start_animation(move[0], move[1], self.ai_color, "place")
            self._start_wave_flip_animations(move[0], move[1], flipped, self.ai_color)
            self.play_sound("move")
            self.current_game_moves += 1
            self.last_move = move
            self.notation_log.append((self.ai_color, move[0], move[1]))
            self.ai.record_move(self.ai_color, move[0], move[1])

        self.board.check_game_over()

        if self.board.game_over:
            self.update_stats()
            winner = self.board.winner
            if winner == self.player_color:
                self.play_sound("win")
            elif winner == self.ai_color:
                self.play_sound("lose")
            else:
                self.play_sound("draw")

        self._refresh_hint()
        self.ai_thinking = False
        if not self.board.game_over and self.board.current_player == self.ai_color:
            self.ai_thinking = True

    def _update_ava(self):
        """Advance the AI-vs-AI demo by one move per frame, with a 300 ms delay
        so moves are visible.  ``self.ai`` plays Black; ``self.ai2`` plays White.
        """
        if self.board.game_over:
            return
        if not self.ai_thinking:
            self.ai_thinking = True
            return

        current = self.board.current_player
        ai_agent = self.ai if current == PLAYER_BLACK else self.ai2
        move = ai_agent.get_move(self.board)
        if move:
            flipped = self.board.make_move(move[0], move[1], current)
            self.start_animation(move[0], move[1], current, "place")
            self._start_wave_flip_animations(move[0], move[1], flipped, current)
            self.play_sound("move")
            self.current_game_moves += 1
            self.last_move = move
            self.notation_log.append((current, move[0], move[1]))

        self.board.check_game_over()
        if self.board.game_over:
            self.play_sound("draw" if self.board.winner == 0 else "win")

        # Brief pause so each move is visible before the next one
        pg.time.delay(300)

    def _new_game(self):
        """Reset all game state for a fresh game, then trigger the AI immediately
        if it has the first move (AvA mode, or HvAI when the human plays White).
        """
        self.board.reset()
        self.move_history.clear()
        self.redo_stack.clear()
        self.animations.clear()
        self.notation_log.clear()
        self.last_move = None
        self.game_started = False
        self.current_game_moves = 0
        self.replay_mode = False
        self.hint_move = None
        self.ai.reset_log()
        self.ai2.reset_log()
        self._refresh_hint()
        # Trigger AI immediately if it moves first
        if self.game_mode == MODE_AvA:
            self.ai_thinking = True
        elif (self.game_mode == MODE_HvAI
              and self.board.current_player == self.ai_color):
            self.ai_thinking = True
        else:
            self.ai_thinking = False

    def _refresh_hint(self):
        """Recompute and cache ``self.hint_move`` using the instant heuristic.
        Clears the hint when hints are disabled or the game is over.
        """
        if self.board.game_over or not self.show_valid_moves:
            self.hint_move = None
        else:
            self.hint_move = self.ai.get_hint(self.board)

    def _update_hover(self, pos: Tuple[int, int]):
        """Update ``self.hover_cell`` from mouse-motion coordinates.
        Sets to None when the cursor is outside the board area.
        """
        x, y = pos
        bx = x - MARGIN
        by = y - self.board_top
        if 0 <= bx < self.board_px and 0 <= by < self.board_px:
            col = bx // CELL_SIZE
            row = by // CELL_SIZE
            self.hover_cell = (row, col)
        else:
            self.hover_cell = None

    def _start_wave_flip_animations(
        self, placed_row: int, placed_col: int,
        flipped: List[Tuple[int, int]], player: int
    ):
        """Queue flip animations for *flipped* cells with a staggered delay
        proportional to their Manhattan distance from (*placed_row*, *placed_col*)
        (50 ms per unit), creating a ripple/wave effect.
        """
        now = pg.time.get_ticks() / 1000.0
        for fr, fc in flipped:
            dist = abs(fr - placed_row) + abs(fc - placed_col)
            delay = dist * 0.05   # 50 ms per unit of Manhattan distance
            anim = Animation(
                row=fr, col=fc, player=player,
                start_time=now + delay,
                duration=self.animation_speed,
                anim_type="flip",
            )
            self.animations.append(anim)

    def start_replay(self, filename: str = "saved_game.json") -> bool:
        """Load a saved game and enter step-by-step replay mode.

        Reads the move log from *filename*, resets the board, and sets
        ``replay_mode = True``.  Returns False if the file is missing or has
        no move log.  Advances are driven by Space/P key or board clicks.
        """
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            raw = data.get("move_log", [])
            if not raw:
                return False
            self.replay_moves = [tuple(m) for m in raw]
            self.board.reset()
            self.notation_log.clear()
            self.last_move = None
            self.animations.clear()
            self.replay_step = 0
            self.replay_mode = True
            return True
        except Exception:
            return False

    def replay_next(self):
        """Apply the next move in the replay sequence.  Exits replay mode
        automatically after the last move has been played.
        """
        if self.replay_step >= len(self.replay_moves):
            self.replay_mode = False
            return
        player, row, col = self.replay_moves[self.replay_step]
        flipped = self.board.make_move(row, col, player)
        self.start_animation(row, col, player, "place")
        self._start_wave_flip_animations(row, col, flipped, player)
        self.play_sound("move")
        self.last_move = (row, col)
        self.notation_log.append((player, row, col))
        self.replay_step += 1
        self.board.check_game_over()

    def _handle_menu_click(self, pos: Tuple[int, int]):
        """Dispatch a click inside the Options overlay to the correct action.

        Mode change   – calls ``_new_game()``
        Difficulty    – updates both AIs and clears the opening-book log
        Hints         – toggles ``show_valid_moves``
        Play as       – swaps player/AI colours and calls ``_new_game()``
        New Game btn  – calls ``_new_game()`` and closes the overlay
        Close btn     – closes the overlay
        """
        for key, items in self._menu_rects.items():
            for rect, idx in items:
                if rect.collidepoint(pos):
                    if key == "mode":
                        self.game_mode = MODES[idx]
                        self._new_game()
                    elif key == "difficulty":
                        self.ai.difficulty = idx + 1
                        self.ai2.difficulty = idx + 1
                        self.ai.reset_log()
                    elif key == "hints":
                        self.show_valid_moves = bool(idx)
                    elif key == "color":
                        if self.game_mode == MODE_HvAI:
                            self.player_color = idx + 1
                            self.ai_color = 3 - self.player_color
                            self._new_game()
                    elif key == "new_game":
                        self._new_game()
                        self.menu_open = False
                    elif key == "close":
                        self.menu_open = False
                    return
