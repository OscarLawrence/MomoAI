#!/usr/bin/env python3
"""
Backend Demonstration - Different Backends and Formatters

This example shows how to use different backends and formatters:
- Console backend with text formatter
- File backend with JSON formatter
- Buffer backend for testing
"""

import asyncio
import sys
import os
import tempfile

from momo_logger import (
    get_logger,
    get_console_logger,
    get_file_logger,
    get_buffer_logger,
)
from momo_logger.types import LogLevel


async def main():
    print("📂 Momo Logger - Backend Demonstration")
    print("=" * 50)

    # Console logger (default)
    console_logger = get_console_logger("example.console", level=LogLevel.DEBUG)
    print("\n📝 Console logging (text formatter):")
    await console_logger.info("This goes to console")
    await console_logger.warning("Console warning", user_id=456)

    # File logger
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_file:
        log_file = tmp_file.name

    try:
        file_logger = get_file_logger(
            "example.file", level=LogLevel.DEBUG, filepath=log_file
        )
        print(f"\n📝 File logging (JSON formatter) to {log_file}:")
        await file_logger.info("This goes to file", record_id=1)
        await file_logger.error("File error", error_code="F001")

        # Flush to ensure data is written
        await file_logger.flush()
        await file_logger.close()

        # Show file contents
        print("\n📄 File contents:")
        with open(log_file, "r") as f:
            print(f.read())

    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)

    # Buffer logger (for testing)
    buffer_logger = get_buffer_logger("example.buffer", level=LogLevel.DEBUG)
    print("\n📝 Buffer logging (for testing):")
    await buffer_logger.info("This goes to buffer", test_id=1)
    await buffer_logger.warning("Buffer warning", test_id=2)

    # Show buffer contents
    backend = await buffer_logger._get_backend()
    print(f"\n📋 Buffer contents ({len(backend.records)} records):")
    for i, record in enumerate(backend.records, 1):
        print(f"  {i}. [{record.level.value.upper()}] {record.message}")
        if record.metadata:
            print(f"      Metadata: {record.metadata}")

    print("\n🎉 Backend demonstration completed!")


if __name__ == "__main__":
    asyncio.run(main())
