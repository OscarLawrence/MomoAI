"""Tests for logger types and models."""

import pytest
from datetime import datetime
from momo_logger.types import LogLevel, LogRecord


def test_log_levels_defined():
    """Test that all log levels are properly defined."""
    # Test standard levels
    assert LogLevel.DEBUG == "debug"
    assert LogLevel.INFO == "info"
    assert LogLevel.WARNING == "warning"
    assert LogLevel.ERROR == "error"
    assert LogLevel.CRITICAL == "critical"

    # Test AI levels
    assert LogLevel.AI_SYSTEM == "ai_system"
    assert LogLevel.AI_USER == "ai_user"
    assert LogLevel.AI_AGENT == "ai_agent"
    assert LogLevel.AI_DEBUG == "ai_debug"

    # Test role-specific levels
    assert LogLevel.TESTER == "tester"
    assert LogLevel.DEVELOPER == "developer"
    assert LogLevel.ARCHITECT == "architect"
    assert LogLevel.OPERATOR == "operator"


def test_log_record_creation():
    """Test that LogRecord can be created with minimal parameters."""
    record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Test message",
        module="test.module",
    )

    assert record.message == "Test message"
    assert record.module == "test.module"
    assert record.level == LogLevel.INFO
    assert isinstance(record.timestamp, datetime)
    assert record.context == {}
    assert record.metadata == {}


def test_log_record_with_optional_fields():
    """Test that LogRecord can be created with optional fields."""
    record = LogRecord(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Test message",
        module="test.module",
        agent="test_agent",
        agent_role="tester",
        user_facing=True,
        ai_optimized=True,
        context={"key": "value"},
        metadata={"meta": "data"},
        exception="Test exception",
        trace_id="trace_123",
    )

    assert record.agent == "test_agent"
    assert record.agent_role == "tester"
    assert record.user_facing is True
    assert record.ai_optimized is True
    assert record.context == {"key": "value"}
    assert record.metadata == {"meta": "data"}
    assert record.exception == "Test exception"
    assert record.trace_id == "trace_123"
