"""Main entry point and public API for momo-logger."""

from typing import Dict, Any, Optional
from .core import Logger
from .types import LogLevel
from .factory import backend_factory
from .backends.console import ConsoleBackend
from .backends.file import FileBackend
from .backends.buffer import BufferBackend

# Register built-in backends
backend_factory.register_backend("console", ConsoleBackend)
backend_factory.register_backend("file", FileBackend)
backend_factory.register_backend("buffer", BufferBackend)

# Global logger cache
_logger_cache: Dict[str, Logger] = {}


def get_logger(
    module: str,
    level: Optional[LogLevel] = None,
    backend: Optional[str] = None,
    formatter: Optional[str] = None,
    **backend_kwargs: Any,
) -> Logger:
    """
    Get a logger instance for the specified module.

    Args:
        module: Module name for the logger
        level: Minimum log level (defaults to INFO)
        backend: Backend identifier (defaults to console)
        formatter: Formatter identifier (defaults to text)
        **backend_kwargs: Additional arguments passed to backend constructor

    Returns:
        Logger instance
    """
    # Create cache key (include backend kwargs for uniqueness)
    cache_key = f"{module}:{level}:{backend}:{formatter}:{hash(frozenset(backend_kwargs.items()))}"

    # Return cached logger if available
    if cache_key in _logger_cache:
        return _logger_cache[cache_key]

    # Create new logger
    logger = Logger(
        module=module,
        level=level or LogLevel.INFO,
        backend=backend or "console",
        formatter=formatter or "text",
        backend_kwargs=backend_kwargs,
    )

    # Cache the logger
    _logger_cache[cache_key] = logger

    return logger


# Convenience functions for common backends
def get_console_logger(
    module: str, level: Optional[LogLevel] = None, **backend_kwargs: Any
) -> Logger:
    """Get a console logger."""
    return get_logger(module, level=level, backend="console", **backend_kwargs)


def get_file_logger(
    module: str,
    level: Optional[LogLevel] = None,
    filepath: Optional[str] = None,
    **backend_kwargs: Any,
) -> Logger:
    """Get a file logger."""
    # For file backend, we might want to customize the implementation
    if filepath:
        backend_kwargs["filepath"] = filepath
    return get_logger(module, level=level, backend="file", **backend_kwargs)


def get_buffer_logger(
    module: str, level: Optional[LogLevel] = None, **backend_kwargs: Any
) -> Logger:
    """Get a buffer logger for testing."""
    return get_logger(module, level=level, backend="buffer", **backend_kwargs)


# Re-export important types
from .types import LogLevel, LogRecord
from .base import LogBackend, LogFormatter
