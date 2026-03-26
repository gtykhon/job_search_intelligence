"""
Enhanced Logging Configuration with Emoji Support
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(level: str = "INFO") -> None:
    """
    Setup basic logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Basic configuration
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / f"job_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )

def create_emoji_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Create an enhanced logger with emoji support and structured formatting
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler
    log_file = log_dir / f'job_search_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Enhanced formatter with emoji support
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class EmojiFilter(logging.Filter):
    """Filter to add emoji prefixes to log levels"""
    
    EMOJI_MAP = {
        'DEBUG': '🐛',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def filter(self, record):
        emoji = self.EMOJI_MAP.get(record.levelname, '')
        if emoji:
            record.msg = f"{emoji} {record.msg}"
        return True
