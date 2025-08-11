"""
Lightweight logger adapter for momo-vector-store.

- Uses momo_logger if available.
- Falls back to Python logging with a compatible API subset.
"""
from __future__ import annotations

from typing import Any


def get_logger(name: str = "momo.vector_store"):
    """Return a logger compatible with momo_logger's interface.

    If momo_logger is installed, delegates to momo_logger.get_logger.
    Otherwise, returns a simple adapter over the stdlib logging module.
    """
    try:
        from momo_logger import get_logger as _get  # type: ignore

        return _get(name)
    except Exception:
        import logging

        class _Adapter:
            def __init__(self, name: str):
                self._logger = logging.getLogger(name)
                if not self._logger.handlers:
                    handler = logging.StreamHandler()
                    fmt = logging.Formatter(
                        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                    )
                    handler.setFormatter(fmt)
                    self._logger.addHandler(handler)
                self._logger.setLevel(logging.INFO)

            async def ai_user(self, message: str, user_facing: bool | None = None, **_: Any):
                self._logger.info(message)

            async def ai_system(self, message: str, **_: Any):
                self._logger.info(message)

            def info(self, msg: str, *args: Any, **kwargs: Any):
                self._logger.info(msg, *args, **kwargs)

            def warning(self, msg: str, *args: Any, **kwargs: Any):
                self._logger.warning(msg, *args, **kwargs)

            def error(self, msg: str, *args: Any, **kwargs: Any):
                self._logger.error(msg, *args, **kwargs)

        return _Adapter(name)
