"""Momo Logger - Structured logging for the Momo AI system."""

from .main import get_logger, get_console_logger, get_file_logger, get_buffer_logger
from .types import LogLevel, LogRecord
from .base import LogBackend, LogFormatter

# Re-export commonly used items
__all__ = [
    "get_logger",
    "get_console_logger",
    "get_file_logger",
    "get_buffer_logger",
    "LogLevel",
    "LogRecord",
    "LogBackend",
    "LogFormatter",
]
