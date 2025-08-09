#!/usr/bin/env python3
"""
Formatter Demonstration - Different Output Formats for Different Needs

This example shows how to use different formatters in momo-logger:
- Text formatter (human-readable output)
- JSON formatter (structured data)
- AI formatter (AI-optimized output)
"""

import asyncio
import tempfile
import os
from momo_logger import get_logger, LogLevel


async def main():
    print("📝 Momo Logger - Formatter Demonstration")
    print("=" * 50)

    # Text formatter (default)
    print("\n📄 Text Formatter (Default):")
    print("-" * 30)
    text_logger = get_logger("example.text", level=LogLevel.DEBUG, formatter="text")
    await text_logger.info(
        "This message uses the text formatter", user_id=123, action="login"
    )
    await text_logger.error(
        "Error with text formatter", error_code="E001", retry_count=3
    )
    await text_logger.ai_user("AI message with text formatter", response_time=0.125)

    # JSON formatter
    print("\n🔍 JSON Formatter (Structured Data):")
    print("-" * 30)
    # Create a temporary file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_file:
        json_log_file = tmp_file.name

    try:
        json_logger = get_logger(
            "example.json",
            level=LogLevel.DEBUG,
            formatter="json",
            backend="file",
            filepath=json_log_file,
        )

        await json_logger.info(
            "This message uses the JSON formatter", user_id=456, action="save"
        )
        await json_logger.warning(
            "Warning with JSON formatter", disk_usage=85, threshold=80
        )
        await json_logger.ai_system(
            "AI system message in JSON", agent="orchestrator", status="active"
        )

        # Flush and close to ensure data is written
        await json_logger.flush()
        await json_logger.close()

        # Show the JSON output
        print("JSON log file contents:")
        with open(json_log_file, "r") as f:
            print(f.read())

    finally:
        # Clean up
        if os.path.exists(json_log_file):
            os.unlink(json_log_file)

    # AI formatter
    print("\n🤖 AI Formatter (AI-Optimized):")
    print("-" * 30)
    ai_logger = get_logger("example.ai", level=LogLevel.DEBUG, formatter="ai")
    await ai_logger.ai_system(
        "Agent selection completed",
        agent="momo_agent",
        selected_agent="developer_agent",
        confidence=0.95,
    )
    await ai_logger.ai_agent(
        "Task dispatched",
        source_agent="momo_agent",
        target_agent="code_analyzer",
        task_id="task_123",
    )
    await ai_logger.developer(
        "Feature implemented", feature="formatter_support", files_changed=3
    )

    print("\n🎉 Formatter demonstration completed!")


if __name__ == "__main__":
    asyncio.run(main())
