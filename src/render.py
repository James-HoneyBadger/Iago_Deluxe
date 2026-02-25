"""
render.py – RenderMixin for Iago Deluxe.

Contains all pygame drawing methods.  ``Game`` inherits from ``RenderMixin``
so these methods have full access to ``self`` (the game instance) while living
in a separate, smaller module.
"""

import pygame as pg
import pygame.gfxdraw
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from board import Board
    from ai import AI as AIType
    from config import GameStats

from config import (
    EMPTY, PLAYER_BLACK, PLAYER_WHITE,
    MARGIN, MENUBAR_HEIGHT, CELL_SIZE, HISTORY_WIDTH,
    GREEN, DARK_GREEN,
    BG_DARK, TEXT_PRIMARY, TEXT_DIM, TEXT_ACCENT,
    HISTORY_BG, WIN_BAR_BLACK, WIN_BAR_WHITE, WIN_BAR_BG,
    HOVER_FLIP, LAST_MOVE_RING,
    MODE_HvAI, MODES, MODE_LABELS, _COL_LETTERS,
)
from ai import MAX_DIFFICULTY, DIFFICULTY_LEVELS


class RenderMixin:
    """Mixin that provides all draw_* methods for the Game class.

    No ``__init__`` is defined here; the methods rely on attributes created by
    ``Game.__init__`` (``self.screen``, ``self.board``, ``self.font``, etc.).
    """

    # ------------------------------------------------------------------
    # Attribute declarations for the type-checker.
    # These are all set by Game.__init__; they are listed here so that mypy
    # can resolve them when type-checking this mixin in isolation.
    # ------------------------------------------------------------------
    if TYPE_CHECKING:
        screen: pg.Surface
        board: "Board"
        ai: "AIType"
        stats: "GameStats"
        font: pg.font.Font
        small_font: pg.font.Font
        tiny_font: pg.font.Font
        board_size: int
        board_top: int
        board_px: int
        screen_width: int
        screen_height: int
        ui_height: int
        game_mode: str
        player_color: int
        show_valid_moves: bool
        menu_open: bool
        ai_thinking: bool
        replay_mode: bool
        replay_step: int
        replay_moves: List[Any]
        last_move: Optional[Tuple[int, int]]
        hover_cell: Optional[Tuple[int, int]]
        hint_move: Optional[Tuple[int, int]]
        notation_log: List[Any]
        _menubar_rects: Dict[str, Any]
        _menu_rects: Dict[str, Any]

        def get_animation_scale(self, row: int, col: int) -> float: ...

    # ------------------------------------------------------------------
    # Top-level draw orchestrator
    # ------------------------------------------------------------------

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
                self.game_mode == "hvh"
                or self.board.current_player == self.player_color
            )
            if human_turn:
                self.draw_valid_moves()
        self.draw_history_sidebar()
        self.draw_ui()
        if self.menu_open:
            self.draw_menu()
        pg.display.flip()

    # ------------------------------------------------------------------
    # Board + pieces
    # ------------------------------------------------------------------

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
                pg.draw.rect(
                    self.screen, DARK_GREEN, (x, y, CELL_SIZE, CELL_SIZE), 1
                )

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
            lx = (MARGIN + col * CELL_SIZE
                  + CELL_SIZE // 2 - lbl.get_width() // 2)
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

        # 1 – drop shadow
        shadow_off = max(2, radius // 5)
        shadow_r = radius - 1
        pg.draw.circle(surf, (12, 12, 12),
                       (cx + shadow_off, cy + shadow_off), shadow_r)

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
            pg.gfxdraw.aacircle(surf, cx, cy, radius, rim)
            pg.gfxdraw.aacircle(surf, cx, cy, radius - 1, rim)
        except AttributeError:
            pg.draw.circle(surf, rim, (cx, cy), radius, 1)

    # ------------------------------------------------------------------
    # Valid-move indicators and hover preview
    # ------------------------------------------------------------------

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
            hover_flips = self.board.get_flips(
                self.hover_cell[0], self.hover_cell[1], current
            )
            for fr, fc in hover_flips:
                hx = MARGIN + fc * CELL_SIZE
                hy = self.board_top + fr * CELL_SIZE
                tint = pg.Surface((CELL_SIZE, CELL_SIZE), pg.SRCALPHA)
                tint.fill((*HOVER_FLIP, 90))
                self.screen.blit(tint, (hx, hy))

        for row, col in valid_moves:
            cx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
            cy = self.board_top + row * CELL_SIZE + CELL_SIZE // 2
            is_best = self.hint_move == (row, col)
            if is_best:
                pg.draw.circle(self.screen, (200, 160, 0), (cx, cy), 13)
                pg.draw.circle(self.screen, (255, 215, 0), (cx, cy), 11)
                pg.draw.circle(self.screen, (255, 240, 80), (cx, cy), 8)
                star = self.tiny_font.render("\u2605", True, (80, 50, 0))
                self.screen.blit(star, (
                    cx - star.get_width() // 2,
                    cy - star.get_height() // 2,
                ))
            else:
                pg.draw.circle(self.screen, (60, 160, 90), (cx, cy), 9)
                pg.draw.circle(self.screen, (120, 210, 140), (cx, cy), 7)
                pg.draw.circle(self.screen, (180, 240, 190), (cx, cy), 4)

    # ------------------------------------------------------------------
    # UI info panel
    # ------------------------------------------------------------------

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

        panel_rect = (
            0, self.board_top + self.board_px, self.screen_width, self.ui_height
        )
        pg.draw.rect(self.screen, BG_DARK, panel_rect)

        sep_y = self.board_top + self.board_px
        pg.draw.line(self.screen, (60, 60, 60),
                     (0, sep_y), (self.screen_width, sep_y), 1)

        # ── Row 1: score + mode ──────────────────────────────────────────
        black_score, white_score = self.board.get_score()
        score_text = f"Black: {black_score}   White: {white_score}"
        score_surf = self.font.render(score_text, True, TEXT_PRIMARY)
        self.screen.blit(score_surf, (MARGIN, ui_y))

        mode_lbl = self.tiny_font.render(
            MODE_LABELS[self.game_mode], True, TEXT_DIM
        )
        self.screen.blit(mode_lbl, (MARGIN, ui_y + 28))

        ai_lbl = self.tiny_font.render(f"AI: {self.ai.name}", True, TEXT_DIM)
        self.screen.blit(ai_lbl, (MARGIN + 85, ui_y + 28))

        # ── Row 2: player turn / game-over ───────────────────────────────
        if self.replay_mode:
            step_max = len(self.replay_moves)
            player_text = f"Replay {self.replay_step}/{step_max}  \u25ba Space/Click"
        elif self.board.game_over:
            if self.board.winner == PLAYER_BLACK:
                player_text = "Black wins!"
            elif self.board.winner == PLAYER_WHITE:
                player_text = "White wins!"
            else:
                player_text = "It's a draw!"
        else:
            player_text = (
                "Black's turn"
                if self.board.current_player == PLAYER_BLACK
                else "White's turn"
            )
        is_end = self.board.game_over and not self.replay_mode
        player_surf = self.font.render(
            player_text, True, TEXT_ACCENT if is_end else TEXT_PRIMARY
        )
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
            thinking_surf = self.small_font.render(
                "AI thinking...", True, TEXT_ACCENT
            )
            self.screen.blit(thinking_surf, (MARGIN, ui_y + 98))
        elif (self.game_mode == MODE_HvAI
              and self.stats.current_streak != 0):
            s = self.stats.current_streak
            streak_text = (
                f"Win streak: {s}" if s > 0 else f"Loss streak: {-s}"
            )
            streak_color = (100, 220, 100) if s > 0 else (220, 100, 100)
            streak_surf = self.small_font.render(
                streak_text, True, streak_color
            )
            self.screen.blit(streak_surf, (MARGIN, ui_y + 98))

        # ── Hotkey reference (two columns) ───────────────────────────────
        col1 = MARGIN + self.board_px + 8
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

    # ------------------------------------------------------------------
    # Win-probability helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Move-history sidebar
    # ------------------------------------------------------------------

    def draw_history_sidebar(self):
        """Render the move-history panel to the right of the board.

        Moves are displayed in paired rows (Black / White) using algebraic
        notation.  Only the last N rows that fit in the panel are shown;
        the most recent move is highlighted in TEXT_PRIMARY.  During replay
        mode the current step counter is shown at the bottom.
        """
        sx = MARGIN + self.board_px
        sy = self.board_top
        sw = HISTORY_WIDTH
        sh = self.board_px

        pg.draw.rect(self.screen, HISTORY_BG, (sx, sy, sw, sh))
        pg.draw.line(self.screen, (60, 60, 60), (sx, sy), (sx, sy + sh), 1)

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

        row_h = 16
        max_rows = (sh - 26) // row_h
        visible = pairs[-max_rows:] if len(pairs) > max_rows else pairs

        for idx, line in enumerate(visible):
            colour = TEXT_DIM if idx < len(visible) - 1 else TEXT_PRIMARY
            lbl = self.tiny_font.render(line, True, colour)
            self.screen.blit(lbl, (sx + 6, sy + 24 + idx * row_h))

        if self.replay_mode:
            step_surf = self.tiny_font.render(
                f"Replay {self.replay_step}/{len(self.replay_moves)}",
                True, TEXT_ACCENT,
            )
            self.screen.blit(step_surf, (sx + 6, sy + sh - 18))

    # ------------------------------------------------------------------
    # Top menu bar
    # ------------------------------------------------------------------

    def draw_menu_bar(self):
        """Render the persistent top menu bar strip with four action buttons
        (New Game, Undo, Redo, Options) and the game title right-aligned.
        The Options button is highlighted green while the overlay is open.
        Populates ``self._menubar_rects`` for click-hit-testing.
        """
        self._menubar_rects.clear()
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
            active = key == "options" and self.menu_open
            rect = pg.Rect(bx, btn_y, btn_w, btn_h)
            bg = (55, 130, 80) if active else (42, 42, 56)
            pg.draw.rect(self.screen, bg, rect, border_radius=4)
            pg.draw.rect(self.screen, (75, 75, 96), rect, 1, border_radius=4)
            t = self.tiny_font.render(
                label, True, TEXT_PRIMARY if active else TEXT_DIM
            )
            self.screen.blit(t, (
                rect.x + rect.w // 2 - t.get_width() // 2,
                rect.y + rect.h // 2 - t.get_height() // 2,
            ))
            self._menubar_rects[key] = rect
            bx += btn_w + gap
        title = self.small_font.render("Iago Deluxe", True, TEXT_ACCENT)
        self.screen.blit(title, (
            self.screen_width - title.get_width() - MARGIN,
            MENUBAR_HEIGHT // 2 - title.get_height() // 2,
        ))

    # ------------------------------------------------------------------
    # Options overlay
    # ------------------------------------------------------------------

    def draw_menu(self):
        """Render the Options overlay: semi-transparent backdrop, centred panel
        with four segmented-button rows (Mode, AI Level, Hints, Play as) and
        New Game / Close buttons.  The active selection in each row is
        highlighted green.  Play-as buttons are greyed when not in HvAI mode.
        Populates ``self._menu_rects`` for click-hit-testing.
        """
        self._menu_rects.clear()

        backdrop = pg.Surface(
            (self.screen_width, self.screen_height), pg.SRCALPHA
        )
        backdrop.fill((0, 0, 0, 185))
        self.screen.blit(backdrop, (0, 0))

        pw, ph = 368, 310
        px = (self.screen_width - pw) // 2
        py = (self.screen_height - ph) // 2
        pg.draw.rect(
            self.screen, (35, 35, 44), (px, py, pw, ph), border_radius=12
        )
        pg.draw.rect(
            self.screen, (90, 90, 108), (px, py, pw, ph), 2, border_radius=12
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
                self.screen.blit(t, (
                    rect.x + rect.w // 2 - t.get_width() // 2,
                    rect.y + rect.h // 2 - t.get_height() // 2,
                ))
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
            self.screen.blit(t, (
                rect.centerx - t.get_width() // 2,
                rect.centery - t.get_height() // 2,
            ))
        self._menu_rects["new_game"] = [(ng_rect, 0)]
        self._menu_rects["close"] = [(cl_rect, 0)]
