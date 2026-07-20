"""Logging configuration for Setlistify.

Sets up structured logging to files and console.
"""

import logging
import logging.handlers
from pathlib import Path

from .config import Config


def setup_logging() -> None:
    """Configure logging for the application.

    Sets up:
    - Console logging at INFO level
    - File logging with rotation for INFO, WARNING, and ERROR
    """
    Config.ensure_directories()

    # Create logger
    logger = logging.getLogger("setlistify")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handlers with rotation
    log_dir = Config.LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # Info log
    info_handler = logging.handlers.RotatingFileHandler(
        log_dir / "info.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

    # Warning log
    warning_handler = logging.handlers.RotatingFileHandler(
        log_dir / "warnings.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)
    logger.addHandler(warning_handler)

    # Error log
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Name of the logger (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"setlistify.{name}")
