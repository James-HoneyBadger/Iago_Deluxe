#!/usr/bin/env python3
"""
Logging utility for Reversi Deluxe
Provides centralized logging configuration with file and console handlers
"""
import logging
import logging.handlers
import sys
from typing import Optional

from src.config import file_config, log_config


class GameLogger:
    """Centralized logging configuration for the game"""

    _initialized = False
    _loggers = {}

    @classmethod
    def setup_logging(cls, debug: bool = False, log_file: Optional[str] = None):
        """
        Initialize the logging system

        Args:
            debug: If True, set console logging to DEBUG level
            log_file: Optional custom log file path
        """
        if cls._initialized:
            return

        # Determine log file path
        if log_file is None:
            log_file = file_config.LOG_FILE

        # Create formatters
        formatter = logging.Formatter(
            log_config.LOG_FORMAT, datefmt=log_config.LOG_DATE_FORMAT
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = (
            logging.DEBUG if debug else getattr(logging, log_config.LOG_LEVEL_CONSOLE)
        )
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)

        # File handler with rotation
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=log_config.MAX_LOG_SIZE_MB * 1024 * 1024,
                backupCount=log_config.LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, log_config.LOG_LEVEL_FILE))
            file_handler.setFormatter(formatter)
            file_handler_available = True
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create log file: {e}", file=sys.stderr)
            file_handler_available = False

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        if file_handler_available:
            root_logger.addHandler(file_handler)

        cls._initialized = True

        # Log initial message
        logger = cls.get_logger("GameLogger")
        logger.info("=" * 60)
        logger.info("Reversi Deluxe - Logging system initialized")
        logger.info(
            f"Console level: {console_level}, "
            f"File level: {log_config.LOG_LEVEL_FILE}"
        )
        logger.info("=" * 60)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module

        Args:
            name: Name of the logger (typically __name__ of the module)

        Returns:
            Configured logger instance
        """
        if not cls._initialized:
            cls.setup_logging()

        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)

        return cls._loggers[name]

    @classmethod
    def set_level(cls, level: str):
        """
        Change the logging level for all loggers

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        for logger in cls._loggers.values():
            logger.setLevel(log_level)
        logging.getLogger().setLevel(log_level)


# Convenience function
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance - convenience wrapper"""
    return GameLogger.get_logger(name)


# Performance logging decorator
def log_performance(func):
    """Decorator to log function execution time"""
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} completed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} failed after {elapsed:.2f}ms: {e}")
            raise

    return wrapper


# Exception logging context manager
class log_exceptions:
    """Context manager for logging exceptions"""

    def __init__(self, logger: logging.Logger, message: str = "Exception occurred"):
        self.logger = logger
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"{self.message}: {exc_val}", exc_info=True)
        return False  # Don't suppress the exception
