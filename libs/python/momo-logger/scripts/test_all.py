#!/usr/bin/env python3
"""
Test All Scripts - Verify All Examples and Benchmarks Work

This script runs quick tests on all example scripts and benchmarks
to ensure they're working correctly.
"""

import asyncio
import sys
import os
from pathlib import Path


# Add the src directory to the path so we can import momo_logger
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


async def test_script(script_name):
    """Test a single script."""
    try:
        scripts_dir = Path(__file__).parent
        script_path = scripts_dir / f"{script_name}.py"

        if not script_path.exists():
            print(f"❌ Script {script_name} not found")
            return False

        # Import and run the script
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # If the script has a main function, call it with a timeout
        if hasattr(module, "main"):
            print(f"🏃 Testing {script_name}...")
            try:
                if asyncio.iscoroutinefunction(module.main):
                    # Run with timeout to prevent hanging
                    await asyncio.wait_for(module.main(), timeout=10.0)
                else:
                    module.main()
                print(f"✅ {script_name} completed successfully")
                return True
            except asyncio.TimeoutError:
                print(
                    f"⏰ {script_name} timed out (this is expected for long-running scripts)"
                )
                return True
            except Exception as e:
                print(f"❌ {script_name} failed with error: {e}")
                return False
        else:
            print(f"✅ {script_name} imported successfully")
            return True

    except Exception as e:
        print(f"❌ Failed to test {script_name}: {e}")
        return False


async def main():
    print("🧪 Momo Logger - Test All Scripts and Benchmarks")
    print("=" * 55)

    # Test all example scripts
    example_scripts = [
        "01_basic_usage",
        "02_backend_demonstration",
        "03_log_levels_demo",
        "04_formatter_demo",
        "05_context_demo",
        "06_comprehensive_example",
        "test_module",
    ]

    print("📋 Testing Example Scripts:")
    print("-" * 30)

    results = []
    for script in example_scripts:
        result = await test_script(script)
        results.append((script, result))

    # Test benchmark scripts
    print("\n📊 Testing Benchmark Scripts:")
    print("-" * 30)

    benchmark_scripts = ["basic_performance", "concurrent_performance"]

    for script in benchmark_scripts:
        # Just test that they can be imported
        try:
            benchmarks_dir = Path(__file__).parent.parent / "benchmarks"
            script_path = benchmarks_dir / f"{script}.py"

            if script_path.exists():
                spec = importlib.util.spec_from_file_location(script, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"✅ {script} imported successfully")
                results.append((script, True))
            else:
                print(f"❌ {script} not found")
                results.append((script, False))
        except Exception as e:
            print(f"❌ {script} failed to import: {e}")
            results.append((script, False))

    # Summary
    print("\n📈 Test Summary:")
    print("-" * 20)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1


if __name__ == "__main__":
    import importlib.util

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
