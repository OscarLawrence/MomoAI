"""Basic tests for momo-logger."""

import pytest
import asyncio
from src.momo_logger import get_logger, LogLevel
from src.momo_logger.backends.buffer import BufferBackend


def test_logger_creation():
    """Test that logger can be created."""
    logger = get_logger("test.module")
    assert logger is not None
    assert logger.module == "test.module"


def test_buffer_logger():
    """Test buffer logger functionality."""
    logger = get_logger("test.module", backend="buffer")
    assert logger is not None

    # Check that backend is BufferBackend
    # Note: This test would need to be async to properly initialize the backend


@pytest.mark.asyncio
async def test_basic_logging():
    """Test basic logging functionality."""
    logger = get_logger("test.module", backend="buffer")

    # Log a message
    await logger.info("Test message", test_key="test_value")

    # Get the backend to check recorded messages
    # This would require access to the backend instance


def test_log_levels():
    """Test that all log levels are defined."""
    # Test standard levels
    assert LogLevel.DEBUG is not None
    assert LogLevel.INFO is not None
    assert LogLevel.WARNING is not None
    assert LogLevel.ERROR is not None
    assert LogLevel.CRITICAL is not None

    # Test AI levels
    assert LogLevel.AI_SYSTEM is not None
    assert LogLevel.AI_USER is not None
    assert LogLevel.AI_AGENT is not None
    assert LogLevel.AI_DEBUG is not None

    # Test role-specific levels
    assert LogLevel.TESTER is not None
    assert LogLevel.DEVELOPER is not None
    assert LogLevel.ARCHITECT is not None
    assert LogLevel.OPERATOR is not None
