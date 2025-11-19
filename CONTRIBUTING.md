# Contributing to HB_Reversi

Thank you for your interest in contributing to HB_Reversi! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- Basic understanding of Pygame and object-oriented programming

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/HB_Reversi.git
   cd HB_Reversi
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/James-HoneyBadger/HB_Reversi.git
   ```

## 🛠️ Development Setup

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Verify installation:**
   ```bash
   python3 main.py
   ```

## ✏️ Making Changes

### Branch Strategy

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

   Branch naming conventions:
   - `feature/` - New features
   - `bugfix/` - Bug fixes
   - `docs/` - Documentation updates
   - `refactor/` - Code refactoring
   - `test/` - Test additions or modifications

2. **Keep your branch updated:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Making Commits

Write clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "Add corner strategy to AI evaluation"
git commit -m "Fix bug in undo/redo move history"
git commit -m "Update README with new command-line options"

# Poor commit messages (avoid these)
git commit -m "Fixed stuff"
git commit -m "Update"
git commit -m "asdf"
```

**Commit message format:**
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues/PRs when relevant (#123)

## 🎨 Code Style

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line length:** 88 characters (Black formatter standard)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings
- **Naming conventions:**
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### Linting

Run Flake8 before committing:

```bash
# Check code style
python3 -m flake8 src/ tests/

# Auto-format with Black (optional)
python3 -m black src/ tests/
```

Our `.flake8` configuration:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git, __pycache__, .venv, build, dist
```

### Code Organization

- **Import order:**
  1. Standard library imports
  2. Third-party imports
  3. Local application imports

  ```python
  # Standard library
  import os
  import sys
  from typing import List, Optional
  
  # Third-party
  import pygame
  
  # Local
  from src.config import GameConfig
  from src.logger import get_logger
  ```

- **Type hints:** Use type hints for function parameters and return values
  ```python
  def calculate_score(board: List[List[int]]) -> tuple[int, int]:
      """Calculate black and white scores."""
      pass
  ```

- **Docstrings:** Use docstrings for classes and public methods
  ```python
  def legal_moves(self, player: int) -> list[tuple[int, int]]:
      """
      Find all legal moves for the given player.
      
      Args:
          player: Player color (1 for black, 2 for white)
          
      Returns:
          List of (row, col) tuples representing legal moves
      """
      pass
  ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python3 tests/run_tests.py

# Run specific test file
python3 -m pytest tests/test_board.py -v

# Run with coverage
python3 -m pytest --cov=src --cov-report=html tests/

# View coverage report
# Open htmlcov/index.html in browser
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names

Example:
```python
import pytest
from src.Reversi import Board

def test_initial_board_setup():
    """Test that board initializes with correct starting position."""
    board = Board(size=8)
    assert board.grid[3][3] == 2  # White
    assert board.grid[3][4] == 1  # Black
    assert board.grid[4][3] == 1  # Black
    assert board.grid[4][4] == 2  # White

def test_legal_moves_initial_position():
    """Test legal moves from starting position."""
    board = Board(size=8)
    moves = board.legal_moves(player=1)
    expected = [(2, 3), (3, 2), (4, 5), (5, 4)]
    assert sorted(moves) == sorted(expected)
```

### Test Coverage Goals

- Aim for **80%+ code coverage**
- All new features must include tests
- Bug fixes should include regression tests

## 📤 Submitting Changes

### Pull Request Process

1. **Ensure all tests pass:**
   ```bash
   python3 tests/run_tests.py
   python3 -m flake8 src/ tests/
   ```

2. **Update documentation:**
   - Update relevant `.md` files
   - Add docstrings to new functions/classes
   - Update QUICK_REFERENCE.md for new features

3. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request:**
   - Go to GitHub and create a PR from your fork
   - Use a clear, descriptive title
   - Fill out the PR template
   - Link related issues

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

## 🐛 Reporting Bugs

### Before Submitting

1. Check existing issues for duplicates
2. Verify it's actually a bug
3. Collect necessary information

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what the bug is

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11]
- Pygame version: [e.g., 2.5.2]

**Additional context**
Any other relevant information
```

## 💡 Suggesting Enhancements

### Enhancement Request Template

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why this feature would be useful

**Proposed Implementation**
How you think it could be implemented (optional)

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other relevant information
```

## 📝 Documentation

### Documentation Standards

- Use **Markdown** for all documentation
- Keep line length reasonable (80-100 characters)
- Use code blocks with language specifiers
- Include examples where helpful

### Documentation Locations

- **README.md** - Project overview and quick start
- **docs/DEVELOPMENT.md** - Architecture and technical details
- **docs/QUICK_REFERENCE.md** - Commands and shortcuts
- **Code comments** - Inline documentation for complex logic
- **Docstrings** - Function/class documentation

## 🔍 Code Review Process

### What Reviewers Look For

- Code correctness and functionality
- Test coverage
- Code style compliance
- Documentation completeness
- Performance considerations
- Security implications

### Addressing Review Comments

- Respond to all comments
- Make requested changes or discuss alternatives
- Push updates to the same branch
- Mark conversations as resolved when addressed

## 🎯 Priority Areas

Current areas where contributions are especially welcome:

1. **Test Coverage** - Expanding test suite
2. **AI Improvements** - Better evaluation functions
3. **Performance** - Optimization opportunities
4. **Documentation** - Examples, tutorials, guides
5. **Themes** - New visual themes
6. **Accessibility** - Keyboard navigation, screen readers

## 💬 Questions?

- Open a GitHub Discussion for questions
- Comment on relevant issues
- Reach out to maintainers

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!

---

**Happy Coding!** 🎮
