"""Tests for logger formatters."""

import json
import pytest
from datetime import datetime
from momo_logger.types import LogLevel, LogRecord
from momo_logger.formatters.json import JSONFormatter
from momo_logger.formatters.text import TextFormatter
from momo_logger.formatters.ai import AIFormatter


def test_json_formatter():
    """Test JSON formatter functionality."""
    formatter = JSONFormatter()

    # Create a log record
    timestamp = datetime.now()
    record = LogRecord(
        timestamp=timestamp,
        level=LogLevel.INFO,
        message="Test JSON message",
        module="test.module",
        context={"key": "value"},
        metadata={"meta": "data"},
    )

    # Format the record
    formatted = formatter.format(record)

    # Parse the JSON to verify structure
    parsed = json.loads(formatted)

    assert parsed["message"] == "Test JSON message"
    assert parsed["module"] == "test.module"
    assert parsed["level"] == "info"
    assert parsed["context"]["key"] == "value"
    assert parsed["metadata"]["meta"] == "data"
    assert "timestamp" in parsed


def test_text_formatter():
    """Test text formatter functionality."""
    formatter = TextFormatter()

    # Create a log record
    timestamp = datetime.now()
    record = LogRecord(
        timestamp=timestamp,
        level=LogLevel.INFO,
        message="Test text message",
        module="test.module",
    )

    # Format the record
    formatted = formatter.format(record)

    # Check that it contains expected elements
    assert "Test text message" in formatted
    assert "test.module" in formatted
    assert "INFO" in formatted


def test_text_formatter_user_facing():
    """Test text formatter with user-facing messages."""
    formatter = TextFormatter()

    # Create a user-facing log record
    record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Operation completed successfully",
        module="test.module",
        user_facing=True,
    )

    # Format the record
    formatted = formatter.format(record)

    # Should have user-friendly formatting
    assert "✅" in formatted
    assert "Operation completed successfully" in formatted


def test_text_formatter_warnings_errors():
    """Test text formatter with warnings and errors."""
    formatter = TextFormatter()

    # Test warning
    warning_record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.WARNING,
        message="This is a warning",
        module="test.module",
        user_facing=True,
    )

    formatted_warning = formatter.format(warning_record)
    assert "⚠️" in formatted_warning

    # Test error
    error_record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.ERROR,
        message="This is an error",
        module="test.module",
        user_facing=True,
    )

    formatted_error = formatter.format(error_record)
    assert "❌" in formatted_error


def test_ai_formatter():
    """Test AI formatter functionality."""
    formatter = AIFormatter()

    # Create a log record
    timestamp = datetime.now()
    record = LogRecord(
        timestamp=timestamp,
        level=LogLevel.AI_SYSTEM,
        message="Agent selection completed",
        module="momo.agent",
        agent="momo_agent",
        agent_role="orchestrator",
        ai_optimized=True,
        context={"selected_agent": "developer_agent"},
        metadata={"confidence": 0.95},
    )

    # Format the record
    formatted = formatter.format(record)

    # Parse the JSON to verify structure
    parsed = json.loads(formatted)

    assert parsed["type"] == "log"
    assert parsed["message"] == "Agent selection completed"
    assert parsed["module"] == "momo.agent"
    assert parsed["level"] == "ai_system"
    assert parsed["agent"] == "momo_agent"
    assert parsed["agent_role"] == "orchestrator"
    assert parsed["ai_optimized"] is True
    assert parsed["context"]["selected_agent"] == "developer_agent"
    assert parsed["metadata"]["confidence"] == 0.95
