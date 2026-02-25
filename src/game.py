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
    HISTORY_BG, WIN_BAR_BLACK, WIN_BAR_WHITE, WIN_BAR_BG, HOVER_FLIP, LAST_MOVE_RING,
    GameStats, GameState, Animation,
)

# ── Game mode constants ───────────────────────────────────────────────────────
MODE_HvAI = "hvai"  # Human vs AI
MODE_HvH = "hvh"   # Human vs Human (local two-player)
MODE_AvA = "ava"   # AI vs AI (demo / spectator)
MODES = [MODE_HvAI, MODE_HvH, MODE_AvA]
MODE_LABELS = {
    MODE_HvAI: "Human vs AI",
    MODE_HvH: "2-Player",
    MODE_AvA: "AI vs AI",
}

# Board coordinate label characters
_COL_LETTERS = "abcdefgh"


class Game:
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

    def draw(self):
        """Compose the full frame: menu bar → board → pieces → hints → sidebar
        → UI panel → optional overlay → flip to display.
        """
        self.screen.fill(BG_DARK)
        self.draw_menu_bar()
        self.draw_board()
        self.draw_pieces()
        if self.show_valid_moves and not self.board.game_over:
            human_turn = (
                self.game_mode == MODE_HvH
                or self.board.current_player == self.player_color
            )
            if human_turn:
                self.draw_valid_moves()
        self.draw_history_sidebar()
        self.draw_ui()
        if self.menu_open:
            self.draw_menu()
        pg.display.flip()

    def draw_board(self):
        """Fill each board cell with the green felt colour, draw grid lines,
        overlay the gold last-move ring, and render the coordinate labels
        (a–h above, 1–8 left).
        """
        for row in range(self.board_size):
            for col in range(self.board_size):
                x = MARGIN + col * CELL_SIZE
                y = self.board_top + row * CELL_SIZE
                pg.draw.rect(self.screen, GREEN, (x, y, CELL_SIZE, CELL_SIZE))
                pg.draw.rect(self.screen, DARK_GREEN, (x, y, CELL_SIZE, CELL_SIZE), 1)

        # Last-move highlight ring
        if self.last_move:
            lr, lc = self.last_move
            cx = MARGIN + lc * CELL_SIZE + CELL_SIZE // 2
            cy = self.board_top + lr * CELL_SIZE + CELL_SIZE // 2
            pg.draw.circle(self.screen, LAST_MOVE_RING, (cx, cy),
                           CELL_SIZE // 2 - 2, 3)

        # Column letters (a-h) above the board
        for col in range(self.board_size):
            lbl = self.tiny_font.render(_COL_LETTERS[col], True, TEXT_DIM)
            lx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2 - lbl.get_width() // 2
            self.screen.blit(lbl, (lx, MENUBAR_HEIGHT + 4))

        # Row numbers (1-8) to the left of the board
        for row in range(self.board_size):
            lbl = self.tiny_font.render(str(row + 1), True, TEXT_DIM)
            ly = (self.board_top + row * CELL_SIZE
                  + CELL_SIZE // 2 - lbl.get_height() // 2)
            self.screen.blit(lbl, (4, ly))

    def draw_pieces(self):
        """Iterate the grid and call ``_draw_piece_3d`` for every occupied cell,
        scaling the radius by the active animation progress.
        """
        for row in range(self.board_size):
            for col in range(self.board_size):
                piece = self.board.grid[row][col]
                if piece != EMPTY:
                    cx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
                    cy = self.board_top + row * CELL_SIZE + CELL_SIZE // 2
                    scale = self.get_animation_scale(row, col)
                    radius = int((CELL_SIZE // 2 - 5) * scale)
                    if radius > 0:
                        self._draw_piece_3d(cx, cy, radius, piece)

    def _draw_piece_3d(self, cx: int, cy: int, radius: int, player: int):
        """Render a single disc with layered circles to simulate a 3D appearance:
        drop shadow → base disc → body disc (offset) → soft highlight → specular
        pinpoint → anti-aliased rim outline.
        """
        surf = self.screen

        # Colour palette per player
        if player == PLAYER_BLACK:
            base = (32, 32, 36)
            body = (52, 52, 58)
            rim = (18, 18, 20)
            shine1 = (105, 105, 118)
            shine2 = (175, 175, 188)
        else:
            base = (225, 225, 220)
            body = (248, 248, 244)
            rim = (170, 170, 165)
            shine1 = (255, 255, 255)
            shine2 = (255, 255, 255)

        # 1 – drop shadow (offset down-right, no alpha needed)
        shadow_off = max(2, radius // 5)
        shadow_r = radius - 1
        pg.draw.circle(surf, (12, 12, 12), (cx + shadow_off, cy + shadow_off), shadow_r)

        # 2 – base disc
        pg.draw.circle(surf, base, (cx, cy), radius)

        # 3 – slightly lighter body disc offset a touch downward
        body_r = max(1, int(radius * 0.78))
        body_dy = max(1, radius // 7)
        pg.draw.circle(surf, body, (cx, cy + body_dy), body_r)

        # 4 – soft highlight blob (upper-left)
        if radius > 6:
            hl_r = max(2, int(radius * 0.42))
            hl_x = cx - int(radius * 0.26)
            hl_y = cy - int(radius * 0.26)
            pg.draw.circle(surf, shine1, (hl_x, hl_y), hl_r)

        # 5 – sharp specular pinpoint
        if radius > 10:
            dot_r = max(1, int(radius * 0.14))
            dot_x = cx - int(radius * 0.38)
            dot_y = cy - int(radius * 0.38)
            pg.draw.circle(surf, shine2, (dot_x, dot_y), dot_r)

        # 6 – anti-aliased rim outline
        try:
            pg.gfxdraw.aacircle(surf, cx, cy, radius,     rim)
            pg.gfxdraw.aacircle(surf, cx, cy, radius - 1, rim)
        except AttributeError:
            pg.draw.circle(surf, rim, (cx, cy), radius, 1)

    def draw_valid_moves(self):
        """Render move indicators for the current player.

        The best move (from ``self.hint_move``) is highlighted with a gold star
        and three concentric glow rings.  All other legal moves get a smaller
        three-circle green dot.  When hovering over a legal cell the cells that
        would be flipped are tinted with a semi-transparent overlay.
        """
        current = self.board.current_player
        valid_moves = self.board.get_valid_moves(current)

        # Hover preview: highlight cells that would be flipped
        if self.hover_cell and self.hover_cell in valid_moves:
            hover_flips = self.board.get_flips(self.hover_cell[0],
                                               self.hover_cell[1], current)
            for fr, fc in hover_flips:
                hx = MARGIN + fc * CELL_SIZE
                hy = self.board_top + fr * CELL_SIZE
                # Semi-transparent tint surface
                tint = pg.Surface((CELL_SIZE, CELL_SIZE), pg.SRCALPHA)
                tint.fill((*HOVER_FLIP, 90))
                self.screen.blit(tint, (hx, hy))

        for row, col in valid_moves:
            cx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
            cy = self.board_top + row * CELL_SIZE + CELL_SIZE // 2
            is_best = self.hint_move == (row, col)
            if is_best:
                # Gold outer glow ring
                pg.draw.circle(self.screen, (200, 160, 0), (cx, cy), 13)
                pg.draw.circle(self.screen, (255, 215, 0), (cx, cy), 11)
                pg.draw.circle(self.screen, (255, 240, 80), (cx, cy), 8)
                # Star character centred on the cell
                star = self.tiny_font.render("\u2605", True, (80, 50, 0))
                self.screen.blit(star, (
                    cx - star.get_width() // 2,
                    cy - star.get_height() // 2,
                ))
            else:
                # Visible dot for other valid moves
                pg.draw.circle(self.screen, (60, 160, 90), (cx, cy), 9)
                pg.draw.circle(self.screen, (120, 210, 140), (cx, cy), 7)
                pg.draw.circle(self.screen, (180, 240, 190), (cx, cy), 4)

    def draw_ui(self):
        """Render the bottom info panel beneath the board.

        Contains (top to bottom):
          * score and mode/AI-level labels
          * current-turn or game-over banner
          * win-probability bar (B xx% ←→ W xx%)
          * AI-thinking indicator or win/loss streak
          * hotkey reference column (inside sidebar area)
        """
        ui_y = self.board_top + self.board_px + 8

        # Dark panel
        panel_rect = (
            0, self.board_top + self.board_px, self.screen_width, self.ui_height
        )
        pg.draw.rect(self.screen, BG_DARK, panel_rect)

        # Thin separator line
        sep_y = self.board_top + self.board_px
        pg.draw.line(self.screen, (60, 60, 60),
                     (0, sep_y), (self.screen_width, sep_y), 1)

        # ── Row 1: score + mode ──────────────────────────────────────────
        black_score, white_score = self.board.get_score()
        score_text = f"Black: {black_score}   White: {white_score}"
        score_surf = self.font.render(score_text, True, TEXT_PRIMARY)
        self.screen.blit(score_surf, (MARGIN, ui_y))

        mode_lbl = self.tiny_font.render(MODE_LABELS[self.game_mode], True, TEXT_DIM)
        self.screen.blit(mode_lbl, (MARGIN, ui_y + 28))

        ai_lbl = self.tiny_font.render(f"AI: {self.ai.name}", True, TEXT_DIM)
        self.screen.blit(ai_lbl, (MARGIN + 85, ui_y + 28))

        # ── Row 2: player turn / game-over ───────────────────────────────
        if self.replay_mode:
            step_max = len(self.replay_moves)
            player_text = f"Replay {self.replay_step}/{step_max}  ► Space/Click"
        elif self.board.game_over:
            if self.board.winner == PLAYER_BLACK:
                player_text = "Black wins!"
            elif self.board.winner == PLAYER_WHITE:
                player_text = "White wins!"
            else:
                player_text = "It's a draw!"
        else:
            player_text = (
                "Black's turn" if self.board.current_player == PLAYER_BLACK
                else "White's turn"
            )
        is_end = self.board.game_over and not self.replay_mode
        player_surf = self.font.render(player_text, True,
                                       TEXT_ACCENT if is_end else TEXT_PRIMARY)
        self.screen.blit(player_surf, (MARGIN, ui_y + 46))

        # ── Win-probability bar ───────────────────────────────────────────
        bar_x = MARGIN
        bar_y = ui_y + 82
        bar_w = self.board_px
        bar_h = 10
        pg.draw.rect(
            self.screen, WIN_BAR_BG,
            (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        prob = self._get_win_probability()
        black_w = int(bar_w * prob)
        if black_w > 0:
            pg.draw.rect(self.screen, WIN_BAR_BLACK,
                         (bar_x, bar_y, black_w, bar_h), border_radius=4)
        if black_w < bar_w:
            pg.draw.rect(
                self.screen, WIN_BAR_WHITE,
                (bar_x + black_w, bar_y, bar_w - black_w, bar_h),
                border_radius=4)
        # Centre tick
        pg.draw.line(self.screen, BG_DARK,
                     (bar_x + bar_w // 2, bar_y),
                     (bar_x + bar_w // 2, bar_y + bar_h), 2)
        prob_pct = int(prob * 100)
        b_lbl = self.tiny_font.render(f"B {prob_pct}%", True, (160, 170, 200))
        w_lbl = self.tiny_font.render(
            f"W {100 - prob_pct}%", True, (200, 200, 195)
        )
        self.screen.blit(b_lbl, (bar_x, bar_y - 14))
        self.screen.blit(
            w_lbl, (bar_x + bar_w - w_lbl.get_width(), bar_y - 14)
        )

        # ── Row 4: AI thinking / streak ──────────────────────────────────
        if self.ai_thinking:
            thinking_surf = self.small_font.render("AI thinking...", True, TEXT_ACCENT)
            self.screen.blit(thinking_surf, (MARGIN, ui_y + 98))
        elif self.game_mode == MODE_HvAI and self.stats.current_streak != 0:
            s = self.stats.current_streak
            streak_text = (
                f"Win streak: {s}" if s > 0 else f"Loss streak: {-s}"
            )
            streak_color = (100, 220, 100) if s > 0 else (220, 100, 100)
            streak_surf = self.small_font.render(streak_text, True, streak_color)
            self.screen.blit(streak_surf, (MARGIN, ui_y + 98))

        # ── Hotkey reference (two columns) ───────────────────────────────
        col1 = MARGIN + self.board_px + 8    # inside sidebar
        col2 = col1 + 82
        hotkeys = [
            "Click: move",   "R: Reset",
            "H: Hints",      "D: AI level",
            "M: Mode",       "U: Undo",
            "S: Save",       "Y: Redo",
            "L: Load",       "P: Replay",
            "O: Options",    "ESC: Quit",
        ]
        row_h = 18
        hk_y0 = self.board_top + self.board_px + 6
        for i, text in enumerate(hotkeys):
            if not text:
                continue
            x = col1 if i % 2 == 0 else col2
            y = hk_y0 + (i // 2) * row_h
            surf = self.tiny_font.render(text, True, TEXT_DIM)
            self.screen.blit(surf, (x, y))

    # ──────────────────────────────────────────────────────────────────────────
    # Helper methods
    # ──────────────────────────────────────────────────────────────────────────

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

    def _get_win_probability(self) -> float:
        """Return a value in [0.0, 1.0] representing Black's estimated winning
        chance.  1.0 = Black winning, 0.0 = White winning, 0.5 = even.

        When the game is over the result is exact (1.0 / 0.0 / 0.5).
        During play, the raw heuristic score is clamped to ±2000 and rescaled.
        """
        if self.board.game_over:
            b, w = self.board.get_score()
            if b > w:
                return 1.0
            if w > b:
                return 0.0
            return 0.5
        raw = self.ai.evaluate_for_black(self.board)
        raw = max(-2000, min(2000, raw))
        return (raw + 2000) / 4000.0

    @staticmethod
    def _cell_to_notation(row: int, col: int) -> str:
        """Convert (row, col) to algebraic notation, e.g. (1, 4) → 'e2'."""
        return f"{_COL_LETTERS[col]}{row + 1}"

    def draw_history_sidebar(self):
        """Render the move-history panel to the right of the board.

        Moves are displayed in paired rows (Black / White) using algebraic
        notation.  Only the last N rows that fit in the panel are shown;
        the most recent move is highlighted in TEXT_PRIMARY.  During replay
        mode the current step counter is shown at the bottom.
        """
        sx = MARGIN + self.board_px          # sidebar left edge
        sy = self.board_top
        sw = HISTORY_WIDTH
        sh = self.board_px

        pg.draw.rect(self.screen, HISTORY_BG, (sx, sy, sw, sh))
        pg.draw.line(self.screen, (60, 60, 60), (sx, sy), (sx, sy + sh), 1)

        # Header
        header = self.tiny_font.render("MOVES", True, TEXT_ACCENT)
        self.screen.blit(header, (sx + 6, sy + 4))
        pg.draw.line(self.screen, (60, 60, 60),
                     (sx, sy + 20), (sx + sw, sy + 20), 1)

        # Build move pairs:  1. b4  c3
        pairs: List[str] = []
        i = 0
        while i < len(self.notation_log):
            p, r, c = self.notation_log[i]
            bm = self._cell_to_notation(r, c) if p == PLAYER_BLACK else "---"
            wm = "---"
            if i + 1 < len(self.notation_log):
                p2, r2, c2 = self.notation_log[i + 1]
                if p2 == PLAYER_WHITE:
                    wm = self._cell_to_notation(r2, c2)
                    i += 1
            pairs.append(f"{len(pairs)+1:2}. {bm}  {wm}")
            i += 1

        # Show last N pairs that fit
        row_h = 16
        max_rows = (sh - 26) // row_h
        visible = pairs[-max_rows:] if len(pairs) > max_rows else pairs

        for idx, line in enumerate(visible):
            colour = TEXT_DIM if idx < len(visible) - 1 else TEXT_PRIMARY
            lbl = self.tiny_font.render(line, True, colour)
            self.screen.blit(lbl, (sx + 6, sy + 24 + idx * row_h))

        # Replay overlay
        if self.replay_mode:
            step_surf = self.tiny_font.render(
                f"Replay {self.replay_step}/{len(self.replay_moves)}",
                True, TEXT_ACCENT
            )
            self.screen.blit(step_surf, (sx + 6, sy + sh - 18))

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

    def draw_menu_bar(self):
        """Render the persistent top menu bar strip with four action buttons
        (New Game, Undo, Redo, Options) and the game title right-aligned.
        The Options button is highlighted green while the overlay is open.
        Populates ``self._menubar_rects`` for click-hit-testing.
        """
        self._menubar_rects.clear()
        # Background strip
        pg.draw.rect(self.screen, (28, 28, 38),
                     (0, 0, self.screen_width, MENUBAR_HEIGHT))
        pg.draw.line(self.screen, (60, 60, 78),
                     (0, MENUBAR_HEIGHT - 1),
                     (self.screen_width, MENUBAR_HEIGHT - 1), 1)
        btn_h = 22
        btn_w = 80
        gap = 6
        btn_y = (MENUBAR_HEIGHT - btn_h) // 2
        bx = MARGIN
        buttons = [
            ("New Game", "new_game"),
            ("Undo",     "undo"),
            ("Redo",     "redo"),
            ("Options",  "options"),
        ]
        for label, key in buttons:
            active = (key == "options" and self.menu_open)
            rect = pg.Rect(bx, btn_y, btn_w, btn_h)
            bg = (55, 130, 80) if active else (42, 42, 56)
            pg.draw.rect(self.screen, bg, rect, border_radius=4)
            pg.draw.rect(self.screen, (75, 75, 96), rect, 1, border_radius=4)
            t = self.tiny_font.render(label, True,
                                      TEXT_PRIMARY if active else TEXT_DIM)
            self.screen.blit(t, (
                rect.x + rect.w // 2 - t.get_width() // 2,
                rect.y + rect.h // 2 - t.get_height() // 2,
            ))
            self._menubar_rects[key] = rect
            bx += btn_w + gap
        # Game title right-aligned
        title = self.small_font.render("Iago Deluxe", True, TEXT_ACCENT)
        self.screen.blit(title, (
            self.screen_width - title.get_width() - MARGIN,
            MENUBAR_HEIGHT // 2 - title.get_height() // 2,
        ))

    def draw_menu(self):
        """Render the Options overlay: semi-transparent backdrop, centred panel
        with four segmented-button rows (Mode, AI Level, Hints, Play as) and
        New Game / Close buttons.  The active selection in each row is
        highlighted green.  Play-as buttons are greyed when not in HvAI mode.
        Populates ``self._menu_rects`` for click-hit-testing.
        """
        self._menu_rects.clear()

        # Semi-transparent backdrop
        backdrop = pg.Surface(
            (self.screen_width, self.screen_height), pg.SRCALPHA
        )
        backdrop.fill((0, 0, 0, 185))
        self.screen.blit(backdrop, (0, 0))

        # Panel
        pw, ph = 368, 310
        px = (self.screen_width - pw) // 2
        py = (self.screen_height - ph) // 2
        pg.draw.rect(
            self.screen, (35, 35, 44),
            (px, py, pw, ph), border_radius=12
        )
        pg.draw.rect(
            self.screen, (90, 90, 108),
            (px, py, pw, ph), 2, border_radius=12
        )

        title = self.font.render("Options", True, TEXT_ACCENT)
        self.screen.blit(
            title, (px + pw // 2 - title.get_width() // 2, py + 10)
        )

        cy = py + 52
        row_h = 48
        lbl_x = px + 12
        btn_x0 = px + 110
        btn_area_w = pw - 122

        def draw_row(label, choices, active_idx, key, enabled=True):
            nonlocal cy
            lbl_col = TEXT_DIM if enabled else (65, 65, 72)
            lbl = self.small_font.render(label, True, lbl_col)
            self.screen.blit(lbl, (lbl_x, cy + 8))
            n = len(choices)
            btn_w = (btn_area_w - 4 * (n - 1)) // n
            self._menu_rects[key] = []
            for i, ch in enumerate(choices):
                bx = btn_x0 + i * (btn_w + 4)
                rect = pg.Rect(bx, cy, btn_w, 28)
                active = i == active_idx
                if not enabled:
                    bg, tc = (48, 48, 54), (72, 72, 80)
                elif active:
                    bg, tc = (55, 130, 80), TEXT_PRIMARY
                else:
                    bg, tc = (54, 54, 66), TEXT_DIM
                pg.draw.rect(self.screen, bg, rect, border_radius=5)
                pg.draw.rect(
                    self.screen, (88, 88, 102), rect, 1, border_radius=5
                )
                t = self.tiny_font.render(ch, True, tc)
                self.screen.blit(
                    t,
                    (
                        rect.x + rect.w // 2 - t.get_width() // 2,
                        rect.y + rect.h // 2 - t.get_height() // 2,
                    ),
                )
                self._menu_rects[key].append((rect, i))
            cy += row_h

        draw_row(
            "Mode",
            [MODE_LABELS[m] for m in MODES],
            MODES.index(self.game_mode),
            "mode",
        )
        diff_names = [
            DIFFICULTY_LEVELS[i][0] for i in range(1, MAX_DIFFICULTY + 1)
        ]
        draw_row("AI Level", diff_names, self.ai.difficulty - 1, "difficulty")
        draw_row(
            "Hints",
            ["Off", "On"],
            1 if self.show_valid_moves else 0,
            "hints",
        )
        draw_row(
            "Play as",
            ["Black", "White"],
            self.player_color - 1,
            "color",
            enabled=(self.game_mode == MODE_HvAI),
        )

        cy += 4
        bw2 = 130
        ng_rect = pg.Rect(px + pw // 2 - bw2 - 6, cy, bw2, 30)
        cl_rect = pg.Rect(px + pw // 2 + 6, cy, bw2, 30)
        pg.draw.rect(self.screen, (50, 110, 55), ng_rect, border_radius=6)
        pg.draw.rect(self.screen, (110, 55, 55), cl_rect, border_radius=6)
        for rect, text in ((ng_rect, "New Game"), (cl_rect, "Close  [O]")):
            t = self.small_font.render(text, True, TEXT_PRIMARY)
            self.screen.blit(
                t,
                (
                    rect.centerx - t.get_width() // 2,
                    rect.centery - t.get_height() // 2,
                ),
            )
        self._menu_rects["new_game"] = [(ng_rect, 0)]
        self._menu_rects["close"] = [(cl_rect, 0)]

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
