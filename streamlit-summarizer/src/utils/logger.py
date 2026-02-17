"""
Logging utility for the Streamlit application.

Configures Python logging to write to the logs directory with proper formatting,
rotation, and different log levels.
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Creates log files in the specified directory with rotation based on file size.
    Logs are written to both file and console (for Streamlit).
    
    Args:
        log_dir: Directory to store log files (default: "logs")
        log_level: Logging level (default: INFO)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    log_filename = log_path / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error log file handler (separate file for errors)
    error_log_filename = log_path / f"error_{datetime.now().strftime('%Y-%m-%d')}.log"
    error_handler = RotatingFileHandler(
        error_log_filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Console handler (for Streamlit output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors in console
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ of the calling module).
              If None, returns the root logger.
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name) if name else logging.getLogger()
