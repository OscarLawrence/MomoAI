"""
Performance benchmarks for momo-agent framework.

This module provides comprehensive performance testing for the agent framework,
measuring execution times, memory usage, and scalability characteristics.
"""

import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any

from momo_workflow.types import StepStatus

from momo_agent import (
    AgentExecutionContext,
    AgentTaskType,
    AgentWorkflowEngine,
    BaseAgentTask,
    BaseAgentWorkflow,
    TaskPriority,
)


class BenchmarkTask(BaseAgentTask):
    """Benchmarkable test task with configurable workload."""

    def __init__(
        self,
        task_id: str,
        workload_duration: float = 0.1,
        should_fail: bool = False,
    ):
        super().__init__(
            task_id=task_id,
            description=f"Benchmark task with {workload_duration}s workload",
            task_type=AgentTaskType.SIMPLE,
            priority=TaskPriority.NORMAL,
            estimated_duration=workload_duration,
            is_reversible=True,
        )
        self._workload_duration = workload_duration
        self._should_fail = should_fail

    async def execute(self, context):
        """Execute benchmark task with controlled workload."""
        start_time = time.time()

        # Simulate workload
        await asyncio.sleep(self._workload_duration)

        if self._should_fail:
            return self._create_result(
                status=StepStatus.FAILED,
                start_time=start_time,
                error=Exception("Intentional benchmark failure"),
            )

        return self._create_result(
            status=StepStatus.SUCCESS,
            start_time=start_time,
            outputs={
                "workload_duration": self._workload_duration,
                "task_id": self.metadata.task_id,
            },
            rollback_data={"task_completed": True},
        )

    async def rollback(self, context, result):
        """Simulate rollback operation."""
        await asyncio.sleep(0.01)  # Small rollback overhead


class PerformanceBenchmarks:
    """Performance benchmark suite for momo-agent framework."""

    def __init__(self):
        self.results: dict[str, Any] = {
            "timestamp": time.time(),
            "benchmarks": {},
        }

    async def run_all_benchmarks(self) -> dict[str, Any]:
        """Run complete benchmark suite."""
        print("Running momo-agent performance benchmarks...")

        # Execution performance
        await self._benchmark_task_execution()
        await self._benchmark_workflow_scaling()
        await self._benchmark_workflow_rollback()

        # Framework overhead
        await self._benchmark_framework_overhead()

        # Error handling performance
        await self._benchmark_error_handling()

        self.results["summary"] = self._generate_summary()
        return self.results

    async def _benchmark_task_execution(self):
        """Benchmark individual task execution performance."""
        print("  Benchmarking task execution...")

        task_durations = []
        context = AgentExecutionContext(session_id="benchmark-session")

        # Run multiple iterations for statistical significance
        iterations = 50
        for i in range(iterations):
            task = BenchmarkTask(f"task_{i}", workload_duration=0.05)

            start_time = time.time()
            result = await task.execute(context)
            end_time = time.time()

            assert result.success, "Benchmark task should succeed"
            task_durations.append(end_time - start_time)

        self.results["benchmarks"]["task_execution"] = {
            "iterations": iterations,
            "mean_duration": statistics.mean(task_durations),
            "median_duration": statistics.median(task_durations),
            "std_deviation": statistics.stdev(task_durations),
            "min_duration": min(task_durations),
            "max_duration": max(task_durations),
        }

    async def _benchmark_workflow_scaling(self):
        """Benchmark workflow performance with increasing task counts."""
        print("  Benchmarking workflow scaling...")

        scaling_results = {}
        task_counts = [1, 5, 10, 25, 50]

        for task_count in task_counts:
            print(f"    Testing {task_count} tasks...")
            durations = []

            # Run multiple iterations for each scale
            for iteration in range(5):
                tasks = [
                    BenchmarkTask(f"scale_task_{i}", workload_duration=0.01)
                    for i in range(task_count)
                ]

                workflow = BaseAgentWorkflow(
                    workflow_id=f"scale_workflow_{task_count}_{iteration}",
                    name=f"Scaling Test {task_count}",
                    tasks=tasks,
                )

                context = AgentExecutionContext(
                    session_id=f"scale-benchmark-{task_count}-{iteration}"
                )

                engine = AgentWorkflowEngine()
                start_time = time.time()
                result = await engine.execute_workflow(workflow, context)
                end_time = time.time()

                assert result.status == "SUCCESS", "Scaling workflow should succeed"
                durations.append(end_time - start_time)

            scaling_results[str(task_count)] = {
                "mean_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "tasks_per_second": task_count / statistics.mean(durations),
            }

        self.results["benchmarks"]["workflow_scaling"] = scaling_results

    async def _benchmark_workflow_rollback(self):
        """Benchmark workflow rollback performance."""
        print("  Benchmarking rollback performance...")

        rollback_durations = []
        iterations = 10

        for i in range(iterations):
            tasks = [
                BenchmarkTask(f"rollback_task_{j}", workload_duration=0.02)
                for j in range(5)  # 5 successful tasks
            ]
            # Add a failing task to trigger rollback
            tasks.append(BenchmarkTask("failing_task", should_fail=True))

            workflow = BaseAgentWorkflow(
                workflow_id=f"rollback_workflow_{i}",
                name=f"Rollback Test {i}",
                tasks=tasks,
            )

            context = AgentExecutionContext(session_id=f"rollback-benchmark-{i}")

            engine = AgentWorkflowEngine()
            start_time = time.time()
            result = await engine.execute_workflow(
                workflow, context, rollback_on_failure=True
            )
            end_time = time.time()

            assert result.status == "FAILED", "Rollback workflow should fail"
            rollback_durations.append(end_time - start_time)

        self.results["benchmarks"]["rollback_performance"] = {
            "iterations": iterations,
            "mean_duration": statistics.mean(rollback_durations),
            "median_duration": statistics.median(rollback_durations),
            "std_deviation": statistics.stdev(rollback_durations),
        }

    async def _benchmark_framework_overhead(self):
        """Benchmark framework overhead vs raw task execution."""
        print("  Benchmarking framework overhead...")

        # Measure raw async task execution
        raw_durations = []
        iterations = 50

        for i in range(iterations):
            start_time = time.time()
            await asyncio.sleep(0.01)  # Simulate work
            end_time = time.time()
            raw_durations.append(end_time - start_time)

        # Measure framework-wrapped task execution
        framework_durations = []
        context = AgentExecutionContext(session_id="overhead-benchmark")

        for i in range(iterations):
            task = BenchmarkTask(f"overhead_task_{i}", workload_duration=0.01)

            start_time = time.time()
            result = await task.execute(context)
            end_time = time.time()

            assert result.success, "Overhead benchmark task should succeed"
            framework_durations.append(end_time - start_time)

        raw_mean = statistics.mean(raw_durations)
        framework_mean = statistics.mean(framework_durations)
        overhead_percentage = ((framework_mean - raw_mean) / raw_mean) * 100

        self.results["benchmarks"]["framework_overhead"] = {
            "raw_mean_duration": raw_mean,
            "framework_mean_duration": framework_mean,
            "overhead_seconds": framework_mean - raw_mean,
            "overhead_percentage": overhead_percentage,
            "iterations": iterations,
        }

    async def _benchmark_error_handling(self):
        """Benchmark error handling and recovery performance."""
        print("  Benchmarking error handling...")

        error_durations = []
        success_durations = []
        iterations = 25

        context = AgentExecutionContext(session_id="error-benchmark")

        # Benchmark successful tasks
        for i in range(iterations):
            task = BenchmarkTask(f"success_task_{i}", workload_duration=0.01)
            start_time = time.time()
            result = await task.execute(context)
            end_time = time.time()

            assert result.success
            success_durations.append(end_time - start_time)

        # Benchmark failing tasks
        for i in range(iterations):
            task = BenchmarkTask(f"error_task_{i}", should_fail=True)
            start_time = time.time()
            result = await task.execute(context)
            end_time = time.time()

            assert not result.success
            error_durations.append(end_time - start_time)

        self.results["benchmarks"]["error_handling"] = {
            "success_mean_duration": statistics.mean(success_durations),
            "error_mean_duration": statistics.mean(error_durations),
            "error_overhead": statistics.mean(error_durations)
            - statistics.mean(success_durations),
            "iterations": iterations,
        }

    def _generate_summary(self) -> dict[str, Any]:
        """Generate benchmark summary with key metrics."""
        benchmarks = self.results["benchmarks"]

        return {
            "framework_overhead_percentage": benchmarks["framework_overhead"][
                "overhead_percentage"
            ],
            "max_tasks_per_second": max(
                result["tasks_per_second"]
                for result in benchmarks["workflow_scaling"].values()
            ),
            "task_execution_p95": self._calculate_p95(benchmarks["task_execution"]),
            "rollback_overhead_factor": (
                benchmarks["rollback_performance"]["mean_duration"]
                / benchmarks["task_execution"]["mean_duration"]
            ),
            "error_handling_overhead_ms": benchmarks["error_handling"]["error_overhead"]
            * 1000,
        }

    def _calculate_p95(self, execution_data: dict[str, float]) -> float:
        """Calculate 95th percentile from execution statistics."""
        # Approximate P95 using mean + 1.65 * std_dev (assumes normal distribution)
        return execution_data["mean_duration"] + (
            1.65 * execution_data["std_deviation"]
        )

    def save_results(self, output_path: Path = None) -> Path:
        """Save benchmark results to JSON file."""
        if output_path is None:
            output_path = Path("benchmark_results.json")

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"Benchmark results saved to {output_path}")
        return output_path

    def print_summary(self):
        """Print benchmark summary to console."""
        summary = self.results["summary"]

        print("\n=== momo-agent Performance Benchmark Results ===")
        print(f"Framework overhead: {summary['framework_overhead_percentage']:.2f}%")
        print(f"Maximum throughput: {summary['max_tasks_per_second']:.1f} tasks/second")
        print(f"Task execution P95: {summary['task_execution_p95'] * 1000:.2f}ms")
        print(f"Rollback overhead factor: {summary['rollback_overhead_factor']:.2f}x")
        print(f"Error handling overhead: {summary['error_handling_overhead_ms']:.2f}ms")
        print("=" * 50)


async def main():
    """Run benchmark suite."""
    benchmarks = PerformanceBenchmarks()
    results = await benchmarks.run_all_benchmarks()

    benchmarks.print_summary()
    benchmarks.save_results()

    return results


if __name__ == "__main__":
    asyncio.run(main())
