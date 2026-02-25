# Iago Deluxe

A polished Reversi (Othello) game written in Python/pygame with a strong AI opponent and a modern dark-themed UI.

## ✨ Features

- **Four AI difficulty levels** — Easy (random) → Medium (heuristic) → Hard (1 s search) → Expert (3 s search)
- **Opening book** — Hard/Expert consult a validated opening library for the first few moves
- **Best-move hints** — gold star ★ marks the AI's recommended square; green dots show all other legal moves
- **Win-probability bar** — live estimate of each player's winning chance based on position evaluation
- **Move-history sidebar** — full algebraic notation log (e.g. `e6`, `d3`) for every move played
- **Undo / Redo** — unlimited step-back and step-forward through the game
- **Wave-flip animation** — captured pieces ripple outward from the placed disc
- **Options overlay** — change mode, AI level, hints, and play colour without leaving the game
- **Top menu bar** — one-click New Game, Undo, Redo, and Options
- **Three game modes** — Human vs AI, Human vs Human, AI vs AI demo
- **Save / Load / Replay** — persist games to JSON and step through them later
- **Programmatic sound** — move/win/lose/draw audio generated at runtime (no external files)
- **Statistics** — win/loss/draw totals and current streak saved to `stats.json`

## 🚀 Quick Start

```bash
# First-time setup (creates .venv and installs pygame)
./setup.sh

# Launch the game
./play.sh
```

Or run directly:
```bash
.venv/bin/python3 src/main.py
```

## 🎮 Controls

| Input | Action |
|---|---|
| **Left click** on a green dot or gold star | Place piece |
| **O** or **Tab** | Toggle Options overlay |
| **R** | New game |
| **U** | Undo last move |
| **Y** | Redo undone move |
| **H** | Toggle move hints |
| **D** | Cycle AI difficulty |
| **M** | Cycle game mode |
| **S** | Save game to `saved_game.json` |
| **L** | Load and replay saved game |
| **Space / P** | Advance replay one move |
| **ESC** | Close overlay / quit |

## 🤖 AI Difficulty

| Level | Name | Algorithm |
|---|---|---|
| 1 | Easy | Random legal move |
| 2 | Medium | Instant heuristic (corners/edges/X-squares) |
| 3 | Hard | Iterative-deepening minimax, 1-second budget |
| 4 | Expert | Iterative-deepening minimax, 3-second budget |

Levels 3 and 4 use alpha-beta pruning and consult an opening book for the first moves.

## 📁 Project Structure

```
Iago_Deluxe/
├── main.py              # Entry point (delegates to src/game.py)
├── play.sh              # Launcher script
├── setup.sh             # One-time venv + dependency installer
├── requirements.txt     # Python dependencies (pygame)
├── stats.json           # Persisted game statistics
│
├── src/
│   ├── config.py        # All constants, colours, dataclasses
│   ├── board.py         # Pure game logic (no pygame dependency)
│   ├── ai.py            # AI opponent (four difficulty levels)
│   ├── game.py          # Pygame window, render pipeline, main loop
│   ├── Reversi.py       # Legacy shim (not used at runtime)
│   ├── logger.py        # File-rotation logging helper
│   └── error_handling.py# Custom exceptions
│
├── tests/
│   ├── test_board.py         # Board logic unit tests
│   ├── test_ai.py            # AI behaviour unit tests
│   ├── test_settings.py      # GameSettings / GameStats tests
│   ├── test_all_functions.py # Comprehensive coverage (55 tests)
│   └── run_tests.py          # Convenience test runner
│
└── docs/
    ├── USER_GUIDE.md
    ├── IMPLEMENTATION_SUMMARY.md
    └── AI_LEVELS_VERIFICATION.md
```

## 🧪 Running Tests

```bash
# All tests (83 total, all should pass)
.venv/bin/python3 -m pytest tests/ -v

# With coverage
.venv/bin/python3 -m pytest --cov=src tests/
```

## 📚 Documentation

- [User Guide](docs/USER_GUIDE.md) — detailed controls and UI walkthrough
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) — architecture and algorithm details

## 📝 License

See [LICENSE](LICENSE).

---

**Version:** 3.0 — Deluxe Edition


