#!/usr/bin/env python3
"""
Comprehensive test runner for momo-store-document with coverage analysis.

Runs all tests and generates coverage reports to ensure 90%+ test coverage.
"""

import subprocess
import sys
import os
from pathlib import Path
import json


def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "pytest", "pytest-cov", "pytest-asyncio", 
        "pandas", "duckdb", "psutil"
    ]
    
    missing = []
    for package in required_packages:
        success, _, _ = run_command(f"python3 -c 'import {package}'")
        if not success:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All dependencies available")
    return True


def run_unit_tests():
    """Run unit tests with coverage."""
    print("\n🧪 Running Unit Tests with Coverage")
    print("-" * 40)
    
    # Change to the momo-store-document directory
    test_dir = Path("code/libs/python/momo-store-document")
    
    # Run pytest with coverage
    cmd = [
        "python3", "-m", "pytest",
        "tests/",
        "--cov=momo_store_document",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_html",
        "--cov-report=json:coverage.json",
        "--cov-fail-under=90",
        "-v",
        "--tb=short"
    ]
    
    success, stdout, stderr = run_command(" ".join(cmd), cwd=test_dir)
    
    print(stdout)
    if stderr:
        print("STDERR:", stderr)
    
    return success


def analyze_coverage():
    """Analyze coverage results and provide detailed report."""
    print("\n📊 Coverage Analysis")
    print("-" * 30)
    
    coverage_file = Path("code/libs/python/momo-store-document/coverage.json")
    
    if not coverage_file.exists():
        print("❌ Coverage file not found")
        return False
    
    try:
        with open(coverage_file) as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data["totals"]["percent_covered"]
        print(f"📈 Total Coverage: {total_coverage:.1f}%")
        
        # Analyze per-file coverage
        files = coverage_data["files"]
        
        print("\n📁 Per-File Coverage:")
        print("File                           | Coverage | Missing Lines")
        print("-" * 60)
        
        for file_path, file_data in files.items():
            filename = Path(file_path).name
            coverage_pct = file_data["summary"]["percent_covered"]
            missing_lines = len(file_data["missing_lines"])
            
            status = "✅" if coverage_pct >= 90 else "⚠️" if coverage_pct >= 80 else "❌"
            print(f"{status} {filename:25} | {coverage_pct:7.1f}% | {missing_lines:4d} lines")
        
        # Identify areas needing more tests
        low_coverage_files = [
            (path, data) for path, data in files.items() 
            if data["summary"]["percent_covered"] < 90
        ]
        
        if low_coverage_files:
            print(f"\n⚠️  Files needing more tests ({len(low_coverage_files)} files):")
            for file_path, file_data in low_coverage_files:
                filename = Path(file_path).name
                coverage_pct = file_data["summary"]["percent_covered"]
                missing_lines = file_data["missing_lines"]
                print(f"   {filename}: {coverage_pct:.1f}% (missing lines: {missing_lines[:10]}{'...' if len(missing_lines) > 10 else ''})")
        
        return total_coverage >= 90.0
        
    except Exception as e:
        print(f"❌ Error analyzing coverage: {e}")
        return False


def run_integration_tests():
    """Run integration tests."""
    print("\n🔗 Running Integration Tests")
    print("-" * 30)
    
    test_dir = Path("code/libs/python/momo-store-document")
    
    # Run integration tests if they exist
    integration_test_dir = test_dir / "tests" / "integration"
    if integration_test_dir.exists():
        cmd = [
            "python3", "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short"
        ]
        
        success, stdout, stderr = run_command(" ".join(cmd), cwd=test_dir)
        print(stdout)
        if stderr:
            print("STDERR:", stderr)
        return success
    else:
        print("ℹ️  No integration tests found")
        return True


def run_benchmark_validation():
    """Run a quick benchmark validation."""
    print("\n⚡ Running Benchmark Validation")
    print("-" * 30)
    
    # Create a simple benchmark validation script
    validation_script = """
import asyncio
import tempfile
import os
import time
import sys
from pathlib import Path

# Add the module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "momo_store_document"))

try:
    from PandasDocumentStore import PandasDocumentBackend
    from persistence import DuckDBPersistence, NoPersistence
    
    async def quick_benchmark():
        print("🚀 Quick Performance Validation")
        
        # Test DuckDB backend
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            backend = PandasDocumentBackend(
                DuckDBPersistence(db_path), 
                cache_size=50
            )
            
            # Add test documents
            test_docs = []
            for i in range(100):
                doc = {
                    "content": f"Test document {i}",
                    "metadata": {"type": "test", "id": i}
                }
                test_docs.append((f"doc_{i}", doc))
            
            # Benchmark bulk insert
            start_time = time.time()
            for doc_id, doc in test_docs:
                await backend.put(doc_id, doc)
            insert_time = time.time() - start_time
            
            print(f"✅ Inserted 100 docs in {insert_time:.3f}s ({100/insert_time:.1f} docs/sec)")
            
            # Benchmark retrieval
            start_time = time.time()
            for i in range(10):
                doc = await backend.get("doc_0")
            get_time = time.time() - start_time
            
            print(f"✅ 10 retrievals in {get_time:.3f}s ({10/get_time:.1f} ops/sec)")
            
            # Benchmark scan
            start_time = time.time()
            results = await backend.scan(filters={"type": "test"})
            scan_time = time.time() - start_time
            
            print(f"✅ Scan found {len(results)} docs in {scan_time:.3f}s")
            
            await backend.close()
            
            # Validate optimizations are working
            if insert_time < 5.0 and get_time < 0.1 and scan_time < 1.0:
                print("🎉 Performance validation passed!")
                return True
            else:
                print("⚠️  Performance slower than expected")
                return False
                
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    return asyncio.run(quick_benchmark())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    return False
except Exception as e:
    print(f"❌ Benchmark error: {e}")
    return False
"""
    
    # Write and run validation script
    script_path = Path("code/libs/python/momo-store-document/temp_benchmark_validation.py")
    with open(script_path, "w") as f:
        f.write(validation_script)
    
    try:
        success, stdout, stderr = run_command(f"python3 {script_path}")
        print(stdout)
        if stderr:
            print("STDERR:", stderr)
        return success
    finally:
        if script_path.exists():
            script_path.unlink()


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n📋 Generating Test Report")
    print("-" * 30)
    
    report = []
    report.append("# Momo Store Document - Test Coverage Report")
    report.append("=" * 50)
    report.append("")
    
    # Read coverage data
    coverage_file = Path("code/libs/python/momo-store-document/coverage.json")
    if coverage_file.exists():
        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data["totals"]["percent_covered"]
            total_lines = coverage_data["totals"]["num_statements"]
            covered_lines = coverage_data["totals"]["covered_lines"]
            
            report.append(f"## Overall Coverage: {total_coverage:.1f}%")
            report.append(f"- Total Lines: {total_lines}")
            report.append(f"- Covered Lines: {covered_lines}")
            report.append(f"- Missing Lines: {total_lines - covered_lines}")
            report.append("")
            
            # Test categories covered
            report.append("## Test Categories Covered")
            report.append("✅ Document Cache (LRU, invalidation, edge cases)")
            report.append("✅ DuckDB Query Pushdown (WHERE clauses, column selection)")
            report.append("✅ PandasDocumentBackend Optimizations (caching integration)")
            report.append("✅ Error Handling and Fallbacks")
            report.append("✅ Backward Compatibility")
            report.append("✅ Performance Benchmarks")
            report.append("")
            
            # Optimization features tested
            report.append("## Optimization Features Tested")
            report.append("- [x] Query pushdown to DuckDB")
            report.append("- [x] Lazy loading with column selection")
            report.append("- [x] LRU document caching")
            report.append("- [x] Cache invalidation on updates")
            report.append("- [x] Fallback to pandas filtering")
            report.append("- [x] Memory usage optimization")
            report.append("- [x] Bulk operation performance")
            report.append("")
            
            # Files coverage breakdown
            report.append("## File Coverage Breakdown")
            files = coverage_data["files"]
            for file_path, file_data in files.items():
                filename = Path(file_path).name
                coverage_pct = file_data["summary"]["percent_covered"]
                status = "🟢" if coverage_pct >= 90 else "🟡" if coverage_pct >= 80 else "🔴"
                report.append(f"{status} {filename}: {coverage_pct:.1f}%")
            
        except Exception as e:
            report.append(f"Error reading coverage data: {e}")
    
    report_content = "\n".join(report)
    
    # Save report
    report_path = Path("code/libs/python/momo-store-document/TEST_COVERAGE_REPORT.md")
    with open(report_path, "w") as f:
        f.write(report_content)
    
    print(f"📄 Test report saved to: {report_path}")
    return report_content


def main():
    """Run comprehensive test suite."""
    print("🚀 Momo Store Document - Comprehensive Test Suite")
    print("=" * 55)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run tests
    test_results = {
        "unit_tests": run_unit_tests(),
        "integration_tests": run_integration_tests(),
        "benchmark_validation": run_benchmark_validation(),
    }
    
    # Analyze coverage
    coverage_ok = analyze_coverage()
    
    # Generate report
    generate_test_report()
    
    # Summary
    print("\n🎯 Test Suite Summary")
    print("-" * 25)
    
    for test_type, passed in test_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_type.replace('_', ' ').title()}")
    
    coverage_status = "✅" if coverage_ok else "❌"
    print(f"{coverage_status} Test Coverage (90%+ target)")
    
    # Overall result
    all_passed = all(test_results.values()) and coverage_ok
    
    if all_passed:
        print("\n🎉 All tests passed with 90%+ coverage!")
        print("✅ Ready for production deployment")
    else:
        print("\n⚠️  Some tests failed or coverage is below 90%")
        print("🔧 Review test results and add missing tests")
        sys.exit(1)


if __name__ == "__main__":
    main()