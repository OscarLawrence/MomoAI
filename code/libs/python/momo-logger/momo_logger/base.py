"""Protocol definitions and base classes for the momo-logger module."""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any
from .types import LogRecord, LogLevel


class LogBackend(Protocol):
    """Protocol for log backends."""

    async def write(self, record: LogRecord) -> bool:
        """Write a log record to the backend."""
        ...

    async def flush(self) -> None:
        """Flush any buffered log records."""
        ...

    async def close(self) -> None:
        """Close the backend connection."""
        ...


class BaseLogBackend(ABC):
    """Abstract base class for log backends."""

    @abstractmethod
    async def write(self, record: LogRecord) -> bool:
        """Write a log record to the backend."""
        pass

    @abstractmethod
    async def flush(self) -> None:
        """Flush any buffered log records."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the backend connection."""
        pass


class LogFormatter(Protocol):
    """Protocol for log formatters."""

    def format(self, record: LogRecord) -> str:
        """Format a log record for output."""
        ...


class BaseLogFormatter(ABC):
    """Abstract base class for log formatters."""

    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """Format a log record for output."""
        pass
