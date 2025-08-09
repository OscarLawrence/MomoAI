"""Text formatter for momo-logger."""

from datetime import datetime
from ..base import BaseLogFormatter
from ..types import LogRecord, LogLevel


class TextFormatter(BaseLogFormatter):
    """Text formatter that outputs human-readable log records."""

    def format(self, record: LogRecord) -> str:
        """Format a log record as human-readable text."""
        # Format timestamp
        timestamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Format level (pad to 8 characters)
        level = record.level.value.upper().ljust(8)

        # Format module
        module = record.module

        # Format agent info if present
        agent_info = f"[{record.agent}]" if record.agent else ""

        # Format user-facing messages differently
        if record.user_facing:
            # Simplified format for user-facing messages
            message = record.message
            if record.level == LogLevel.WARNING:
                return f"⚠️  {message}"
            elif record.level == LogLevel.ERROR:
                return f"❌ {message}"
            elif record.level == LogLevel.CRITICAL:
                return f"💥 {message}"
            else:
                return f"✅ {message}"

        # Standard format for system messages
        context_parts = []
        if record.context:
            context_str = ", ".join([f"{k}={v}" for k, v in record.context.items()])
            context_parts.append(context_str)

        if record.metadata:
            metadata_str = ", ".join([f"{k}={v}" for k, v in record.metadata.items()])
            context_parts.append(metadata_str)

        context = f" ({'; '.join(context_parts)})" if context_parts else ""

        # Format exception if present
        exception = f"\nException: {record.exception}" if record.exception else ""

        return f"[{timestamp}] {level} [{module}] {agent_info} {record.message}{context}{exception}"
