"""
Performance benchmarks for momo-cmd command routing.
"""

import statistics
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from momo_cmd.cli import mo
from momo_cmd.context import WorkspaceContext
from momo_cmd.router import ContextAwareCommandRouter


class BenchmarkSuite:
    """Performance benchmark suite for momo-cmd."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.results = {}

    def run_benchmark(self, name: str, func, iterations: int = 100):
        """Run a benchmark function multiple times and collect statistics."""
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        self.results[name] = {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "iterations": iterations,
        }

        print(f"\n{name}:")
        print(f"  Mean: {self.results[name]['mean'] * 1000:.2f}ms")
        print(f"  Median: {self.results[name]['median'] * 1000:.2f}ms")
        print(f"  StdDev: {self.results[name]['stdev'] * 1000:.2f}ms")
        print(f"  Min: {self.results[name]['min'] * 1000:.2f}ms")
        print(f"  Max: {self.results[name]['max'] * 1000:.2f}ms")

        return self.results[name]

    def create_test_workspace(self):
        """Create test workspace structure."""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create workspace markers
        (workspace / "nx.json").write_text('{"version": 3}')
        (workspace / "CLAUDE.md").write_text("# Test Workspace")
        (workspace / "package.json").write_text('{"name": "test"}')

        # Create multiple modules
        for i in range(10):
            module_dir = workspace / "code" / "libs" / "python" / f"module-{i:02d}"
            module_dir.mkdir(parents=True)

            (module_dir / "pyproject.toml").write_text(f"""
[project]
name = "module-{i:02d}"
version = "1.0.0"
""")

            (module_dir / "project.json").write_text("""
{
    "targets": {
        "test-fast": {"command": "pytest tests/unit"},
        "format": {"command": "ruff format ."},
        "lint": {"command": "ruff check ."},
        "typecheck": {"command": "pyright"}
    }
}
""")

        return workspace


def benchmark_context_detection():
    """Benchmark workspace context detection performance."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()

    def detect_context():
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            context = WorkspaceContext()
            assert context.workspace_root == workspace

    suite.run_benchmark("Context Detection", detect_context, iterations=50)

    def detect_module_context():
        module_dir = workspace / "code" / "libs" / "python" / "module-01"
        with patch("momo_cmd.context.Path.cwd", return_value=module_dir):
            context = WorkspaceContext()
            assert context.current_module == "module-01"

    suite.run_benchmark(
        "Module Context Detection", detect_module_context, iterations=50
    )

    return suite.results


def benchmark_command_classification():
    """Benchmark command classification performance."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()

    with patch("momo_cmd.context.Path.cwd", return_value=workspace):
        router = ContextAwareCommandRouter()

    def classify_module_command():
        strategy = router._classify_command(["test-fast", "module-01"])
        assert strategy is not None

    def classify_file_command():
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "is_file", return_value=True):
                strategy = router._classify_command(["script.py", "arg1"])
                assert strategy is not None

    def classify_passthrough_command():
        strategy = router._classify_command(["git", "status"])
        assert strategy is not None

    suite.run_benchmark(
        "Module Command Classification", classify_module_command, iterations=200
    )
    suite.run_benchmark(
        "File Command Classification", classify_file_command, iterations=200
    )
    suite.run_benchmark(
        "Passthrough Command Classification",
        classify_passthrough_command,
        iterations=200,
    )

    return suite.results


def benchmark_command_execution():
    """Benchmark command execution performance (dry run)."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()

    with patch("momo_cmd.context.Path.cwd", return_value=workspace):
        router = ContextAwareCommandRouter(dry_run=True)

    def execute_module_command():
        result = router.route_and_execute(["test-fast", "module-01"])
        assert result is True

    def execute_status_command():
        result = router.route_and_execute(["status"])
        assert result is True

    def execute_passthrough_command():
        result = router.route_and_execute(["git", "status"])
        assert result is True

    suite.run_benchmark(
        "Module Command Execution (dry run)", execute_module_command, iterations=100
    )
    suite.run_benchmark(
        "Status Command Execution", execute_status_command, iterations=100
    )
    suite.run_benchmark(
        "Passthrough Command Execution (dry run)",
        execute_passthrough_command,
        iterations=100,
    )

    return suite.results


def benchmark_cli_interface():
    """Benchmark CLI interface performance."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()
    runner = CliRunner()

    def cli_help_command():
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            result = runner.invoke(mo, ["--help"])
            assert result.exit_code == 0

    def cli_status_command():
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            result = runner.invoke(mo, ["status"])
            assert result.exit_code == 0

    def cli_context_command():
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            result = runner.invoke(mo, ["--context"])
            assert result.exit_code == 0

    def cli_dry_run_command():
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            result = runner.invoke(mo, ["--dry-run", "test", "module-01"])
            assert result.exit_code == 0

    suite.run_benchmark("CLI Help Command", cli_help_command, iterations=50)
    suite.run_benchmark("CLI Status Command", cli_status_command, iterations=50)
    suite.run_benchmark("CLI Context Command", cli_context_command, iterations=50)
    suite.run_benchmark("CLI Dry Run Command", cli_dry_run_command, iterations=50)

    return suite.results


def benchmark_module_info_caching():
    """Benchmark module info caching performance."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()

    with patch("momo_cmd.context.Path.cwd", return_value=workspace):
        context = WorkspaceContext()

    def first_module_info_access():
        info = context.get_module_info("module-01")
        assert info is not None
        assert info.name == "module-01"

    def cached_module_info_access():
        info = context.get_module_info("module-01")
        assert info is not None
        assert info.name == "module-01"

    # First access (cold cache)
    suite.run_benchmark(
        "Module Info First Access", first_module_info_access, iterations=50
    )

    # Subsequent accesses (warm cache)
    suite.run_benchmark(
        "Module Info Cached Access", cached_module_info_access, iterations=200
    )

    return suite.results


def benchmark_idea_workflow():
    """Benchmark idea workflow operations."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()

    # Create ideas directory
    ideas_dir = workspace / "code" / "libs" / "python" / "momo-graph" / "ideas"
    ideas_dir.mkdir(parents=True)

    from momo_cmd.idea_workflow import IdeaManager

    manager = IdeaManager(ideas_location=ideas_dir)

    def get_next_idea_number():
        number = manager._get_next_idea_number()
        assert isinstance(number, int)

    def slugify_topic():
        slug = manager._slugify("Test Authentication System")
        assert slug == "test-authentication-system"

    def create_idea_structure():
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            idea_id = manager.create_idea("Performance Test Idea")
            assert idea_id is not None

    suite.run_benchmark("Get Next Idea Number", get_next_idea_number, iterations=200)
    suite.run_benchmark("Slugify Topic", slugify_topic, iterations=200)
    suite.run_benchmark("Create Idea Structure", create_idea_structure, iterations=10)

    return suite.results


def benchmark_large_workspace():
    """Benchmark performance with large workspace (many modules)."""
    suite = BenchmarkSuite()

    # Create large workspace
    temp_dir = tempfile.mkdtemp()
    workspace = Path(temp_dir)

    (workspace / "nx.json").write_text('{"version": 3}')
    (workspace / "CLAUDE.md").write_text("# Large Workspace")

    # Create 50 modules
    for i in range(50):
        module_dir = workspace / "code" / "libs" / "python" / f"large-module-{i:03d}"
        module_dir.mkdir(parents=True)
        (module_dir / "pyproject.toml").write_text(
            f'[project]\nname = "large-module-{i:03d}"'
        )

    def detect_large_workspace_context():
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            context = WorkspaceContext()
            assert context.workspace_root == workspace

    def status_in_large_workspace():
        runner = CliRunner()
        with patch("momo_cmd.context.Path.cwd", return_value=workspace):
            result = runner.invoke(mo, ["status"])
            assert result.exit_code == 0

    suite.run_benchmark(
        "Large Workspace Context Detection",
        detect_large_workspace_context,
        iterations=20,
    )
    suite.run_benchmark(
        "Status in Large Workspace", status_in_large_workspace, iterations=20
    )

    return suite.results


def benchmark_error_handling():
    """Benchmark error handling performance."""
    suite = BenchmarkSuite()
    workspace = suite.create_test_workspace()

    with patch("momo_cmd.context.Path.cwd", return_value=workspace):
        router = ContextAwareCommandRouter()

    def handle_invalid_module():
        result = router.route_and_execute(["test", "nonexistent-module"])
        assert result is False

    def handle_invalid_command():
        result = router.route_and_execute(["completely-unknown-command"])
        assert result is False

    def handle_file_not_found():
        result = router.route_and_execute(["nonexistent-file.py"])
        assert result is False

    suite.run_benchmark("Invalid Module Handling", handle_invalid_module, iterations=50)
    suite.run_benchmark(
        "Invalid Command Handling", handle_invalid_command, iterations=50
    )
    suite.run_benchmark("File Not Found Handling", handle_file_not_found, iterations=50)

    return suite.results


def run_all_benchmarks():
    """Run all performance benchmarks."""
    print("=" * 60)
    print("MOMO-CMD PERFORMANCE BENCHMARKS")
    print("=" * 60)

    all_results = {}

    print("\n" + "=" * 40)
    print("CONTEXT DETECTION BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_context_detection())

    print("\n" + "=" * 40)
    print("COMMAND CLASSIFICATION BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_command_classification())

    print("\n" + "=" * 40)
    print("COMMAND EXECUTION BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_command_execution())

    print("\n" + "=" * 40)
    print("CLI INTERFACE BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_cli_interface())

    print("\n" + "=" * 40)
    print("MODULE INFO CACHING BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_module_info_caching())

    print("\n" + "=" * 40)
    print("IDEA WORKFLOW BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_idea_workflow())

    print("\n" + "=" * 40)
    print("LARGE WORKSPACE BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_large_workspace())

    print("\n" + "=" * 40)
    print("ERROR HANDLING BENCHMARKS")
    print("=" * 40)
    all_results.update(benchmark_error_handling())

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    # Show summary of key metrics
    key_metrics = [
        "Context Detection",
        "Module Command Classification",
        "CLI Status Command",
        "Module Info Cached Access",
    ]

    for metric in key_metrics:
        if metric in all_results:
            result = all_results[metric]
            print(f"{metric}: {result['mean'] * 1000:.2f}ms avg")

    # Performance targets
    print("\nPerformance Targets:")
    print(
        "- Context Detection: < 50ms ✓"
        if all_results.get("Context Detection", {}).get("mean", 1) < 0.05
        else "- Context Detection: < 50ms ✗"
    )
    print(
        "- Command Classification: < 5ms ✓"
        if all_results.get("Module Command Classification", {}).get("mean", 1) < 0.005
        else "- Command Classification: < 5ms ✗"
    )
    print(
        "- CLI Commands: < 100ms ✓"
        if all_results.get("CLI Status Command", {}).get("mean", 1) < 0.1
        else "- CLI Commands: < 100ms ✗"
    )
    print(
        "- Cached Access: < 1ms ✓"
        if all_results.get("Module Info Cached Access", {}).get("mean", 1) < 0.001
        else "- Cached Access: < 1ms ✗"
    )

    return all_results


if __name__ == "__main__":
    run_all_benchmarks()
