"""Backend factory system for dynamic backend loading."""

from typing import Dict, Type, Union, Any
from .types import LogLevel
from .base import BaseLogBackend
from .constants import DEFAULT_LOG_LEVEL


class BackendFactory:
    """Factory for creating backend instances from string identifiers."""

    def __init__(self) -> None:
        self._backends: Dict[str, Type[BaseLogBackend]] = {}
        self._register_builtin_backends()

    def _register_builtin_backends(self) -> None:
        """Register built-in backend implementations."""
        # Import here to avoid circular imports
        from .backends.console import ConsoleBackend
        from .backends.file import FileBackend
        from .backends.buffer import BufferBackend

        # Register built-in backends
        self._backends = {
            "console": ConsoleBackend,
            "file": FileBackend,
            "buffer": BufferBackend,
        }

    def create_backend(
        self, backend: Union[str, BaseLogBackend], *args: Any, **kwargs: Any
    ) -> BaseLogBackend:
        """Create a backend from string identifier or return existing instance."""
        if isinstance(backend, str):
            if backend not in self._backends:
                available = list(self._backends.keys())
                raise ValueError(f"Unknown backend '{backend}'. Available: {available}")

            backend_class = self._backends[backend]
            return backend_class(*args, **kwargs)

        # Already an instance, return as-is
        if isinstance(backend, BaseLogBackend):
            return backend
        raise ValueError(f"Invalid backend type: {type(backend)}")

    def register_backend(self, name: str, backend_class: Type[BaseLogBackend]) -> None:
        """Register a new backend implementation."""
        self._backends[name] = backend_class


# Global factory instance
backend_factory = BackendFactory()
