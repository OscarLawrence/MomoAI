#!/usr/bin/env python3
"""
Log Levels Demonstration - Comprehensive Overview of All Log Levels

This example shows how to use all available log levels in momo-logger:
- Standard levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- AI-optimized levels (AI_SYSTEM, AI_USER, AI_AGENT, AI_DEBUG)
- Role-specific levels (TESTER, DEVELOPER, ARCHITECT, OPERATOR)
"""

import asyncio
from momo_logger import get_logger, LogLevel


async def main():
    print("📊 Momo Logger - Log Levels Demonstration")
    print("=" * 50)

    # Create a logger with DEBUG level to show all messages
    logger = get_logger("example.levels", level=LogLevel.DEBUG)
    print("✅ Created logger with DEBUG level")

    print("\n📝 Standard Log Levels:")
    print("-" * 30)
    await logger.debug(
        "This is a DEBUG message - detailed information for diagnosing problems"
    )
    await logger.info(
        "This is an INFO message - general information about program execution"
    )
    await logger.warning("This is a WARNING message - something unexpected happened")
    await logger.error("This is an ERROR message - a serious problem occurred")
    await logger.critical(
        "This is a CRITICAL message - the program may not be able to continue"
    )

    print("\n🤖 AI-Optimized Log Levels:")
    print("-" * 30)
    await logger.ai_debug(
        "This is an AI_DEBUG message - detailed AI system information"
    )
    await logger.ai_system(
        "This is an AI_SYSTEM message - AI system operations and status"
    )
    await logger.ai_agent(
        "This is an AI_AGENT message - communication between AI agents"
    )
    await logger.ai_user("This is an AI_USER message - information for end users")

    print("\n👥 Role-Specific Log Levels:")
    print("-" * 30)
    await logger.tester("This is a TESTER message - testing-specific information")
    await logger.developer(
        "This is a DEVELOPER message - development-specific information"
    )
    await logger.architect(
        "This is an ARCHITECT message - architecture-level information"
    )
    await logger.operator(
        "This is an OPERATOR message - operations-specific information"
    )

    print("\n📋 Filtering by Log Level:")
    print("-" * 30)
    # Create a logger with WARNING level - only warnings and above will be logged
    warning_logger = get_logger("example.filtered", level=LogLevel.WARNING)
    print("Created logger with WARNING level - only warnings and above will appear:")
    await warning_logger.debug("This DEBUG message won't appear")
    await warning_logger.info("This INFO message won't appear")
    await warning_logger.warning("This WARNING message will appear")
    await warning_logger.error("This ERROR message will appear")

    print("\n🎉 Log levels demonstration completed!")


if __name__ == "__main__":
    asyncio.run(main())
