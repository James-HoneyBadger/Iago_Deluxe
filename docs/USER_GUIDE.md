# Iago Deluxe — User Guide

## Starting the Game

```bash
./play.sh                        # recommended (uses .venv automatically)
.venv/bin/python3 src/main.py    # direct invocation
```

---

## Window Layout

```
┌──────────────────────────────────────────────────────┐
│  [New Game]  [Undo]  [Redo]  [Options]    Iago Deluxe │  ← menu bar (32 px)
├──────────────────────────────────────────────────────┤
│                                          │ Move history│
│               8 × 8 board               │  sidebar    │
│                                          │             │
├──────────────────────────────────────────┤             │
│  Score | Mode            turn / game-over│             │
│  Win-probability bar  (B ██████░░ W)     │  Hotkeys    │
└──────────────────────────────────────────────────────┘
```

### Menu bar
Four buttons at the top of the window: **New Game**, **Undo**, **Redo**, and **Options**.
The Options button turns green while the overlay is open.

### Board area
- **Green dots** — legal moves for the current player.
- **Gold star ★** — the AI's recommended best move (shown when hints are on).
- **Hover preview** — move your cursor over a legal cell to see which pieces would flip (tinted green).
- **Gold ring** — marks the square where the last move was played.

### Win-probability bar
Displayed below the board during play.  The bar shows `B xx% ←→ W xx%`, updated after
every move using the AI's position evaluation.

### Move-history sidebar
All moves in full algebraic notation (e.g. `e6`, `d3`) from the start of the game.
The most recent move is highlighted.  In replay mode a step counter is shown at the bottom.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| **O** or **Tab** | Toggle Options overlay |
| **R** | New game |
| **U** | Undo last move |
| **Y** | Redo undone move |
| **H** | Toggle move hints (green dots + gold star) |
| **D** | Cycle AI difficulty (Easy → Medium → Hard → Expert) |
| **M** | Cycle game mode (HvAI → HvH → AvA) |
| **S** | Save game to `saved_game.json` |
| **L** | Load saved game and enter replay mode |
| **Space** or **P** | Advance replay by one move |
| **ESC** | Close overlay; press again to quit (auto-saves) |

---

## Options Overlay

Open with **O**, **Tab**, or the Options button in the menu bar.

| Row | Option | Values |
|---|---|---|
| Mode | Game mode | Human vs AI · Human vs Human · AI vs AI |
| AI Level | Difficulty | Easy · Medium · Hard · Expert |
| Hints | Move indicators | On · Off |
| Play as | Your colour | Black · White (HvAI only) |

**New Game** button applies all changes and starts a fresh game.
**Close** (or press **O** / **ESC**) returns without restarting.

> Changing "Play as" always starts a new game automatically.

---

## AI Difficulty

| Level | Name | Description |
|---|---|---|
| 1 | Easy | Random legal move — good for beginners |
| 2 | Medium | Instant heuristic: favours corners and edges, avoids X-squares |
| 3 | Hard | Iterative-deepening minimax with alpha-beta, 1-second budget |
| 4 | Expert | Same algorithm, 3-second budget; stronger end-game play |

Hard and Expert use an opening book for the first few moves.

---

## Move Hints

When hints are enabled (**H** to toggle):

- **Gold star ★** with amber glow rings — the AI's top recommendation.
- **Bright green dot** — other legal moves.
- **Hover tint** — cells that would flip if you clicked the hovered square.

All indicators disappear when it is the AI's turn or when hints are turned off.

---

## Undo and Redo

- **U** (or Undo button) steps back one move.  In Human-vs-AI mode this undoes both
  the AI's response and your preceding move.
- **Y** (or Redo button) reapplies the last undone move.
- The undo/redo stack is cleared when a new game starts.

---

## Save / Load / Replay

Press **S** to save the current game to `saved_game.json`.

Press **L** to load that file and enter **replay mode**:
- The board resets to the opening position.
- Press **Space** or **P** (or click the board area) to advance one move at a time.
- The move counter in the history sidebar tracks your position.
- Press **ESC** to exit replay at any time.

The game is also auto-saved to `autosave.json` when you close the window.

---

## Statistics

Wins, losses, draws, and streaks are automatically saved to `stats.json` after each
game and displayed in the win/loss streak line at the bottom of the UI panel.

---

## Game Rules (quick reference)

- The board starts with two Black and two White pieces in the centre.
- Black always moves first.
- A move is legal only if it captures at least one opponent piece.
- Captured pieces (those between your new piece and another of yours in a straight line)
  are flipped to your colour.
- If a player has no legal move, their turn is skipped; if neither can move, the game ends.
- The player with more pieces at the end wins.
