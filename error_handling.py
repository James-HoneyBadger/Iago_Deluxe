#!/usr/bin/env python3
"""
Error handling utilities for Reversi Deluxe
Provides custom exceptions and error handling helpers
"""
from typing import Optional, Any, Callable
from functools import wraps
import json

from logger import get_logger

logger = get_logger(__name__)


# Custom Exceptions
class ReversiError(Exception):
    """Base exception for Reversi game errors"""

    pass


class InvalidMoveError(ReversiError):
    """Raised when an invalid move is attempted"""

    pass


class InvalidBoardStateError(ReversiError):
    """Raised when board state is corrupted or invalid"""

    pass


class SaveFileError(ReversiError):
    """Raised when save file operations fail"""

    pass


class ConfigurationError(ReversiError):
    """Raised when configuration is invalid"""

    pass


# Error handling decorators
def handle_file_errors(
    default_return: Any = None, error_message: str = "File operation failed"
):
    """
    Decorator to handle file operation errors gracefully

    Args:
        default_return: Value to return on error
        error_message: Custom error message to log
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                logger.error(f"{error_message} - File not found: {e}")
                return default_return
            except PermissionError as e:
                logger.error(f"{error_message} - Permission denied: {e}")
                return default_return
            except json.JSONDecodeError as e:
                logger.error(f"{error_message} - Invalid JSON: {e}")
                return default_return
            except OSError as e:
                logger.error(f"{error_message} - OS error: {e}")
                return default_return
            except Exception as e:
                logger.error(f"{error_message} - Unexpected error: {e}", exc_info=True)
                return default_return

        return wrapper

    return decorator


def safe_execute(
    func: Callable, *args, default: Any = None, error_msg: str = "", **kwargs
) -> Any:
    """
    Safely execute a function with error handling

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default: Default value to return on error
        error_msg: Custom error message
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        msg = error_msg or f"Error executing {func.__name__}"
        logger.error(f"{msg}: {e}", exc_info=True)
        return default


def validate_board_size(size: int) -> bool:
    """
    Validate board size

    Args:
        size: Board size to validate

    Returns:
        True if valid, False otherwise
    """
    from config import game_config

    if not isinstance(size, int):
        logger.warning(f"Board size must be integer, got {type(size)}")
        return False

    if size < game_config.MIN_BOARD_SIZE or size > game_config.MAX_BOARD_SIZE:
        logger.warning(
            f"Board size {size} outside valid range [{game_config.MIN_BOARD_SIZE}, {game_config.MAX_BOARD_SIZE}]"
        )
        return False

    if size % 2 != 0:
        logger.warning(f"Board size {size} must be even")
        return False

    return True


def validate_save_file(data: dict) -> bool:
    """
    Validate save file structure

    Args:
        data: Deserialized save file data

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["grid", "size", "to_move"]

    for field in required_fields:
        if field not in data:
            logger.error(f"Save file missing required field: {field}")
            return False

    # Validate grid structure
    grid = data.get("grid", [])
    size = data.get("size", 0)

    if not isinstance(grid, list):
        logger.error("Grid must be a list")
        return False

    if len(grid) != size:
        logger.error(f"Grid height {len(grid)} doesn't match size {size}")
        return False

    for i, row in enumerate(grid):
        if not isinstance(row, list):
            logger.error(f"Grid row {i} is not a list")
            return False
        if len(row) != size:
            logger.error(f"Grid row {i} length {len(row)} doesn't match size {size}")
            return False
        for j, cell in enumerate(row):
            if cell not in [0, 1, 2]:
                logger.error(f"Invalid cell value at ({i},{j}): {cell}")
                return False

    # Validate to_move
    if data.get("to_move") not in [1, 2]:
        logger.error(f"Invalid to_move value: {data.get('to_move')}")
        return False

    return True


def validate_ai_depth(depth: int) -> bool:
    """
    Validate AI depth setting

    Args:
        depth: AI search depth

    Returns:
        True if valid, False otherwise
    """
    from config import game_config

    if not isinstance(depth, int):
        logger.warning(f"AI depth must be integer, got {type(depth)}")
        return False

    if depth < game_config.MIN_AI_DEPTH or depth > game_config.MAX_AI_DEPTH:
        logger.warning(
            f"AI depth {depth} outside valid range [{game_config.MIN_AI_DEPTH}, {game_config.MAX_AI_DEPTH}]"
        )
        return False

    return True


def validate_theme(theme: str) -> bool:
    """
    Validate theme name

    Args:
        theme: Theme name

    Returns:
        True if valid, False otherwise
    """
    from config import THEMES

    if theme not in THEMES:
        logger.warning(f"Unknown theme: {theme}. Available: {list(THEMES.keys())}")
        return False

    return True


class ErrorContext:
    """Context manager for structured error handling"""

    def __init__(self, operation: str, reraise: bool = False):
        """
        Args:
            operation: Description of the operation being performed
            reraise: If True, re-raise the exception after logging
        """
        self.operation = operation
        self.reraise = reraise
        self.logger = get_logger("ErrorContext")

    def __enter__(self):
        self.logger.debug(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Failed: {self.operation} - {exc_val}", exc_info=True)
            return not self.reraise
        else:
            self.logger.debug(f"Completed: {self.operation}")
        return False
