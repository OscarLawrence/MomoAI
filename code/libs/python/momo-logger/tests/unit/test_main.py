"""Tests for main logger API."""

import pytest
from momo_logger.main import (
    get_logger,
    get_console_logger,
    get_file_logger,
    get_buffer_logger,
)
from momo_logger.core import Logger
from momo_logger.types import LogLevel


def test_get_logger():
    """Test get_logger function."""
    logger = get_logger("test.module")

    assert isinstance(logger, Logger)
    assert logger.module == "test.module"


def test_get_logger_with_options():
    """Test get_logger with custom options."""
    logger = get_logger(
        "test.module", level=LogLevel.DEBUG, backend="buffer", formatter="json"
    )

    assert isinstance(logger, Logger)
    assert logger.module == "test.module"
    assert logger.level == LogLevel.DEBUG
    assert logger.backend_name == "buffer"
    assert logger.formatter_name == "json"


def test_get_console_logger():
    """Test get_console_logger convenience function."""
    logger = get_console_logger("test.module")

    assert isinstance(logger, Logger)
    assert logger.module == "test.module"
    assert logger.backend_name == "console"


def test_get_console_logger_with_level():
    """Test get_console_logger with custom level."""
    logger = get_console_logger("test.module", level=LogLevel.DEBUG)

    assert isinstance(logger, Logger)
    assert logger.module == "test.module"
    assert logger.level == LogLevel.DEBUG
    assert logger.backend_name == "console"


def test_get_file_logger():
    """Test get_file_logger convenience function."""
    logger = get_file_logger("test.module")

    assert isinstance(logger, Logger)
    assert logger.module == "test.module"
    assert logger.backend_name == "file"


def test_get_buffer_logger():
    """Test get_buffer_logger convenience function."""
    logger = get_buffer_logger("test.module")

    assert isinstance(logger, Logger)
    assert logger.module == "test.module"
    assert logger.backend_name == "buffer"


def test_logger_caching():
    """Test that loggers are cached."""
    logger1 = get_logger("test.module")
    logger2 = get_logger("test.module")

    # Should be the same instance
    assert logger1 is logger2

    # Different module should create different logger
    logger3 = get_logger("test.module2")
    assert logger1 is not logger3

    # Same module with different options should create different logger
    logger4 = get_logger("test.module", level=LogLevel.DEBUG)
    assert logger1 is not logger4
