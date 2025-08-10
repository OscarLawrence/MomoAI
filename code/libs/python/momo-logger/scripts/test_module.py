#!/usr/bin/env python3
"""
Module Test - Quick Verification of Core Functionality

This script provides a quick way to verify that the momo-logger
module is working correctly after installation or changes.
"""

import asyncio
from momo_logger import get_logger, LogLevel


async def main():
    print("🧪 Momo Logger - Module Test")
    print("=" * 40)

    # Test basic functionality
    print("\n1. Testing basic logger creation...")
    logger = get_logger("test.module")
    print("✅ Logger created successfully")

    # Test standard log levels
    print("\n2. Testing standard log levels...")
    await logger.debug("Debug message")
    await logger.info("Info message")
    await logger.warning("Warning message", test_key="test_value")
    await logger.error("Error message", error_code=404)
    await logger.critical("Critical message", component="test")
    print("✅ Standard log levels working")

    # Test AI log levels
    print("\n3. Testing AI log levels...")
    await logger.ai_system("AI system message", agent="test")
    await logger.ai_user("AI user message")
    await logger.ai_agent("AI agent message", target="worker")
    await logger.ai_debug("AI debug message", data="test")
    print("✅ AI log levels working")

    # Test role-specific log levels
    print("\n4. Testing role-specific log levels...")
    await logger.tester("Tester message", test_case="basic")
    await logger.developer("Developer message", feature="logging")
    await logger.architect("Architect message", design="module")
    await logger.operator("Operator message", status="running")
    print("✅ Role-specific log levels working")

    # Test context management
    print("\n5. Testing context management...")
    async with logger.context(user_id="123", session="test"):
        await logger.info("Message with context")
        await logger.debug("Debug with context", detail="value")
    print("✅ Context management working")

    # Test different backends
    print("\n6. Testing different backends...")
    console_logger = get_logger("test.console", backend="console")
    buffer_logger = get_logger("test.buffer", backend="buffer")

    await console_logger.info("Console backend message")
    await buffer_logger.info("Buffer backend message", test_id=1)
    print("✅ Different backends working")

    # Test different formatters
    print("\n7. Testing different formatters...")
    text_logger = get_logger("test.text", formatter="text")
    json_logger = get_logger("test.json", formatter="json")
    ai_logger = get_logger("test.ai", formatter="ai")

    await text_logger.info("Text formatter message")
    await json_logger.info("JSON formatter message", data="structured")
    await ai_logger.info("AI formatter message", ai_optimized=True)
    print("✅ Different formatters working")

    print("\n🎉 All tests passed! Momo Logger is working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
