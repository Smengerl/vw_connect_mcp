"""Centralized logging configuration.

Supports:
- Multiple log levels
- Environment variables
- Output to stderr and/or file
"""

import logging
import os
import sys
from typing import Optional

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logging(
    name: Optional[str] = None,
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
) -> logging.Logger:
    """Setup logging for the application.
    
    Args:
        name: Logger name (typically __name__). If None, returns root logger
        level: Log level. If None, uses default
        log_file: Log file path. If None, logs to stderr only
        format_string: Custom format. If None, uses default
        date_format: Custom date format. If None, uses default
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name) if name else logging.getLogger()
    
    if logger.handlers:
        return logger
    
    if level is None:
        level = DEFAULT_LOG_LEVEL
    logger.setLevel(level)
    
    fmt = format_string or DEFAULT_LOG_FORMAT
    datefmt = date_format or DEFAULT_DATE_FORMAT
    formatter = logging.Formatter(fmt, datefmt=datefmt)
    
    # Console handler (stderr for MCP compatibility)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning("Failed to setup file logging to %s: %s", log_file, e)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger
    """
    return setup_logging(name)
