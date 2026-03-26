"""
Unicode-Safe Logging Configuration for Windows

This module provides a centralized logging configuration that properly handles
Unicode characters (emojis) on Windows systems to prevent encoding errors.
"""

import sys
import os
import logging
from pathlib import Path


class UnicodeConsoleHandler(logging.StreamHandler):
    """Custom console handler that safely handles Unicode characters on Windows"""
    
    def __init__(self):
        super().__init__(sys.stdout)
        self.setLevel(logging.INFO)
        
    def emit(self, record):
        """Emit a log record with Unicode safety"""
        try:
            msg = self.format(record)
            # Try to encode with UTF-8 first
            try:
                self.stream.write(msg + self.terminator)
                self.flush()
            except UnicodeEncodeError:
                # Fallback: replace Unicode characters with safe equivalents
                safe_msg = self._make_unicode_safe(msg)
                self.stream.write(safe_msg + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)
    
    def _make_unicode_safe(self, text):
        """Replace Unicode emojis with ASCII equivalents"""
        emoji_replacements = {
            '🚀': '[ROCKET]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '📊': '[CHART]',
            '🎯': '[TARGET]',
            '📁': '[FOLDER]',
            '💾': '[SAVE]',
            '📱': '[PHONE]',
            '🤝': '[HANDSHAKE]',
            '👔': '[SHIRT]',
            '🏢': '[BUILDING]',
            '📄': '[FILE]',
            '⚠️': '[WARNING]',
            '📅': '[CALENDAR]',
            '🗓️': '[CALENDAR]',
            '🌍': '[GLOBE]',
            '💪': '[MUSCLE]',
            'ℹ️': '[INFO]',
            '🎉': '[PARTY]',
            '🔧': '[WRENCH]',
            '🔍': '[SEARCH]',
            '📋': '[CLIPBOARD]',
            '📈': '[TRENDING_UP]',
            '🏭': '[FACTORY]',
            '💼': '[BRIEFCASE]',
            '🔗': '[LINK]',
            '🌟': '[STAR]',
            '🎨': '[ART]',
            '🛠️': '[TOOLS]',
            '⭐': '[STAR]',
            '🎪': '[CIRCUS]',
            '🔥': '[FIRE]',
            '💡': '[BULB]',
            '🎭': '[THEATER]'
        }
        
        safe_text = text
        for emoji, replacement in emoji_replacements.items():
            safe_text = safe_text.replace(emoji, replacement)
        
        # Fallback: encode with errors='replace' to handle any remaining Unicode
        safe_text = safe_text.encode('ascii', errors='replace').decode('ascii')
        return safe_text


class UnicodeFileHandler(logging.FileHandler):
    """Custom file handler that properly handles Unicode in log files"""
    
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        # Ensure log directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, mode, encoding, delay)


def configure_unicode_logging(
    name: str = None,
    level: int = logging.INFO,
    log_file: str = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Configure Unicode-safe logging for a module
    
    Args:
        name: Logger name (defaults to calling module)
        level: Logging level
        log_file: Log file path (optional)
        console_output: Whether to log to console
        file_output: Whether to log to file
        
    Returns:
        Configured logger instance
    """
    
    # Get logger name
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler if requested
    if console_output:
        console_handler = UnicodeConsoleHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_output:
        if log_file is None:
            # Default log file location
            log_file = f"logs/{name.replace('.', '_')}.log"
        
        file_handler = UnicodeFileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_system_wide_unicode_logging():
    """
    Set up Unicode-safe logging for the entire LinkedIn intelligence system
    """
    
    # Set Windows console to UTF-8 if possible
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul')
        except:
            pass
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    # Add Unicode-safe handlers to root logger
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = UnicodeConsoleHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for system-wide logs
    file_handler = UnicodeFileHandler('logs/system_wide.log')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return root_logger


# Convenience function for quick logger setup
def get_unicode_logger(name: str, log_file: str = None) -> logging.Logger:
    """Get a Unicode-safe logger for a module"""
    return configure_unicode_logging(
        name=name,
        log_file=log_file,
        console_output=True,
        file_output=True
    )


# Example usage
if __name__ == "__main__":
    # Test the Unicode logging
    logger = get_unicode_logger("test_unicode_logging")
    
    logger.info("🚀 Testing Unicode logging system")
    logger.info("✅ This should work without errors")
    logger.info("📊 Charts and graphs: 📈📉")
    logger.info("🎯 Emojis should display properly or be replaced safely")
    logger.info("🌟 System ready for production!")