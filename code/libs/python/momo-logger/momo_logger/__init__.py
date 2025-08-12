"""Momo Logger - Structured logging for the Momo AI system."""

from .main import (
    get_logger,
    get_console_logger,
    get_file_logger,
    get_buffer_logger,
    generate_trace_id,
    set_trace_id,
    get_trace_id,
    with_trace_id,
)
from .types import LogLevel, LogRecord
from .base import LogBackend, LogFormatter

# Re-export commonly used items
__all__ = [
    "get_logger",
    "get_console_logger",
    "get_file_logger",
    "get_buffer_logger",
    "generate_trace_id",
    "set_trace_id",
    "get_trace_id",
    "with_trace_id",
    "LogLevel",
    "LogRecord",
    "LogBackend",
    "LogFormatter",
]
