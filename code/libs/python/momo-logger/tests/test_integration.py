"""Integration tests for momo-logger."""

import pytest
import asyncio
import sys
import os

from momo_logger import get_logger, LogLevel


@pytest.mark.asyncio
async def test_basic_integration():
    """Test basic integration of all components."""
    # Create logger with buffer backend for testing
    logger = get_logger("test.integration", level=LogLevel.DEBUG, backend="buffer")

    # Test all log levels
    await logger.debug("Debug message")
    await logger.info("Info message")
    await logger.warning("Warning message")
    await logger.error("Error message")
    await logger.critical("Critical message")

    # Test AI levels
    await logger.ai_system("AI system message", agent="test")
    await logger.ai_user("AI user message")  # user_facing is set by default
    await logger.ai_agent("AI agent message", target="worker")
    await logger.ai_debug("AI debug message", data="test")

    # Test role-specific levels
    await logger.tester("Tester message", test="integration")
    await logger.developer("Developer message", feature="logging")
    await logger.architect("Architect message", design="module")
    await logger.operator("Operator message", status="running")

    # Get backend and verify all messages were recorded
    backend = await logger._get_backend()
    assert len(backend.records) == 13

    # Verify message content and levels
    messages = [record.message for record in backend.records]
    levels = [record.level for record in backend.records]

    assert "Debug message" in messages
    assert "Info message" in messages
    assert "Warning message" in messages
    assert "Error message" in messages
    assert "Critical message" in messages
    assert "AI system message" in messages
    assert "AI user message" in messages
    assert "AI agent message" in messages
    assert "AI debug message" in messages
    assert "Tester message" in messages
    assert "Developer message" in messages
    assert "Architect message" in messages
    assert "Operator message" in messages

    # Verify AI levels have ai_optimized flag
    ai_records = [
        r
        for r in backend.records
        if r.level
        in [LogLevel.AI_SYSTEM, LogLevel.AI_USER, LogLevel.AI_AGENT, LogLevel.AI_DEBUG]
    ]
    for record in ai_records:
        assert record.ai_optimized is True

    # Verify role-specific levels have agent_role
    role_records = [
        r
        for r in backend.records
        if r.level
        in [LogLevel.TESTER, LogLevel.DEVELOPER, LogLevel.ARCHITECT, LogLevel.OPERATOR]
    ]
    for record in role_records:
        assert record.agent_role is not None


@pytest.mark.asyncio
async def test_context_integration():
    """Test context integration."""
    logger = get_logger("test.context", level=LogLevel.DEBUG, backend="buffer")

    # Log without context
    await logger.info("No context")

    # Log with context
    async with logger.context(user_id="123", session="abc"):
        await logger.info("With context")
        await logger.debug("Debug with context", detail="test")

    # Log without context again
    await logger.warning("No context again")

    # Verify context was applied correctly
    backend = await logger._get_backend()
    assert len(backend.records) == 4

    # First record: no context
    assert backend.records[0].message == "No context"
    assert backend.records[0].context == {}

    # Second record: with context
    assert backend.records[1].message == "With context"
    assert backend.records[1].context == {"user_id": "123", "session": "abc"}

    # Third record: with context and metadata
    assert backend.records[2].message == "Debug with context"
    assert backend.records[2].context == {"user_id": "123", "session": "abc"}
    assert backend.records[2].metadata == {"detail": "test"}

    # Fourth record: no context again
    assert backend.records[3].message == "No context again"
    assert backend.records[3].context == {}


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_basic_integration())
    asyncio.run(test_context_integration())
    print("✅ All integration tests passed!")
