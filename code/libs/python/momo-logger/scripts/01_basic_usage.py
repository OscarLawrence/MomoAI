#!/usr/bin/env python3
"""
Basic Usage Example - Getting Started with Momo Logger

This example shows the simplest way to use momo-logger:
- Create a logger
- Log messages at different levels
- Use AI-optimized logging
- Use role-specific logging
- Add context to log records
"""

import asyncio
import sys
import os

from momo_logger import get_logger, LogLevel


async def main():
    print("📝 Momo Logger - Basic Usage Example")
    print("=" * 50)

    # Create a logger (uses console backend by default)
    logger = get_logger("example.basic")
    print("✅ Created logger")

    # Basic logging
    print("\n📝 Basic logging...")
    await logger.debug("This is a debug message")
    await logger.info("Application started successfully")
    await logger.warning("This is a warning message", user_id=123)
    await logger.error("An error occurred", error_code="E001")
    await logger.critical("Critical system failure", component="database")

    # AI-optimized logging
    print("\n🤖 AI-optimized logging...")
    await logger.ai_system(
        "Agent selection completed",
        agent="momo_agent",
        selected_agent="developer_agent",
        confidence=0.95,
    )

    await logger.ai_user(
        "I've found the information you requested about Python", user_facing=True
    )

    await logger.ai_agent(
        "Task dispatched to worker agent",
        target_agent="code_analyzer",
        task_id="task_123",
    )

    await logger.ai_debug(
        "Neural network weights updated", layer="hidden_1", weights_changed=1542
    )

    # Role-specific logging
    print("\n👥 Role-specific logging...")
    await logger.tester(
        "Test case passed", test_name="document_save_test", duration_ms=125
    )
    await logger.developer(
        "Implemented new feature", feature="graph_traversal", files_changed=3
    )
    await logger.architect(
        "Refactored module structure", modules_affected=["kb", "core"]
    )
    await logger.operator("System operational", uptime_hours=168, cpu_usage=23)

    # Context management
    print("\n🔄 Context management...")
    async with logger.context(
        user_id="user_123", session_id="session_abc", request_id="req_xyz"
    ):
        await logger.info("Processing user request")
        await logger.debug(
            "Detailed operation info", operation="document_save", size_bytes=1024
        )
        await logger.tester("Sub-test completed", sub_test="validation")

    # Log with different level
    print("\n🔍 Logging with different minimum level...")
    quiet_logger = get_logger("example.quiet", level=LogLevel.WARNING)
    await quiet_logger.debug("This debug message won't be logged")
    await quiet_logger.info("This info message won't be logged")
    await quiet_logger.warning("This warning will be logged")
    await quiet_logger.error("This error will be logged")

    # User-facing messages
    print("\n💬 User-facing messages...")
    await logger.info("✅ Document saved successfully", user_facing=True)
    await logger.warning(
        "⚠️ Large document detected, processing may take a moment", user_facing=True
    )
    await logger.error("❌ Failed to save document", user_facing=True)

    print("\n🎉 Basic usage example completed!")


if __name__ == "__main__":
    asyncio.run(main())
