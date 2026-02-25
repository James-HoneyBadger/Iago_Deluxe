# Iago Deluxe — Implementation Summary

## Architecture Overview

The project is split into four source files under `src/`:

| File | Purpose |
|---|---|
| `config.py` | All constants, colour tuples, and dataclasses; no logic |
| `board.py` | Pure Reversi rules; no pygame dependency |
| `ai.py` | AI opponent (four difficulty levels) |
| `game.py` | Pygame window, event loop, render pipeline, game coordination |

`main.py` at the root is a two-line entry point that imports and calls `Game().run()`.

---

## Board Logic (`src/board.py`)

### `Board` class

- `grid`: 2-D list `[row][col]` of `EMPTY | PLAYER_BLACK | PLAYER_WHITE`.
- `make_move(row, col, player)`: places a piece, delegates flip detection to
  `_flip_direction()` for each of 8 directions, then calls `switch_player()`.
  Returns the list of flipped cells (used to start wave animations).
- `get_flips(row, col, player)`: pure query (no mutation) that returns which cells
  *would* be flipped — used by the hover-preview and AI speculative copies.
- `check_game_over()`: if the current player has no moves, passes the turn; if
  neither player has moves, sets `game_over = True` and resolves `winner`.

---

## AI Opponent (`src/ai.py`)

### Difficulty levels

| Level | Name | Algorithm |
|---|---|---|
| 1 | Easy | `random.choice(valid_moves)` |
| 2 | Medium | Instant positional heuristic — `_get_best_move_simple()` |
| 3 | Hard | Iterative deepening, 1-second budget — `_get_move_timed()` |
| 4 | Expert | Iterative deepening, 3-second budget — `_get_move_timed()` |

### Iterative deepening (`_get_move_timed`)

Runs alpha-beta minimax at increasing depths (1 to 15).  After each complete depth
the best move is recorded.  When 85 % of the time budget has elapsed, the search
stops and the best move from the last *complete* iteration is returned.  This
guarantees a legal move is always returned even if the first depth times out.

### Alpha-beta minimax (`_minimax_alpha_beta`)

Standard negamax with alpha-beta pruning.  Terminal states are scored ±10 000.
When the current player has no moves, the function passes (switches player and
recurses) rather than treating a forced-pass position as terminal.

### Static evaluation (`_evaluate_board_advanced`)

Combines five factors (from current-player's perspective):
1. **Material** — piece difference × 10
2. **Positional weight** — corner cells = 100, non-corner edges = 10
3. **Mobility** — legal-move count difference × 10
4. **Corner ownership** — count of corners × 20
5. **Edge ownership** — count of non-corner edge cells × 5

`evaluate_for_black()` wraps this with a sign flip when it's White's turn, so
the win-probability bar always gets a Black-perspective score.

### Opening book (`_OPENING_BOOK`)

A dictionary mapping the sequence of moves played so far (as a tuple of
`(player, row, col)` triples) to a response `(row, col)`.  Covers White's first
reply to each of Black's four standard opening moves, plus two second-ply
continuations.  Consulted only at difficulty ≥ 3.

### Best-move hints (`get_hint`)

Calls `_get_best_move_simple()` (the Medium-level heuristic) instantly, making it
safe to invoke every frame without blocking.  The `Game` class caches the result in
`self.hint_move` and refreshes it after every board change via `_refresh_hint()`.

---

## Game Rendering (`src/game.py`)

### Window layout constants

```
y = 0                      ← top of window
y = MENUBAR_HEIGHT (32)    ← bottom of menu bar strip
y = board_top              ← MENUBAR_HEIGHT + MARGIN (52)  ← row 0 of board
y = board_top + board_px   ← bottom of board
y = board_top + board_px + gap  ← top of UI info panel
```

`board_top` is computed in `__init__` and propagated to every draw method that
places board-relative content.

### Piece rendering (`_draw_piece_3d`)

Each disc is rendered as six overlapping circles: drop shadow → base colour →
offset body → soft highlight gradient → specular pinpoint → anti-aliased rim.

### Wave-flip animation (`_start_wave_flip_animations`)

When a move produces flips, `_start_wave_flip_animations` staggers the flip
`Animation` objects by Manhattan distance from the placed piece (50 ms per unit).
The `Animation` dataclass stores `start_scale`, `end_scale`, `start_time`, and
`anim_type` (`'place'` or `'flip'`).  `get_animation_scale()` interpolates the
radius used by `draw_pieces()`.

### Valid-move and hint indicators (`draw_valid_moves`)

Two rendering tiers:
- **Best move** (`hint_move`): three concentric glow rings (amber at r=13, gold at
  r=11, bright centre at r=8) plus a dark ★ rendered with `tiny_font`.
- **Other moves**: three concentric green circles (r=9, 7, 4).

### Win-probability bar (`_get_win_probability` + `draw_ui`)

`_get_win_probability()` returns a `float` in [0.0, 1.0] (1.0 = Black winning).
During play the raw evaluation is clamped to ±2000 and remapped; terminal positions
return exact values (1.0 / 0.5 / 0.0).  The bar is drawn as two filled rectangles
filling a 240 px track.

### Menu bar (`draw_menu_bar`)

A 32 px dark strip at y=0 with four `pg.Rect`s stored in `_menubar_rects`:
`new_game`, `undo`, `redo`, `options`.  The Options button uses a green fill while
`menu_open` is True.  The game title is right-aligned using `TEXT_ACCENT`.

### Options overlay (`draw_menu`)

Semi-transparent backdrop + centred panel with four segmented button rows (Mode,
AI Level, Hints, Play as) rendered using `_menu_rects`.  Play-as buttons are
dimmed when not in HvAI mode.  Route-on-click is handled by `_handle_menu_click()`.

---

## Undo / Redo

`save_game_state()` pushes a `GameState` snapshot onto `move_history` and clears
`redo_stack`.  `undo_move()` / `redo_move()` move the snapshot between the two stacks
and restore `board.grid`, `board.current_player`, `board.game_over`, etc.

---

## Sound Generation

All sound effects are synthesised at startup with `numpy` + `pygame.sndarray`:
- **move**: 100 ms 800 Hz tone
- **win**: 500 ms rising chirp (400 → 800 Hz)
- **lose**: 500 ms falling tone (600 → 300 Hz)
- **draw**: 300 ms 500 Hz tone

---

## Save / Load / Replay

`save_game()` writes `notation_log`, `current_player`, scores, and game-over state
to a JSON file.  `start_replay()` reads the log into `replay_moves` and enters
`replay_mode`; `replay_next()` calls `make_player_move()` for each step.

---

## Statistics

`GameStats` (dataclass from `config.py`) is serialised to/from `stats.json` by
`_load_stats()` / `_save_stats()`.  `current_streak` is positive for a win streak
and negative for a loss streak.

---

## Test Suite

83 tests across five files:

| File | Coverage |
|---|---|
| `test_board.py` | Core Board API, edge-case moves |
| `test_ai.py` | Difficulty levels, move quality |
| `test_settings.py` | GameSettings / GameStats dataclasses |
| `test_all_functions.py` | Every Board + AI method (55 tests) |
| `run_tests.py` | Convenience runner |

Run with:
```bash
.venv/bin/python3 -m pytest tests/ -v
```
