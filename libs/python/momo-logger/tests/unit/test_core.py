"""Tests for core logger functionality."""

import pytest
import asyncio
from datetime import datetime
from momo_logger.core import Logger
from momo_logger.types import LogLevel
from momo_logger.backends.buffer import BufferBackend


@pytest.mark.asyncio
async def test_logger_creation():
    """Test logger creation and initialization."""
    logger = Logger(
        module="test.module", level=LogLevel.INFO, backend="buffer", formatter="json"
    )

    assert logger.module == "test.module"
    assert logger.level == LogLevel.INFO
    assert logger.backend_name == "buffer"
    assert logger.formatter_name == "json"
    assert logger._global_context == {}


@pytest.mark.asyncio
async def test_basic_logging():
    """Test basic logging functionality."""
    logger = Logger(module="test.module", level=LogLevel.DEBUG, backend="buffer")

    # Log a message
    await logger.info("Test message", test_key="test_value")

    # Get the backend to check recorded messages
    backend = await logger._get_backend()
    assert isinstance(backend, BufferBackend)

    # Check that message was recorded
    assert len(backend.records) == 1
    record = backend.records[0]
    assert record.message == "Test message"
    assert record.module == "test.module"
    assert record.level == LogLevel.INFO
    assert record.metadata.get("test_key") == "test_value"


@pytest.mark.asyncio
async def test_log_level_filtering():
    """Test that log levels are properly filtered."""
    logger = Logger(
        module="test.module",
        level=LogLevel.WARNING,  # Only log warnings and above
        backend="buffer",
    )

    # Try to log info (should be filtered out)
    await logger.info("Info message")

    # Log warning (should be logged)
    await logger.warning("Warning message")

    # Log error (should be logged)
    await logger.error("Error message")

    # Get the backend to check recorded messages
    backend = await logger._get_backend()

    # Should only have 2 messages (warning and error)
    assert len(backend.records) == 2
    assert backend.records[0].level == LogLevel.WARNING
    assert backend.records[1].level == LogLevel.ERROR


@pytest.mark.asyncio
async def test_ai_logging():
    """Test AI-specific logging methods."""
    logger = Logger(module="test.module", level=LogLevel.DEBUG, backend="buffer")

    # Test AI system logging
    await logger.ai_system("Agent selection completed", agent="momo_agent")

    # Test AI user logging
    await logger.ai_user("User-facing message", user_facing=True)

    # Test AI agent logging
    await logger.ai_agent("Agent communication", target_agent="worker")

    # Test AI debug logging
    await logger.ai_debug("AI debug info", debug_data={"key": "value"})

    # Get the backend to check recorded messages
    backend = await logger._get_backend()
    assert len(backend.records) == 4

    # Check first record
    record1 = backend.records[0]
    assert record1.level == LogLevel.AI_SYSTEM
    assert record1.message == "Agent selection completed"
    assert record1.agent == "momo_agent"
    assert record1.ai_optimized is True

    # Check second record
    record2 = backend.records[1]
    assert record2.level == LogLevel.AI_USER
    assert record2.message == "User-facing message"
    assert record2.user_facing is True
    assert record2.ai_optimized is True


@pytest.mark.asyncio
async def test_role_specific_logging():
    """Test role-specific logging methods."""
    logger = Logger(module="test.module", level=LogLevel.DEBUG, backend="buffer")

    # Test tester logging
    await logger.tester("Test case passed", test_name="test_1")

    # Test developer logging
    await logger.developer("Feature implemented", feature="logging")

    # Test architect logging
    await logger.architect("Module refactored", module_count=3)

    # Test operator logging
    await logger.operator("System operational", status="ok")

    # Get the backend to check recorded messages
    backend = await logger._get_backend()
    assert len(backend.records) == 4

    # Check tester record
    tester_record = backend.records[0]
    assert tester_record.level == LogLevel.TESTER
    assert tester_record.agent_role == "tester"
    assert tester_record.metadata.get("test_name") == "test_1"

    # Check developer record
    dev_record = backend.records[1]
    assert dev_record.level == LogLevel.DEVELOPER
    assert dev_record.agent_role == "developer"
    assert dev_record.metadata.get("feature") == "logging"


@pytest.mark.asyncio
async def test_context_management():
    """Test context management functionality."""
    logger = Logger(module="test.module", level=LogLevel.DEBUG, backend="buffer")

    # Log without context
    await logger.info("No context message")

    # Log with context manager
    async with logger.context(user_id="123", session_id="abc"):
        await logger.info("Context message 1")
        await logger.debug("Context message 2", extra_data="value")

    # Log without context again
    await logger.warning("No context message 2")

    # Get the backend to check recorded messages
    backend = await logger._get_backend()
    assert len(backend.records) == 4

    # First record should have no context
    record1 = backend.records[0]
    assert record1.message == "No context message"
    assert record1.context == {}

    # Second record should have context
    record2 = backend.records[1]
    assert record2.message == "Context message 1"
    assert record2.context.get("user_id") == "123"
    assert record2.context.get("session_id") == "abc"

    # Third record should have context
    record3 = backend.records[2]
    assert record3.message == "Context message 2"
    assert record3.context.get("user_id") == "123"
    assert record3.context.get("session_id") == "abc"
    assert record3.metadata.get("extra_data") == "value"

    # Fourth record should have no context (context manager exited)
    record4 = backend.records[3]
    assert record4.message == "No context message 2"
    assert record4.context == {}


@pytest.mark.asyncio
async def test_logger_flush_and_close():
    """Test logger flush and close methods."""
    logger = Logger(module="test.module", level=LogLevel.DEBUG, backend="buffer")

    # Test flush (should not raise)
    await logger.flush()

    # Test close (should not raise)
    await logger.close()
