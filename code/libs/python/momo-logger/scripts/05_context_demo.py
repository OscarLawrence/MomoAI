#!/usr/bin/env python3
"""
Context Management Demonstration - Enriching Log Records with Context

This example shows how to use context management in momo-logger:
- Adding global context to all log records
- Nested context management
- Context for different operations
"""

import asyncio
from momo_logger import get_logger, LogLevel


async def process_user_request(logger, user_id, request_id):
    """Simulate processing a user request with context."""
    print(f"\n🔧 Processing request {request_id} for user {user_id}")

    # Add request-specific context
    async with logger.context(user_id=user_id, request_id=request_id):
        await logger.info("Starting request processing")

        # Simulate database operation
        async with logger.context(operation="database_query", table="users"):
            await logger.debug("Executing database query", query_time=0.045)
            await logger.info("Database query completed", rows_returned=1)

        # Simulate API call
        async with logger.context(
            operation="api_call", endpoint="https://api.example.com"
        ):
            await logger.debug("Making API call", timeout=30)
            await logger.info("API call completed", response_code=200)

        await logger.info("Request processing completed")


async def run_tests(logger):
    """Run various tests with context."""
    print("\n🧪 Running tests with context")

    # Test context for testing
    async with logger.context(test_suite="logger_tests", test_run="001"):
        await logger.tester("Starting test suite", test_count=5)

        # Individual test with more context
        async with logger.context(test_name="context_test", test_id="T001"):
            await logger.tester("Test case started")
            await logger.debug("Performing test operations", operation_count=3)
            await logger.tester("Test case completed", result="PASSED")

        await logger.tester("Test suite completed", passed=1, failed=0)


async def main():
    print("🔄 Momo Logger - Context Management Demonstration")
    print("=" * 50)

    # Create a logger
    logger = get_logger("example.context", level=LogLevel.DEBUG)
    print("✅ Created logger")

    # Global context
    print("\n🌐 Global Context:")
    print("-" * 20)
    async with logger.context(
        application="momo-logger", version="1.0.0", environment="demo"
    ):
        await logger.info("Application started")

        # Process multiple user requests
        await process_user_request(logger, user_id="user_123", request_id="req_abc")
        await process_user_request(logger, user_id="user_456", request_id="req_def")

        # Run tests
        await run_tests(logger)

        await logger.info("Application shutting down")

    # Show that context is cleared
    print("\n🔚 Context Cleared:")
    print("-" * 20)
    await logger.info("This message has no context")

    print("\n🎉 Context management demonstration completed!")


if __name__ == "__main__":
    asyncio.run(main())
