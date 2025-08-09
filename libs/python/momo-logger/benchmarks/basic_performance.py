#!/usr/bin/env python3
"""
Basic Performance Benchmarks - Measure Logger Performance

This script measures the performance of different aspects of the momo-logger
to ensure it meets performance requirements for high-throughput applications.
"""

import asyncio
import time
import tempfile
import os
from momo_logger import get_logger, LogLevel


async def benchmark_basic_logging(iterations=1000):
    """Benchmark basic logging performance."""
    print(f"Benchmarking basic logging with {iterations} iterations...")

    logger = get_logger("benchmark.basic", level=LogLevel.DEBUG, backend="buffer")

    start_time = time.time()

    for i in range(iterations):
        await logger.info(f"Log message {i}", iteration=i, test=True)

    end_time = time.time()
    duration = end_time - start_time
    rate = iterations / duration

    print(f"  Duration: {duration:.4f} seconds")
    print(f"  Rate: {rate:.2f} messages/second")
    print(f"  Average: {(duration / iterations) * 1000:.4f} ms per message")

    return duration, rate


async def benchmark_different_levels(iterations=1000):
    """Benchmark performance across different log levels."""
    print(f"\nBenchmarking different log levels with {iterations} iterations each...")

    logger = get_logger("benchmark.levels", level=LogLevel.DEBUG, backend="buffer")

    levels = [
        ("DEBUG", logger.debug),
        ("INFO", logger.info),
        ("WARNING", logger.warning),
        ("ERROR", logger.error),
        ("CRITICAL", logger.critical),
        ("AI_SYSTEM", logger.ai_system),
        ("AI_USER", logger.ai_user),
        ("TESTER", logger.tester),
        ("DEVELOPER", logger.developer),
    ]

    results = {}

    for level_name, log_method in levels:
        start_time = time.time()

        for i in range(iterations):
            await log_method(f"{level_name} message {i}", test_id=i)

        end_time = time.time()
        duration = end_time - start_time
        rate = iterations / duration

        results[level_name] = {
            "duration": duration,
            "rate": rate,
            "avg_ms": (duration / iterations) * 1000,
        }

        print(
            f"  {level_name:12} - {rate:8.2f} msg/sec - {results[level_name]['avg_ms']:6.4f} ms/msg"
        )

    return results


async def benchmark_backends(iterations=1000):
    """Benchmark performance across different backends."""
    print(f"\nBenchmarking different backends with {iterations} iterations...")

    # Buffer backend (fastest)
    buffer_logger = get_logger(
        "benchmark.buffer", level=LogLevel.DEBUG, backend="buffer"
    )
    start_time = time.time()

    for i in range(iterations):
        await buffer_logger.info(f"Buffer message {i}", test_id=i)

    buffer_duration = time.time() - start_time
    buffer_rate = iterations / buffer_duration

    print(
        f"  Buffer      - {buffer_rate:8.2f} msg/sec - {(buffer_duration / iterations) * 1000:6.4f} ms/msg"
    )

    # Console backend
    console_logger = get_logger(
        "benchmark.console", level=LogLevel.DEBUG, backend="console"
    )
    start_time = time.time()

    for i in range(min(iterations, 100)):  # Limit console output to avoid spam
        await console_logger.info(f"Console message {i}", test_id=i)

    console_duration = time.time() - start_time
    console_rate = (
        min(iterations, 100) / console_duration if console_duration > 0 else 0
    )

    print(
        f"  Console     - {console_rate:8.2f} msg/sec - {(console_duration / min(iterations, 100)) * 1000:6.4f} ms/msg"
    )

    # File backend
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_file:
        log_file = tmp_file.name

    try:
        file_logger = get_logger(
            "benchmark.file", level=LogLevel.DEBUG, backend="file", filepath=log_file
        )
        start_time = time.time()

        for i in range(iterations):
            await file_logger.info(f"File message {i}", test_id=i)

        # Flush to ensure all writes are complete
        await file_logger.flush()
        await file_logger.close()

        file_duration = time.time() - start_time
        file_rate = iterations / file_duration

        print(
            f"  File        - {file_rate:8.2f} msg/sec - {(file_duration / iterations) * 1000:6.4f} ms/msg"
        )

    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)

    return {
        "buffer": {"duration": buffer_duration, "rate": buffer_rate},
        "console": {"duration": console_duration, "rate": console_rate},
        "file": {"duration": file_duration, "rate": file_rate},
    }


async def benchmark_formatters(iterations=1000):
    """Benchmark performance across different formatters."""
    print(f"\nBenchmarking different formatters with {iterations} iterations...")

    formatters = ["text", "json", "ai"]
    results = {}

    for formatter_name in formatters:
        logger = get_logger(
            "benchmark.formatter",
            level=LogLevel.DEBUG,
            backend="buffer",
            formatter=formatter_name,
        )
        start_time = time.time()

        for i in range(iterations):
            await logger.info(
                f"{formatter_name} formatter message {i}",
                test_id=i,
                formatter=formatter_name,
            )

        duration = time.time() - start_time
        rate = iterations / duration

        results[formatter_name] = {"duration": duration, "rate": rate}

        print(
            f"  {formatter_name:4} - {rate:8.2f} msg/sec - {(duration / iterations) * 1000:6.4f} ms/msg"
        )

    return results


async def benchmark_context_management(iterations=1000):
    """Benchmark context management performance."""
    print(f"\nBenchmarking context management with {iterations} iterations...")

    logger = get_logger("benchmark.context", level=LogLevel.DEBUG, backend="buffer")

    # Without context
    start_time = time.time()
    for i in range(iterations):
        await logger.info(f"No context message {i}", test_id=i)
    no_context_duration = time.time() - start_time
    no_context_rate = iterations / no_context_duration

    # With context
    start_time = time.time()
    async with logger.context(benchmark="context", test_run="001"):
        for i in range(iterations):
            await logger.info(f"With context message {i}", test_id=i)
    with_context_duration = time.time() - start_time
    with_context_rate = iterations / with_context_duration

    print(
        f"  No context   - {no_context_rate:8.2f} msg/sec - {(no_context_duration / iterations) * 1000:6.4f} ms/msg"
    )
    print(
        f"  With context - {with_context_rate:8.2f} msg/sec - {(with_context_duration / iterations) * 1000:6.4f} ms/msg"
    )

    overhead = (
        (with_context_duration - no_context_duration) / no_context_duration
    ) * 100
    print(f"  Context overhead: {overhead:.2f}%")

    return {
        "no_context": {"duration": no_context_duration, "rate": no_context_rate},
        "with_context": {"duration": with_context_duration, "rate": with_context_rate},
        "overhead_percent": overhead,
    }


async def main():
    print("⏱️  Momo Logger - Basic Performance Benchmarks")
    print("=" * 50)

    # Run all benchmarks
    await benchmark_basic_logging(5000)
    await benchmark_different_levels(1000)
    await benchmark_backends(2000)
    await benchmark_formatters(1000)
    await benchmark_context_management(1000)

    print("\n🏁 Performance benchmarks completed!")


if __name__ == "__main__":
    asyncio.run(main())
