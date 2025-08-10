"""File backend implementation for momo-logger."""

import os
import asyncio
from typing import Optional
from datetime import datetime
from ..base import BaseLogBackend
from ..types import LogRecord
from ..constants import DEFAULT_LOG_FILE, DEFAULT_LOG_DIR


class FileBackend(BaseLogBackend):
    """File backend that writes log records to a file."""

    def __init__(self, filepath: Optional[str] = None, directory: Optional[str] = None):
        """
        Initialize file backend.

        Args:
            filepath: Path to log file (overrides directory)
            directory: Directory to store log files
        """
        if filepath:
            self._filepath = filepath
        else:
            log_dir = directory or DEFAULT_LOG_DIR
            log_file = DEFAULT_LOG_FILE
            self._filepath = os.path.join(log_dir, log_file)

        # Ensure directory exists
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)

        # Open file for appending
        self._file = open(self._filepath, "a", encoding="utf-8")

    async def write(self, record: LogRecord) -> bool:
        """Write a log record to the file."""
        try:
            # Import here to avoid circular imports
            from ..formatters.json import JSONFormatter

            formatter = JSONFormatter()
            formatted = formatter.format(record)

            # Write to file
            self._file.write(formatted + "\n")
            self._file.flush()

            return True
        except Exception:
            # Silently fail to avoid infinite logging loops
            return False

    async def flush(self) -> None:
        """Flush the file output."""
        if self._file and not self._file.closed:
            self._file.flush()

    async def close(self) -> None:
        """Close the file backend."""
        if self._file and not self._file.closed:
            self._file.close()
