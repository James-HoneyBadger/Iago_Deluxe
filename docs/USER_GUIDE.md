# Iago Deluxe - User Guide

**Version:** 2.0.0  
**Last Updated:** November 19, 2025

Welcome to Iago Deluxe! This comprehensive guide will help you get the most out of your Reversi/Othello gaming experience.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Game Rules](#game-rules)
- [Playing the Game](#playing-the-game)
- [Strategy Guide](#strategy-guide)
- [Features & Settings](#features--settings)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Getting Started

### Installation

**Quick Install:**
```bash
git clone https://github.com/James-HoneyBadger/Iago_Deluxe.git
cd Iago_Deluxe
./setup.sh
```

**Manual Install:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### First Launch

**Recommended (using launcher):**
```bash
./play.sh
```

**Alternative methods:**
```bash
# Direct execution
.venv/bin/python3 main.py

# With custom settings
./play.sh -s 10 -d 4 -t ocean
```

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.7+ | 3.11+ |
| RAM | 256MB | 512MB |
| Disk Space | 50MB | 100MB |
| Display | 800×600 | 1920×1080 |
| OS | Any | Linux/macOS/Windows |

---

## Game Rules

### Reversi/Othello Basics

**Objective:** Have more pieces of your color on the board when the game ends.

**Setup:**
- 8×8 board (customizable to 4×4 through 16×16)
- 4 pieces placed in center:
  ```
      3 4 5 6
    3 . . . .
    4 . W B .
    5 . B W .
    6 . . . .
  ```
  Black plays first.

**Making Moves:**
1. Place your piece on an empty square
2. You must flank opponent's pieces (trap them between your pieces)
3. All flanked pieces flip to your color
4. If no legal moves, you pass
5. Game ends when:
   - Board is full, OR
   - Neither player can move

**Winning:**
- Player with most pieces wins
- Equal pieces = tie game

### Legal Moves

A move is legal if it flips at least one opponent piece:

**Example:**
```
  Current board:        After Black plays at (2,3):
  
  . . . . . . . .       . . . . . . . .
  . . . . . . . .       . . . . . . . .
  . . . . . . . .       . . B . . . . .
  . . . W B . . .       . . B B B . . .
  . . . B W . . .       . . . B W . . .
  . . . . . . . .       . . . . . . . .
  . . . . . . . .       . . . . . . . .
  . . . . . . . .       . . . . . . . .
  
  Black flips White piece at (3,4)
```

**Flanking Directions:**
- Horizontal (left/right)
- Vertical (up/down)
- Diagonal (4 directions)

**Important:**
- Must flip at least one piece
- Can flip in multiple directions simultaneously
- Cannot place on occupied squares
- Cannot place without flanking

---

## Playing the Game

### Understanding the Interface

**Main Game Screen:**
```
┌─────────────────────────────────────────┐
│  Iago Deluxe v2.0           [Menu Bar]   │
├─────────────────────────────────────────┤
│                                          │
│         ┌─────────────────┐             │
│         │                 │  Status:    │
│         │                 │  Your turn  │
│         │   Game Board    │             │
│         │     (8×8)       │  Score:     │
│         │                 │  Black: 12  │
│         │                 │  White: 8   │
│         └─────────────────┘             │
│                                          │
│  Hints: ON | Sound: ON | Theme: Classic │
└─────────────────────────────────────────┘
```

**Visual Elements:**

1. **Board Squares**
   - Green = Empty  square
   - Light highlight = Legal move (with hints ON)
   - Yellow highlight = Hover preview
   - Blue highlight = Last move

2. **Pieces**
   - Black disc = Black player
   - White disc = White player
   - Animated flipping when captured
   - Shadow effect for depth

3. **Status Area**
   - Current player turn
   - Live score count
   - Move timer (if enabled)
   - Hint status

### Making Your Move

**Mouse Control:**
1. Hover over squares to see preview
2. Legal moves highlighted (if hints enabled)
3. Click to place piece
4. Watch pieces flip!

**What You'll See:**
- Green highlights = Your legal moves
- Yellow overlay = Where piece will go
- Red X = Invalid move attempt
- Flip animation = Captured pieces

### Game Flow

**Turn Sequence:**
1. **Your Turn** - Make a move or pass
2. **AI Thinking** - (if playing vs computer)
3. **AI Move** - Watch AI's choice
4. **Update Board** - Pieces flip
5. **Next Turn** - Repeat

**Passing:**
- If you have no legal moves, turn automatically passes
- "No legal moves - Press any key to pass" appears
- Opponent gets another turn

**Game End:**
- Board full OR both players pass
- Final score calculated
- Winner announced
- Analysis available (press 'G')

---

## Strategy Guide

### Opening Strategy (Moves 1-20)

**Key Principles:**

1. **Control the Center**
   - Center squares are valuable early
   - Don't over-commit to edges early
   - Keep options open

2. **Minimize Your Mobility Loss**
   - Each move should give you future options
   - Avoid moves that limit your choices
   - Think 2-3 moves ahead

3. **Edge Piece Caution**
   - Early edge pieces can be dangerous
   - They're hard to defend
   - Exception: Setting up corners

**Good Opening Moves:**
```
Black's first 4 legal moves (any are reasonable):

  . . . . . . . .
  . . . . . . . .
  . . ①  . ② . . .      ① (2,3) - Standard
  . . . W B . . .       ② (2,5) - Aggressive
  . . . B W . . .       ③ (5,2) - Defensive
  . . ③  . ④  . . .      ④ (5,4) - Balanced
  . . . . . . . .
  . . . . . . . .
```

### Mid-Game Strategy (Moves 20-50)

**Key Principles:**

1. **Corner Strategy**
   - Corners are permanent (can't be flipped)
   - Control corners = control adjacent edges
   - Worth sacrificing pieces for corners

2. **Avoid X-Squares**
   ```
   X . . . . . . X    X-squares (corners of board)
   . . . . . . . .    give opponent corner access!
   . . . . . . . .    Avoid unless necessary
   . . . . . . . .
   . . . . . . . .
   . . . . . . . .
   . . . . . . . .
   X . . . . . . X
   ```

3. **Tempo Control**
   - Force opponent into bad moves
   - Limit their options
   - Create "forced" sequences

**Corner Priority:**
```
Best to Worst Squares (8×8 board):

A = Corner (Best - permanent)
B = Edge (Good - semi-stable)
C = Inner (Okay - flexible)
X = X-square (Worst - gives corners)

A X B B B B X A
X X C C C C X X
B C C C C C C B
B C C C C C C B
B C C C C C C B
B C C C C C C B
X X C C C C X X
A X B B B B X A
```

### Endgame Strategy (Last 10-15 Moves)

**Key Principles:**

1. **Count Pieces**
   - Know if you're ahead or behind
   - Play differently based on position
   - If ahead: limit opponent options
   - If behind: create chaos, take risks

2. **Parity**
   - Try to make the last move
   - Last move often swings the game
   - Count remaining empty squares

3. **Sweep Sequences**
   - Clear entire rows/columns
   - Convert edge positions
   - Lock in your advantage

**Counting Example:**
```
With 10 empty squares left:
Black: 28 pieces
White: 26 pieces

Black is ahead by 2, but:
- 10 moves left
- Each move flips 1-10+ pieces
- Game still very much in play!

Strategy: Black should play defensively
```

### AI Difficulty Strategies

**Level 1-2 (Beginner):**
- Random-ish play
- Good for learning rules
- Easy to beat with basic strategy
- Strategy: Just avoid major blunders

**Level 3-4 (Intermediate):**
- Considers piece count and mobility
- Makes occasional mistakes
- Good challenge for casual players
- Strategy: Control corners, avoid X-squares

**Level 5-6 (Expert):**
- Deep search (5-6 moves ahead)
- Rarely makes mistakes
- Very strong endgame
- Strategy: Perfect play required, study openings

### Common Mistakes to Avoid

**Beginner Mistakes:**
1. ❌ Playing to X-squares early
2. ❌ Ignoring corner opportunities
3. ❌ Taking many pieces every move
4. ❌ Not thinking ahead

**Intermediate Mistakes:**
1. ❌ Over-valuing piece count early
2. ❌ Giving opponent corners
3. ❌ Forgetting about parity
4. ❌ Rushing the endgame

**Advanced Mistakes:**
1. ❌ Predictable opening play
2. ❌ Ignoring tempo
3. ❌ Poor endgame counting
4. ❌ Giving up when behind

---

## Features & Settings

### Game Menu

**New Game**
- Starts fresh game
- Keeps current settings
- Keyboard: 'N'

**Board Size**
- 4×4 (Fast games, ~10 moves)
- 6×6 (Quick games, ~20 moves)
- 8×8 (Standard, ~40 moves)
- 10×10 (Long games, ~60 moves)
- 12×12 (Extended, ~90 moves)
- 14×14 (Marathon, ~120 moves)
- 16×16 (Epic, ~160 moves)

**Save/Load Game**
- Save current position
- Load previously saved game
- Formats: PGN (standard) or JSON
- Location: `data/` directory

**Quit**
- Exit game
- Settings auto-saved
- Keyboard: 'Q'

### AI Menu

**Difficulty Levels:**

| Level | Name | Depth | Avg Time | Description |
|-------|------|-------|----------|-------------|
| 1 | Beginner | 1 | <0.1s | Makes obvious mistakes |
| 2 | Easy | 2 | <0.2s | Plays basic strategy |
| 3 | Medium | 3 | <0.5s | Decent opponent |
| 4 | Normal | 4 | <1.0s | Challenging |
| 5 | Hard | 5 | <2.0s | Very strong |
| 6 | Expert | 6 | <5.0s | Maximum strength |

**Play As:**
- Black (Human) - You play as black
- White (Human) - You play as white
- Both AI - Watch AI play itself
- Keyboard: 'A' to toggle

### Settings Menu

**Themes:**

1. **Classic** (Default)
   - Green board
   - Traditional look
   - Easy on eyes

2. **Ocean**
   - Blue water theme
   - Calming colors
   - Good contrast

3. **Sunset**
   - Orange/purple palette
   - Warm colors
   - Unique look

4. **Midnight**
   - Dark mode
   - Reduced eye strain
   - Modern appearance

5. **Forest**
   - Deep green
   - Natural look
   - Alternative classic

**Sound Effects:**
- ON: Piece placement sounds
- OFF: Silent mode
- Keyboard: 'M'

**Move Hints:**
- ON: Shows legal moves (green highlights)
- OFF: No visual hints
- Keyboard: 'H'

**Move Preview:**
- ON: Shows piece placement preview
- OFF: No preview overlay
- Keyboard: 'I'

### View Menu

**Analysis Window**
- Real-time move analysis
- Quality ratings
- Strategic impact
- Keyboard: 'V'

**Game Statistics**
- Per-difficulty win rates
- Total games played
- Win percentage
- Historical data

**Tutorial**
- Interactive guide
- Step-by-step instructions
- Strategy tips
- Keyboard: 'T'

---

## Keyboard Shortcuts

### Essential Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `N` | New Game | Start fresh game |
| `Q` | Quit | Exit application |
| `ESC` | Pause | Show pause menu |
| `U` | Undo | Take back last move |
| `R` | Redo | Replay undone move |

### Game Control

| Key | Action | Description |
|-----|--------|-------------|
| `S` | Save | Save current game |
| `L` | Load | Load saved game |
| `H` | Hints | Toggle move hints |
| `I` | Preview | Toggle move preview |
| `M` | Sound | Toggle sound effects |

### AI & Analysis

| Key | Action | Description |
|-----|--------|-------------|
| `A` | Toggle AI | Switch AI on/off for current player |
| `D` | Difficulty | Cycle AI difficulty (1-6) |
| `V` | Analysis | Toggle analysis window |
| `G` | Game Analysis | Show post-game analysis |
| `T` | Tutorial | Open interactive tutorial |

### View Control

| Key | Action | Description |
|-----|--------|-------------|
| `F1` | Help | Show help screen |
| `F11` | Fullscreen | Toggle fullscreen mode |
| `+` | Zoom In | Increase board size |
| `-` | Zoom Out | Decrease board size |

---

## Troubleshooting

### Game Won't Start

**Problem:** Double-clicking doesn't launch game

**Solutions:**
```bash
# Method 1: Use launcher script
./play.sh

# Method 2: Check Python version
python3 --version  # Should be 3.7+

# Method 3: Reinstall dependencies
./setup.sh

# Method 4: Manual launch
.venv/bin/python3 main.py
```

### Performance Issues

**Problem:** Game runs slowly or lags

**Solutions:**
1. **Lower AI difficulty:**
   ```bash
   ./play.sh -d 3  # Use level 3 instead of 6
   ```

2. **Reduce board size:**
   ```bash
   ./play.sh -s 8  # Use 8×8 instead of 16×16
   ```

3. **Disable animations:**
   - Settings → Animations → OFF

4. **Close other applications:**
   - Free up RAM and CPU

### Sound Not Working

**Problem:** No sound effects when placing pieces

**Solutions:**
1. Check sound setting:
   - Settings → Sound → ON

2. Test system audio:
   - Play music or video
   - Check volume levels

3. Reinstall pygame:
   ```bash
   .venv/bin/pip install --upgrade pygame
   ```

4. Run without sound:
   ```bash
   ./play.sh --no-sound
   ```

### Save Files Not Loading

**Problem:** "Corrupted save file" error

**Solutions:**
1. **Check file format:**
   - Must be .pgn or .json
   - Located in `data/` directory

2. **Verify file contents:**
   ```bash
   cat data/saved_game.pgn  # Should show game notation
   ```

3. **Use recent autosave:**
   - Check for latest file
   - `data/reversi_game_YYYYMMDD_HHMMSS.pgn`

4. **Start new game:**
   - File may be genuinely corrupted
   - Create new save from working game

### Settings Not Saving

**Problem:** Preferences reset each launch

**Solutions:**
1. **Check directory permissions:**
   ```bash
   ls -la config/
   # Should show iago-settings.json
   ```

2. **Verify file permissions:**
   ```bash
   chmod 644 config/iago-settings.json
   ```

3. **Check disk space:**
   ```bash
   df -h  # Ensure space available
   ```

4. **Manual settings creation:**
   ```bash
   mkdir -p config
   touch config/iago-settings.json
   ```

---

## FAQ

### General Questions

**Q: Is this the same as Othello?**  
A: Yes! Reversi and Othello are the same game. Othello is the trademarked name. We use "Reversi" as the generic term.

**Q: Can I play online against other people?**  
A: Not yet. Network multiplayer is planned for v2.1 (Q1 2026). Currently, you can:
- Play vs AI (6 difficulty levels)
- Play vs local human (hot-seat)
- Watch AI vs AI

**Q: Is this free?**  
A: Yes! Iago Deluxe is open source and completely free. See LICENSE file for details.

**Q: Can I contribute?**  
A: Absolutely! See CONTRIBUTING.md for guidelines. We welcome:
- Bug reports
- Feature suggestions
- Code contributions
- Documentation improvements
- Testing and feedback

### Gameplay Questions

**Q: What's the best opening move?**  
A: All 4 initial moves are equally valid. Common choices:
- (2,3) or (5,4) - "Diagonal" opening (balanced)
- (2,5) or (5,2) - "Parallel" opening (aggressive)
Research suggests minimal advantage to any particular opening.

**Q: Should I try to get as many pieces as possible early?**  
A: **No!** This is a common beginner mistake. Early piece count doesn't matter. Focus on:
- Controlling corners
- Maintaining mobility
- Good positional play

**Q: What if I have no legal moves?**  
A: You must pass. The game automatically passes for you and gives your opponent another turn. If neither player can move, game ends.

**Q: Can I take back moves?**  
A: Yes! Press 'U' to undo. You can undo multiple moves. However:
- Undo is disabled in tournament mode
- AI will re-think after undo
- Cannot undo after game ends

**Q: How does the AI work?**  
A: The AI uses Minimax algorithm with alpha-beta pruning:
- Searches move tree 1-6 moves ahead
- Evaluates positions based on multiple factors
- Higher difficulty = deeper search
- See DEVELOPMENT.md for technical details

### Technical Questions

**Q: What Python version do I need?**  
A: Python 3.7 or higher. Tested on:
- Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- Recommended: Python 3.11+

**Q: Will this work on my operating system?**  
A: Yes! Iago Deluxe works on:
- ✅ Linux (all major distributions)
- ✅ macOS (10.14+)
- ✅ Windows (10, 11)
- ✅ BSD variants
- ❓ Other Unix-like systems (probably works)

**Q: How much disk space does it need?**  
A: Minimal:
- Program: ~20MB
- Virtual environment: ~30MB
- Save files: ~5KB each
- Logs: Max 40MB (auto-rotated)
- **Total: ~100MB maximum**

**Q: Can I run this on a Raspberry Pi?**  
A: Yes! Tested on:
- Raspberry Pi 4 (works great)
- Raspberry Pi 3 (works well, lower AI levels)
- Raspberry Pi Zero (works, limit to AI level 3)

**Q: Is there a mobile version?**  
A: Not yet. Mobile version planned for v3.0 (Q3 2026). Current version requires:
- Desktop/laptop computer
- Keyboard and mouse
- Standard display

### Features Questions

**Q: Can I customize the board colors?**  
A: Yes! Choose from 5 built-in themes:
- Settings → Theme → [choose theme]
- Or command line: `./play.sh -t ocean`

Custom themes can be added to `src/config.py`.

**Q: Can I resize the window?**  
A: Yes, the game window is resizable. Board scales automatically. Minimum size: 600×480.

**Q: How do I enable debug logging?**  
A: Launch with debug flag:
```bash
./play.sh --debug
```
Creates detailed log in `iago.log`.

**Q: Where are save files stored?**  
A: `data/` directory in installation folder:
```
data/
├── iago_game_YYYYMMDD_HHMMSS.pgn
└── reversi_game_20251119_150000.json
```

**Q: Can I analyze my games?**  
A: Yes! Two types of analysis:
1. **Real-time** - Press 'V' during game
2. **Post-game** - Press 'G' after game ends

Shows move quality, strategic factors, and suggestions.

### Strategy Questions

**Q: What's the best way to beat the AI?**  
A: Depends on difficulty:
- **Level 1-2:** Basic strategy wins
- **Level 3-4:** Control corners, avoid X-squares
- **Level 5-6:** Need strong opening knowledge, perfect endgame

Study professional games and practice!

**Q: Are corners really that important?**  
A: **YES!** Corners are the most important squares because:
- Cannot be flipped (permanent)
- Control adjacent edges
- Worth significant sacrifices
- Often decide the game

**Q: Should I always maximize the pieces I flip?**  
A: **No!** Quality over quantity:
- Better to flip fewer pieces with good position
- Than many pieces with bad position
- Think about future moves, not just current

**Q: How do I improve my play?**  
A: Practice methods:
1. **Tutorial** - Complete in-game tutorial (press 'T')
2. **Graduated AI** - Beat each level before moving up
3. **Analysis** - Review games with analysis window
4. **Study** - Read strategy guides online
5. **Practice** - Play regularly

---

## Additional Resources

### Documentation
- [README.md](../README.md) - Project overview
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [DEVELOPMENT.md](DEVELOPMENT.md) - Technical guide
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Version history

### External Resources
- [World Othello Federation](https://www.worldothello.org/)
- [Reversi Strategy Guide](https://www.worldothello.org/strategy)
- [Opening Book Database](http://www.ffothello.org/livres/beginner-cup-en.pdf)

### Community
- [GitHub Issues](https://github.com/James-HoneyBadger/Iago_Deluxe/issues) - Bug reports
- [GitHub Discussions](https://github.com/James-HoneyBadger/Iago_Deluxe/discussions) - Questions

---

## Conclusion

Thank you for playing Iago Deluxe! We hope this guide helps you enjoy the game and improve your play.

**Remember:**
- 🎯 Corners are key
- 🎲 Early piece count doesn't matter
- 🧠 Think ahead
- 💪 Practice makes perfect
- 🎮 Have fun!

**Questions or feedback?**  
Open an issue on GitHub or see [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Version:** 2.0.0  
**Last Updated:** November 19, 2025  
**Happy Gaming!** 🎮
