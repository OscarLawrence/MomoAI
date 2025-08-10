#!/usr/bin/env python3
"""
Benchmark Runner for Momo Logger Module

This script provides a convenient way to run performance benchmarks
for the momo-logger module.
"""

import os
import sys
import argparse
import importlib.util
from pathlib import Path


def list_benchmarks():
    """List all available benchmarks."""
    benchmarks_dir = Path(__file__).parent
    benchmarks = []

    for file in benchmarks_dir.glob("*.py"):
        if file.name not in ["run.py", "__init__.py"]:
            # Get the description from the docstring
            description = get_benchmark_description(file)
            benchmarks.append((file.stem, description))

    if benchmarks:
        print("Available benchmarks:")
        print("-" * 50)
        for name, description in sorted(benchmarks):
            print(f"  {name:<25} {description}")
        print("-" * 50)
        print(f"\nRun with: python benchmarks/run.py <benchmark_name>")
        print(f"Or: pdm run python benchmarks/run.py <benchmark_name>")
    else:
        print("No benchmarks found in the benchmarks directory.")


def get_benchmark_description(benchmark_path):
    """Extract description from benchmark docstring."""
    try:
        with open(benchmark_path, "r") as f:
            # Read first few lines to find docstring
            content = f.read(1000)  # Read first 1000 chars

            # Look for module docstring (first triple-quoted string)
            if '"""' in content:
                start = content.find('"""') + 3
                end = content.find('"""', start)
                if end != -1:
                    docstring = content[start:end].strip()
                    # Return first line as description
                    lines = docstring.split("\n")
                    return lines[0] if lines else "No description"

            return "No description"
    except Exception:
        return "No description"


def run_benchmark(benchmark_name):
    """Run a specific benchmark by name."""
    benchmarks_dir = Path(__file__).parent
    benchmark_path = benchmarks_dir / f"{benchmark_name}.py"

    if not benchmark_path.exists():
        print(f"Error: Benchmark '{benchmark_name}' not found.")
        print(f"Available benchmarks:")
        list_benchmarks()
        sys.exit(1)

    # Import and run the benchmark
    spec = importlib.util.spec_from_file_location(benchmark_name, benchmark_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # If the benchmark has a main function, call it
    if hasattr(module, "main"):
        import asyncio

        if asyncio.iscoroutinefunction(module.main):
            asyncio.run(module.main())
        else:
            module.main()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Momo Logger Benchmark Runner")
    parser.add_argument("benchmark", nargs="?", help="Benchmark to run")
    parser.add_argument(
        "--list", action="store_true", help="List all available benchmarks"
    )

    args = parser.parse_args()

    if args.list:
        list_benchmarks()
    elif args.benchmark:
        run_benchmark(args.benchmark)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
