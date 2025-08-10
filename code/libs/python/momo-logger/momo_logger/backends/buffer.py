"""Buffer backend implementation for momo-logger."""

from typing import List
from ..base import BaseLogBackend
from ..types import LogRecord


class BufferBackend(BaseLogBackend):
    """Buffer backend that stores log records in memory for testing."""

    def __init__(self) -> None:
        """Initialize buffer backend."""
        self._records: List[LogRecord] = []

    async def write(self, record: LogRecord) -> bool:
        """Write a log record to the buffer."""
        try:
            self._records.append(record)
            return True
        except Exception:
            return False

    async def flush(self) -> None:
        """Flush the buffer (no-op)."""
        pass

    async def close(self) -> None:
        """Close the buffer backend (clear records)."""
        self._records.clear()

    @property
    def records(self) -> List[LogRecord]:
        """Get all recorded log records."""
        return self._records.copy()

    def clear(self) -> None:
        """Clear all recorded log records."""
        self._records.clear()
