#!/usr/bin/env python3
"""
Concurrent Performance Benchmarks - Measure Logger Performance Under Load

This script measures the performance of the momo-logger under concurrent load
to ensure it can handle high-throughput scenarios in multi-agent systems.
"""

import asyncio
import time
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from momo_logger import get_logger, LogLevel


async def benchmark_concurrent_loggers(num_loggers=10, messages_per_logger=100):
    """Benchmark performance with multiple concurrent loggers."""
    print(
        f"Benchmarking {num_loggers} concurrent loggers with {messages_per_logger} messages each..."
    )

    async def log_messages(logger_id, message_count):
        """Log messages from a single logger."""
        logger = get_logger(
            f"concurrent.logger_{logger_id}", level=LogLevel.DEBUG, backend="buffer"
        )

        for i in range(message_count):
            await logger.info(
                f"Logger {logger_id} message {i}",
                logger_id=logger_id,
                message_id=i,
                timestamp=time.time(),
            )

    # Create tasks for all loggers
    start_time = time.time()

    tasks = []
    for logger_id in range(num_loggers):
        task = log_messages(logger_id, messages_per_logger)
        tasks.append(task)

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

    end_time = time.time()
    total_duration = end_time - start_time
    total_messages = num_loggers * messages_per_logger
    rate = total_messages / total_duration

    print(f"  Total messages: {total_messages}")
    print(f"  Duration: {total_duration:.4f} seconds")
    print(f"  Rate: {rate:.2f} messages/second")
    print(f"  Average: {(total_duration / total_messages) * 1000:.4f} ms per message")

    return total_duration, rate, total_messages


async def benchmark_concurrent_writers(num_workers=5, messages_per_worker=200):
    """Benchmark performance with concurrent writers to the same logger."""
    print(
        f"\nBenchmarking {num_workers} concurrent writers to the same logger with {messages_per_worker} messages each..."
    )

    # Create a single logger that all workers will use
    logger = get_logger("concurrent.shared", level=LogLevel.DEBUG, backend="buffer")

    async def write_messages(worker_id, message_count):
        """Write messages from a worker."""
        for i in range(message_count):
            await logger.info(
                f"Worker {worker_id} message {i}",
                worker_id=worker_id,
                message_id=i,
                timestamp=time.time(),
            )

    # Create tasks for all workers
    start_time = time.time()

    tasks = []
    for worker_id in range(num_workers):
        task = write_messages(worker_id, messages_per_worker)
        tasks.append(task)

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

    end_time = time.time()
    total_duration = end_time - start_time
    total_messages = num_workers * messages_per_worker
    rate = total_messages / total_duration

    print(f"  Total messages: {total_messages}")
    print(f"  Duration: {total_duration:.4f} seconds")
    print(f"  Rate: {rate:.2f} messages/second")
    print(f"  Average: {(total_duration / total_messages) * 1000:.4f} ms per message")

    return total_duration, rate, total_messages


async def benchmark_mixed_workload():
    """Benchmark a mixed workload simulating a real multi-agent system."""
    print("\nBenchmarking mixed workload (simulating multi-agent system)...")

    # Create different types of loggers for different agent roles
    developer_logger = get_logger(
        "agent.developer", level=LogLevel.DEBUG, backend="buffer"
    )
    tester_logger = get_logger("agent.tester", level=LogLevel.DEBUG, backend="buffer")
    architect_logger = get_logger(
        "agent.architect", level=LogLevel.DEBUG, backend="buffer"
    )
    system_logger = get_logger("system.main", level=LogLevel.DEBUG, backend="buffer")

    # Define workloads for different agent types
    workloads = [
        # Developer workload
        (developer_logger, "ai_system", 50, "Code analysis"),
        (developer_logger, "developer", 100, "Feature implementation"),
        (developer_logger, "debug", 200, "Debugging"),
        # Tester workload
        (tester_logger, "tester", 150, "Running tests"),
        (tester_logger, "info", 50, "Test results"),
        (tester_logger, "warning", 25, "Test warnings"),
        # Architect workload
        (architect_logger, "architect", 75, "Design review"),
        (architect_logger, "ai_system", 25, "System analysis"),
        # System workload
        (system_logger, "info", 100, "System events"),
        (system_logger, "warning", 50, "System warnings"),
        (system_logger, "error", 25, "System errors"),
    ]

    async def execute_workload(logger, log_type, count, description):
        """Execute a specific workload."""
        method_map = {
            "debug": logger.debug,
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical,
            "ai_system": logger.ai_system,
            "ai_user": logger.ai_user,
            "ai_agent": logger.ai_agent,
            "ai_debug": logger.ai_debug,
            "tester": logger.tester,
            "developer": logger.developer,
            "architect": logger.architect,
            "operator": logger.operator,
        }

        log_method = method_map.get(log_type, logger.info)

        for i in range(count):
            await log_method(
                f"{description} - {log_type} message {i}",
                workload=description,
                message_type=log_type,
                message_id=i,
            )

    # Execute all workloads concurrently
    start_time = time.time()

    tasks = []
    total_messages = 0

    for logger, log_type, count, description in workloads:
        task = execute_workload(logger, log_type, count, description)
        tasks.append(task)
        total_messages += count

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

    end_time = time.time()
    total_duration = end_time - start_time
    rate = total_messages / total_duration

    print(f"  Total messages: {total_messages}")
    print(f"  Duration: {total_duration:.4f} seconds")
    print(f"  Rate: {rate:.2f} messages/second")
    print(f"  Average: {(total_duration / total_messages) * 1000:.4f} ms per message")

    return total_duration, rate, total_messages


async def benchmark_context_switching(num_contexts=100, messages_per_context=10):
    """Benchmark performance with frequent context switching."""
    print(
        f"\nBenchmarking context switching with {num_contexts} contexts and {messages_per_context} messages each..."
    )

    logger = get_logger(
        "benchmark.context_switching", level=LogLevel.DEBUG, backend="buffer"
    )

    start_time = time.time()

    # Create and use many different contexts
    for context_id in range(num_contexts):
        async with logger.context(
            context_id=context_id,
            session_id=f"session_{context_id}",
            user_id=f"user_{context_id % 10}",
        ):
            for message_id in range(messages_per_context):
                await logger.info(
                    f"Context {context_id} message {message_id}",
                    context_message=f"msg_{message_id}",
                    timestamp=time.time(),
                )

    end_time = time.time()
    total_duration = end_time - start_time
    total_messages = num_contexts * messages_per_context
    rate = total_messages / total_duration

    print(f"  Total messages: {total_messages}")
    print(f"  Total contexts: {num_contexts}")
    print(f"  Duration: {total_duration:.4f} seconds")
    print(f"  Rate: {rate:.2f} messages/second")
    print(f"  Average: {(total_duration / total_messages) * 1000:.4f} ms per message")

    return total_duration, rate, total_messages


async def main():
    print("🏃 Momo Logger - Concurrent Performance Benchmarks")
    print("=" * 55)

    # Run all concurrent benchmarks
    await benchmark_concurrent_loggers(5, 200)
    await benchmark_concurrent_writers(3, 150)
    await benchmark_mixed_workload()
    await benchmark_context_switching(50, 5)

    print("\n🏁 Concurrent performance benchmarks completed!")


if __name__ == "__main__":
    asyncio.run(main())
