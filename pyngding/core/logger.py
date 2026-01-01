"""Centralized logging configuration for pyngding.

This module provides a configured logger instance for the entire application.
All modules should import and use the logger from here rather than using print().
"""
import logging
import sys

# Create the main logger for the application
logger = logging.getLogger('pyngding')

# Default configuration (can be overridden by calling configure_logging)
_configured = False


def configure_logging(level: int = logging.INFO, format_style: str = 'simple') -> None:
    """Configure the pyngding logger.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format_style: 'simple' for basic output, 'detailed' for timestamps and levels
    """
    global _configured
    
    if _configured:
        return
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stderr)
    
    # Create formatter based on style
    if format_style == 'detailed':
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Simple format for normal operation
        formatter = logging.Formatter('%(message)s')
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    
    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Optional sub-logger name (e.g., 'scheduler', 'adguard')
              If None, returns the main pyngding logger.
    
    Returns:
        A configured Logger instance.
    """
    # Ensure logging is configured with defaults if not already
    if not _configured:
        configure_logging()
    
    if name:
        return logger.getChild(name)
    return logger

