"""Console backend implementation for momo-logger."""

import sys
import asyncio
from typing import Optional
from ..base import BaseLogBackend
from ..types import LogRecord


class ConsoleBackend(BaseLogBackend):
    """Console backend that writes log records to stdout/stderr."""

    def __init__(self, stream: Optional[str] = None):
        """
        Initialize console backend.

        Args:
            stream: Output stream ("stdout", "stderr", or None for stdout)
        """
        if stream == "stderr":
            self._stream = sys.stderr
        else:
            self._stream = sys.stdout

    async def write(self, record: LogRecord) -> bool:
        """Write a log record to the console."""
        try:
            # Import here to avoid circular imports
            from ..formatters.text import TextFormatter

            formatter = TextFormatter()
            formatted = formatter.format(record)

            # Write to stream
            self._stream.write(formatted + "\n")
            self._stream.flush()

            return True
        except Exception:
            # Silently fail to avoid infinite logging loops
            return False

    async def flush(self) -> None:
        """Flush the console output."""
        self._stream.flush()

    async def close(self) -> None:
        """Close the console backend (no-op for console)."""
        pass
