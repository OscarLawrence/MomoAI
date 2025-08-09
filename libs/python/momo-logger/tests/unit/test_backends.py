"""Tests for logger backends."""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime
from momo_logger.types import LogLevel, LogRecord
from momo_logger.backends.console import ConsoleBackend
from momo_logger.backends.file import FileBackend
from momo_logger.backends.buffer import BufferBackend


@pytest.mark.asyncio
async def test_console_backend():
    """Test console backend functionality."""
    backend = ConsoleBackend()

    # Create a log record
    record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Test console message",
        module="test.module",
    )

    # Write the record
    result = await backend.write(record)
    assert result is True

    # Test flush (should not raise)
    await backend.flush()

    # Test close (should not raise)
    await backend.close()


@pytest.mark.asyncio
async def test_console_backend_stderr():
    """Test console backend with stderr."""
    backend = ConsoleBackend(stream="stderr")

    # Create a log record
    record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Test stderr message",
        module="test.module",
    )

    # Write the record
    result = await backend.write(record)
    assert result is True


@pytest.mark.asyncio
async def test_file_backend():
    """Test file backend functionality."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        filepath = tmp_file.name

    try:
        backend = FileBackend(filepath=filepath)

        # Create a log record
        record = LogRecord(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="Test file message",
            module="test.module",
        )

        # Write the record
        result = await backend.write(record)
        assert result is True

        # Test flush
        await backend.flush()

        # Test close
        await backend.close()

        # Check that file was written
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            content = f.read()
            assert "Test file message" in content

    finally:
        # Clean up
        if os.path.exists(filepath):
            os.unlink(filepath)


@pytest.mark.asyncio
async def test_buffer_backend():
    """Test buffer backend functionality."""
    backend = BufferBackend()

    # Create a log record
    record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Test buffer message",
        module="test.module",
    )

    # Initially buffer should be empty
    assert len(backend.records) == 0

    # Write the record
    result = await backend.write(record)
    assert result is True

    # Check that record was stored
    assert len(backend.records) == 1
    assert backend.records[0].message == "Test buffer message"

    # Test flush (should not raise)
    await backend.flush()

    # Test close
    await backend.close()

    # After close, records should be cleared
    assert len(backend.records) == 0


@pytest.mark.asyncio
async def test_buffer_backend_clear():
    """Test buffer backend clear functionality."""
    backend = BufferBackend()

    # Add some records
    record1 = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Message 1",
        module="test.module",
    )

    record2 = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Message 2",
        module="test.module",
    )

    await backend.write(record1)
    await backend.write(record2)

    assert len(backend.records) == 2

    # Clear the buffer
    backend.clear()

    assert len(backend.records) == 0
