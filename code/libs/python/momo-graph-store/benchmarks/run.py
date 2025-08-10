#!/usr/bin/env python3
"""
Benchmark runner for momo-graph-store.

Usage:
    python benchmarks/run.py
    pdm run benchmark
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from performance_benchmarks import main

if __name__ == "__main__":
    asyncio.run(main())
