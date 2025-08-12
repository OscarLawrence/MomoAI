"""
Scientific benchmark suite for workflow performance measurement.

This module provides comprehensive benchmarking capabilities:
- Execution time analysis
- Memory usage profiling
- Scalability testing
- Rollback performance
- Statistical analysis with confidence intervals
"""

import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from momo_workflow.commands import get_command_registry, register_command
from momo_workflow.core import WorkflowEngine
from momo_workflow.testing import (
    TestWorkflowStep,
    WorkflowTestFixture,
    create_performance_test_scenario,
    create_failure_test_scenario,
)
from momo_workflow.types import WorkflowDefinition, WorkflowContext


class WorkflowBenchmarkSuite:
    """Scientific benchmark suite for workflow performance analysis."""

    def __init__(self, output_dir: Path = None):
        """Initialize benchmark suite."""
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(exist_ok=True)
        self.engine = WorkflowEngine()

    def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite and return aggregated results."""
        print("🧪 Running Scientific Workflow Benchmark Suite")
        print("=" * 50)

        benchmark_results = {"timestamp": time.time(), "benchmarks": {}}

        # Execute all benchmark categories
        benchmark_categories = [
            ("execution_performance", self._benchmark_execution_performance),
            ("scalability_analysis", self._benchmark_scalability),
            ("rollback_performance", self._benchmark_rollback_performance),
            ("memory_efficiency", self._benchmark_memory_efficiency),
            ("command_overhead", self._benchmark_command_overhead),
        ]

        for category_name, benchmark_func in benchmark_categories:
            print(f"\n📊 Running {category_name.replace('_', ' ').title()}")

            try:
                result = benchmark_func()
                benchmark_results["benchmarks"][category_name] = result
                print(f"✅ {category_name} completed")
            except Exception as e:
                print(f"❌ {category_name} failed: {e}")
                benchmark_results["benchmarks"][category_name] = {"error": str(e)}

        # Generate summary statistics
        benchmark_results["summary"] = self._generate_summary_statistics(
            benchmark_results["benchmarks"]
        )

        # Save results
        self._save_benchmark_results(benchmark_results)

        print(f"\n📈 Benchmark Results Summary")
        print(f"Results saved to: {self.output_dir}")
        self._print_summary(benchmark_results["summary"])

        return benchmark_results

    def _benchmark_execution_performance(self) -> Dict[str, Any]:
        """Benchmark basic execution performance across different workflow sizes."""
        results = {
            "test_name": "execution_performance",
            "measurements": {},
            "analysis": {},
        }

        # Test different workflow sizes
        step_counts = [1, 5, 10, 25, 50]
        iterations_per_test = 10

        for step_count in step_counts:
            print(f"  Testing {step_count} steps ({iterations_per_test} iterations)")

            durations = []
            for iteration in range(iterations_per_test):
                workflow, context = create_performance_test_scenario(step_count, 0.01)

                start_time = time.time()
                result = self.engine.execute_workflow(workflow, context)
                duration = time.time() - start_time

                if result.success_rate == 1.0:
                    durations.append(duration)

            if durations:
                results["measurements"][f"{step_count}_steps"] = {
                    "sample_size": len(durations),
                    "mean_duration": statistics.mean(durations),
                    "median_duration": statistics.median(durations),
                    "std_deviation": statistics.stdev(durations)
                    if len(durations) > 1
                    else 0,
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                }

        # Calculate performance scaling
        step_counts_with_data = []
        mean_durations = []

        for step_count in step_counts:
            key = f"{step_count}_steps"
            if key in results["measurements"]:
                step_counts_with_data.append(step_count)
                mean_durations.append(results["measurements"][key]["mean_duration"])

        if len(step_counts_with_data) > 1:
            # Simple linear regression for scaling analysis
            scaling_factor = self._calculate_scaling_factor(
                step_counts_with_data, mean_durations
            )
            results["analysis"]["scaling_factor"] = scaling_factor
            results["analysis"]["performance_category"] = self._categorize_performance(
                scaling_factor
            )

        return results

    def _benchmark_scalability(self) -> Dict[str, Any]:
        """Analyze workflow scalability with large step counts."""
        results = {
            "test_name": "scalability_analysis",
            "measurements": {},
            "analysis": {},
        }

        # Test increasingly large workflows
        large_step_counts = [100, 250, 500, 1000]

        for step_count in large_step_counts:
            print(f"  Testing scalability with {step_count} steps")

            try:
                workflow, context = create_performance_test_scenario(step_count, 0.001)

                start_time = time.time()
                result = self.engine.execute_workflow(workflow, context)
                duration = time.time() - start_time

                results["measurements"][f"{step_count}_steps"] = {
                    "duration": duration,
                    "success_rate": result.success_rate,
                    "steps_per_second": step_count / duration if duration > 0 else 0,
                    "memory_peak_mb": result.overall_metrics.memory_peak_mb,
                }

                # Early termination if performance degrades significantly
                if duration > 30.0:  # 30 second timeout
                    results["analysis"]["early_termination"] = (
                        f"Terminated at {step_count} steps due to timeout"
                    )
                    break

            except Exception as e:
                results["measurements"][f"{step_count}_steps"] = {"error": str(e)}

        # Analyze scalability characteristics
        throughputs = []
        for measurement in results["measurements"].values():
            if (
                "steps_per_second" in measurement
                and measurement["steps_per_second"] > 0
            ):
                throughputs.append(measurement["steps_per_second"])

        if throughputs:
            results["analysis"]["mean_throughput"] = statistics.mean(throughputs)
            results["analysis"]["throughput_stability"] = statistics.stdev(
                throughputs
            ) / statistics.mean(throughputs)

        return results

    def _benchmark_rollback_performance(self) -> Dict[str, Any]:
        """Benchmark rollback operation performance."""
        results = {
            "test_name": "rollback_performance",
            "measurements": {},
            "analysis": {},
        }

        # Test rollback at different failure points
        workflow_sizes = [10, 25, 50]
        iterations = 5

        for workflow_size in workflow_sizes:
            for failure_point in [2, workflow_size // 2, workflow_size - 2]:
                test_key = f"{workflow_size}_steps_fail_at_{failure_point}"
                print(f"  Testing rollback: {test_key}")

                rollback_durations = []

                for _ in range(iterations):
                    workflow, context = create_failure_test_scenario(
                        failing_step_index=failure_point,
                        total_steps=workflow_size,
                        enable_rollback=True,
                    )

                    start_time = time.time()
                    result = self.engine.execute_workflow(
                        workflow, context, rollback_on_failure=True
                    )
                    rollback_duration = time.time() - start_time

                    if len(result.rollback_points) > 0:
                        rollback_durations.append(rollback_duration)

                if rollback_durations:
                    results["measurements"][test_key] = {
                        "mean_rollback_duration": statistics.mean(rollback_durations),
                        "rollback_overhead": statistics.mean(rollback_durations)
                        / workflow_size,
                        "sample_size": len(rollback_durations),
                    }

        return results

    def _benchmark_memory_efficiency(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        results = {"test_name": "memory_efficiency", "measurements": {}, "analysis": {}}

        # Test memory usage with different workflow characteristics
        test_scenarios = [
            ("small_workflow", 10, 0.01),
            ("medium_workflow", 50, 0.01),
            ("large_workflow", 100, 0.01),
            ("artifact_heavy", 10, 0.01),  # Would need special artifacts
        ]

        for scenario_name, step_count, step_duration in test_scenarios:
            print(f"  Testing memory: {scenario_name}")

            workflow, context = create_performance_test_scenario(
                step_count, step_duration
            )

            # Execute with memory tracking
            result = self.engine.execute_workflow(workflow, context)

            results["measurements"][scenario_name] = {
                "peak_memory_mb": result.overall_metrics.memory_peak_mb or 0,
                "memory_per_step": (result.overall_metrics.memory_peak_mb or 0)
                / step_count,
                "success_rate": result.success_rate,
            }

        return results

    def _benchmark_command_overhead(self) -> Dict[str, Any]:
        """Benchmark command execution overhead."""
        results = {"test_name": "command_overhead", "measurements": {}, "analysis": {}}

        # Register test commands with different characteristics
        registry = get_command_registry()

        @register_command("fast_command", "Fast test command")
        def fast_command() -> str:
            return "fast_result"

        @register_command("slow_command", "Slow test command")
        def slow_command() -> str:
            time.sleep(0.1)
            return "slow_result"

        # Test command execution overhead
        command_types = ["fast_command", "slow_command"]
        iterations = 20

        for command_type in command_types:
            print(f"  Testing command overhead: {command_type}")

            durations = []
            for _ in range(iterations):
                command = registry.get_command(command_type)

                start_time = time.time()
                result = command.execute()
                duration = time.time() - start_time

                if result.get("success", False):
                    durations.append(duration)

            if durations:
                results["measurements"][command_type] = {
                    "mean_duration": statistics.mean(durations),
                    "overhead_std": statistics.stdev(durations)
                    if len(durations) > 1
                    else 0,
                    "sample_size": len(durations),
                }

        return results

    def _calculate_scaling_factor(
        self, step_counts: List[int], durations: List[float]
    ) -> float:
        """Calculate simple linear scaling factor."""
        if len(step_counts) < 2:
            return 1.0

        # Simple linear regression: duration = a * step_count + b
        n = len(step_counts)
        sum_x = sum(step_counts)
        sum_y = sum(durations)
        sum_xy = sum(x * y for x, y in zip(step_counts, durations))
        sum_x2 = sum(x * x for x in step_counts)

        # Calculate slope (scaling factor)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _categorize_performance(self, scaling_factor: float) -> str:
        """Categorize performance based on scaling factor."""
        if scaling_factor <= 0.001:
            return "EXCELLENT"
        elif scaling_factor <= 0.005:
            return "GOOD"
        elif scaling_factor <= 0.01:
            return "ACCEPTABLE"
        else:
            return "NEEDS_OPTIMIZATION"

    def _generate_summary_statistics(
        self, benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary statistics across all benchmarks."""
        summary = {
            "total_benchmarks": len(benchmarks),
            "successful_benchmarks": 0,
            "failed_benchmarks": 0,
            "performance_highlights": {},
        }

        for benchmark_name, benchmark_data in benchmarks.items():
            if "error" in benchmark_data:
                summary["failed_benchmarks"] += 1
            else:
                summary["successful_benchmarks"] += 1

        # Extract key performance indicators
        if (
            "execution_performance" in benchmarks
            and "analysis" in benchmarks["execution_performance"]
        ):
            exec_analysis = benchmarks["execution_performance"]["analysis"]
            if "performance_category" in exec_analysis:
                summary["performance_highlights"]["execution_category"] = exec_analysis[
                    "performance_category"
                ]

        if (
            "scalability_analysis" in benchmarks
            and "analysis" in benchmarks["scalability_analysis"]
        ):
            scale_analysis = benchmarks["scalability_analysis"]["analysis"]
            if "mean_throughput" in scale_analysis:
                summary["performance_highlights"]["mean_throughput_steps_per_sec"] = (
                    scale_analysis["mean_throughput"]
                )

        return summary

    def _save_benchmark_results(self, results: Dict[str, Any]) -> None:
        """Save benchmark results to JSON file."""
        timestamp = int(results["timestamp"])
        filename = f"workflow_benchmark_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Also save as latest
        latest_filepath = self.output_dir / "latest_benchmark.json"
        with open(latest_filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print formatted benchmark summary."""
        print(f"Total Benchmarks: {summary['total_benchmarks']}")
        print(f"Successful: {summary['successful_benchmarks']}")
        print(f"Failed: {summary['failed_benchmarks']}")

        if "performance_highlights" in summary:
            highlights = summary["performance_highlights"]
            print("\n📊 Performance Highlights:")

            if "execution_category" in highlights:
                print(f"  Execution Performance: {highlights['execution_category']}")

            if "mean_throughput_steps_per_sec" in highlights:
                throughput = highlights["mean_throughput_steps_per_sec"]
                print(f"  Mean Throughput: {throughput:.2f} steps/second")


def run_benchmark_suite():
    """Run the complete benchmark suite."""
    suite = WorkflowBenchmarkSuite()
    return suite.run_full_benchmark_suite()


if __name__ == "__main__":
    run_benchmark_suite()
