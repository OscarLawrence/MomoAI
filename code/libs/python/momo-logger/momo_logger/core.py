"""Core logger implementation for momo-logger."""

import asyncio
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
from contextlib import asynccontextmanager
from .types import LogRecord, LogLevel
from .base import BaseLogBackend
from .factory import backend_factory
from .constants import DEFAULT_LOG_LEVEL, DEFAULT_BACKEND, DEFAULT_FORMATTER
from .levels import should_log


class Logger:
    """Core logger implementation with async support and context management."""

    def __init__(
        self,
        module: str,
        level: LogLevel = DEFAULT_LOG_LEVEL,
        backend: str = DEFAULT_BACKEND,
        formatter: str = DEFAULT_FORMATTER,
        backend_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize logger.

        Args:
            module: Module name for log records
            level: Minimum log level to process
            backend: Backend identifier
            formatter: Formatter identifier
            backend_kwargs: Additional arguments passed to backend constructor
        """
        self.module = module
        self.level = level
        self.backend_name = backend
        self.formatter_name = formatter
        self.backend_kwargs = backend_kwargs or {}
        self._backend: Optional[BaseLogBackend] = None
        self._global_context: Dict[str, Any] = {}

    async def _get_backend(self) -> BaseLogBackend:
        """Get or create backend instance."""
        if self._backend is None:
            self._backend = backend_factory.create_backend(
                self.backend_name, **self.backend_kwargs
            )
        return self._backend

    async def _log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Internal method to create and write log records."""
        # Check if we should log based on level hierarchy
        if not should_log(self.level, level):
            return

        # Separate known fields from metadata
        known_fields = {
            "timestamp",
            "level",
            "message",
            "module",
            "agent",
            "agent_role",
            "user_facing",
            "ai_optimized",
            "context",
            "metadata",
            "exception",
            "trace_id",
        }

        # Extract known fields
        log_kwargs = {}
        metadata = {}

        for key, value in kwargs.items():
            if key in known_fields:
                log_kwargs[key] = value
            else:
                metadata[key] = value

        # Merge any existing metadata with new metadata
        if "metadata" in log_kwargs:
            metadata.update(log_kwargs.pop("metadata"))

        # Add global context
        context = dict(self._global_context)
        if "context" in log_kwargs:
            context.update(log_kwargs.pop("context"))

        # Add trace ID if available
        trace_id = log_kwargs.get("trace_id")
        if not trace_id:
            # Try to get from context
            try:
                from .main import get_trace_id

                trace_id = get_trace_id()
            except ImportError:
                pass

        # Create log record
        record = LogRecord(
            timestamp=self._get_timestamp(),
            level=level,
            message=message,
            module=self.module,
            context=context,
            metadata=metadata,
            trace_id=trace_id,
            **log_kwargs,
        )

        # Write to backend
        backend = await self._get_backend()
        await backend.write(record)

    def _sync_log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Synchronous logging fallback for non-async contexts."""
        # Check if we should log based on level hierarchy
        if not should_log(self.level, level):
            return

        # Create simple log record for sync logging
        timestamp = self._get_timestamp()

        # Simple text output for sync logging
        level_str = level.value.upper()
        log_message = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {level_str} [{self.module}] {message}"

        # Print to console for sync fallback (could be enhanced to use other backends)
        print(log_message)

    def _get_timestamp(self) -> datetime:
        """Get current timestamp."""
        return datetime.now()

    # Standard logging methods
    async def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        await self._log(LogLevel.DEBUG, message, **kwargs)

    async def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        await self._log(LogLevel.INFO, message, **kwargs)

    async def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        await self._log(LogLevel.WARNING, message, **kwargs)

    async def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        await self._log(LogLevel.ERROR, message, **kwargs)

    async def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        await self._log(LogLevel.CRITICAL, message, **kwargs)

    # AI-optimized logging methods
    async def ai_system(self, message: str, **kwargs: Any) -> None:
        """Log an AI system message."""
        kwargs.setdefault("ai_optimized", True)
        await self._log(LogLevel.AI_SYSTEM, message, **kwargs)

    async def ai_user(self, message: str, **kwargs: Any) -> None:
        """Log an AI user-facing message."""
        kwargs.setdefault("ai_optimized", True)
        kwargs.setdefault("user_facing", True)
        await self._log(LogLevel.AI_USER, message, **kwargs)

    async def ai_agent(self, message: str, **kwargs: Any) -> None:
        """Log an AI agent communication message."""
        kwargs.setdefault("ai_optimized", True)
        await self._log(LogLevel.AI_AGENT, message, **kwargs)

    async def ai_debug(self, message: str, **kwargs: Any) -> None:
        """Log an AI debug message."""
        kwargs.setdefault("ai_optimized", True)
        await self._log(LogLevel.AI_DEBUG, message, **kwargs)

    # Role-specific logging methods
    async def tester(self, message: str, **kwargs: Any) -> None:
        """Log a tester-specific message."""
        kwargs.setdefault("agent_role", "tester")
        await self._log(LogLevel.TESTER, message, **kwargs)

    async def developer(self, message: str, **kwargs: Any) -> None:
        """Log a developer-specific message."""
        kwargs.setdefault("agent_role", "developer")
        await self._log(LogLevel.DEVELOPER, message, **kwargs)

    async def architect(self, message: str, **kwargs: Any) -> None:
        """Log an architect-specific message."""
        kwargs.setdefault("agent_role", "architect")
        await self._log(LogLevel.ARCHITECT, message, **kwargs)

    async def operator(self, message: str, **kwargs: Any) -> None:
        """Log an operator-specific message."""
        kwargs.setdefault("agent_role", "operator")
        await self._log(LogLevel.OPERATOR, message, **kwargs)

    @asynccontextmanager
    async def context(self, **context: Any) -> AsyncIterator["Logger"]:
        """Context manager for adding context to log records."""
        # Save previous context
        previous_context = dict(self._global_context)

        # Update context
        self._global_context.update(context)

        try:
            yield self
        finally:
            # Restore previous context
            self._global_context = previous_context

    async def flush(self) -> None:
        """Flush the backend."""
        if self._backend:
            await self._backend.flush()

    async def close(self) -> None:
        """Close the logger and backend."""
        if self._backend:
            await self._backend.close()
