"""
Basic usage examples for momo-agent framework.

This script demonstrates the fundamental capabilities of the momo-agent
framework including task creation, workflow execution, and command integration.
"""

import asyncio
import tempfile
import time
from pathlib import Path

from momo_workflow.types import StepStatus

from momo_agent import (
    AgentExecutionContext,
    AgentTaskType,
    AgentWorkflowEngine,
    BaseAgentTask,
    BaseAgentWorkflow,
    TaskPriority,
)
from momo_agent.main import execute_command_workflow


class FileWriteTask(BaseAgentTask):
    """Example task that writes content to a file."""

    def __init__(self, task_id: str, file_path: Path, content: str):
        super().__init__(
            task_id=task_id,
            description=f"Write content to {file_path}",
            task_type=AgentTaskType.SIMPLE,
            priority=TaskPriority.NORMAL,
        )
        self._file_path = file_path
        self._content = content

    async def execute(self, context):
        """Write content to file."""
        start_time = time.time()

        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(self._content)

            print(f"✅ Created file: {self._file_path}")

            return self._create_result(
                status=StepStatus.SUCCESS,
                start_time=start_time,
                outputs={
                    "file_path": str(self._file_path),
                    "content_length": len(self._content),
                },
            )
        except Exception as e:
            return self._create_result(
                status=StepStatus.FAILED,
                start_time=start_time,
                error=e,
            )


async def example_basic_workflow():
    """Demonstrate basic workflow execution."""
    print("=== Basic Workflow Example ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create tasks
        tasks = [
            FileWriteTask("write_file_1", temp_path / "file1.txt", "Hello, World!"),
            FileWriteTask(
                "write_file_2", temp_path / "file2.txt", "momo-agent is working!"
            ),
        ]

        # Create workflow
        workflow = BaseAgentWorkflow(
            workflow_id="basic-example",
            name="Basic File Writing Workflow",
            tasks=tasks,
        )

        # Create execution context
        context = AgentExecutionContext(
            session_id="basic-example-session",
            working_directory=temp_path,
        )

        # Execute workflow
        engine = AgentWorkflowEngine()
        result = await engine.execute_workflow(workflow, context)

        # Display results
        print(f"Workflow status: {result.status}")
        print(f"Completed tasks: {result.completed_tasks}/{result.total_tasks}")
        print(f"Execution time: {result.overall_metrics.duration_seconds:.2f}s")

        for task_result in result.task_results:
            print(f"  Task {task_result.task_id}: {task_result.status.value}")

        return result


async def example_command_workflow():
    """Demonstrate command-based workflow execution."""
    print("\n=== Command Workflow Example ===")

    commands = [
        "echo 'Starting momo-agent demo'",
        "echo 'Current date:'",
        "date",
    ]

    try:
        result = await execute_command_workflow(
            workflow_name="command_demo",
            commands=commands,
        )

        print(f"Command workflow status: {result.status}")
        print(f"Executed {result.total_tasks} commands")

        for i, task_result in enumerate(result.task_results):
            print(f"  Command {i + 1}: {task_result.status.value}")
            if task_result.outputs:
                print(f"    Output: {task_result.outputs}")

        return result

    except Exception as e:
        print(f"Command workflow failed (expected in some environments): {e}")
        return None


async def example_error_handling():
    """Demonstrate error handling and rollback."""
    print("\n=== Error Handling Example ===")

    class FailingTask(BaseAgentTask):
        """Task that intentionally fails to demonstrate error handling."""

        def __init__(self, task_id: str):
            super().__init__(task_id, "Task that fails", is_reversible=True)

        async def execute(self, context):
            start_time = time.time()
            return self._create_result(
                status=StepStatus.FAILED,
                start_time=start_time,
                error=Exception("Intentional failure for demo"),
                rollback_data={"needs_cleanup": True},
            )

        async def rollback(self, context, result):
            print(f"  🔄 Rolling back task: {self.metadata.task_id}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create workflow with failing task
        tasks = [
            FileWriteTask(
                "success_task", temp_path / "success.txt", "This will succeed"
            ),
            FailingTask("failing_task"),
        ]

        workflow = BaseAgentWorkflow(
            workflow_id="error-example",
            name="Error Handling Workflow",
            tasks=tasks,
        )

        context = AgentExecutionContext(
            session_id="error-example-session",
            working_directory=temp_path,
        )

        engine = AgentWorkflowEngine()
        result = await engine.execute_workflow(
            workflow, context, rollback_on_failure=True
        )

        print(f"Workflow status: {result.status}")
        print(f"Tasks completed: {result.completed_tasks}")
        print(f"Tasks failed: {result.failed_tasks}")
        print(f"Rollback points: {len(result.rollback_points)}")

        return result


async def example_performance_tracking():
    """Demonstrate performance tracking capabilities."""
    print("\n=== Performance Tracking Example ===")

    class InstrumentedTask(BaseAgentTask):
        """Task with detailed performance tracking."""

        def __init__(self, task_id: str, work_duration: float):
            super().__init__(
                task_id=task_id,
                description=f"Instrumented task ({work_duration}s)",
                estimated_duration=work_duration,
            )
            self._work_duration = work_duration

        async def execute(self, context):
            start_time = time.time()

            # Simulate work with progress tracking
            await asyncio.sleep(self._work_duration)

            # Update context performance tracking
            context.update_performance(
                f"{self.metadata.task_id}_duration", self._work_duration
            )

            return self._create_result(
                status=StepStatus.SUCCESS,
                start_time=start_time,
                outputs={"simulated_work_duration": self._work_duration},
            )

    # Create workflow with varying task durations
    tasks = [
        InstrumentedTask("fast_task", 0.1),
        InstrumentedTask("medium_task", 0.2),
        InstrumentedTask("slow_task", 0.3),
    ]

    workflow = BaseAgentWorkflow(
        workflow_id="performance-example",
        name="Performance Tracking Workflow",
        tasks=tasks,
    )

    context = AgentExecutionContext(session_id="performance-example-session")

    engine = AgentWorkflowEngine()
    result = await engine.execute_workflow(workflow, context)

    print(f"Workflow completed in {result.overall_metrics.duration_seconds:.2f}s")
    print("Task performance metrics:")

    for task_result in result.task_results:
        duration = task_result.metrics.duration_seconds
        print(f"  {task_result.task_id}: {duration:.3f}s")

    print("Context performance tracking:")
    for metric, value in context.performance_tracking.items():
        print(f"  {metric}: {value:.3f}s")

    # Engine summary
    summary = engine.get_execution_summary()
    print("Engine statistics:")
    print(f"  Average task duration: {summary['average_duration']:.3f}s")
    print(
        f"  Success rate: {summary['successful_tasks']}/{summary['total_executions']}"
    )

    return result


async def main():
    """Run all examples."""
    print("🚀 momo-agent Framework Examples")
    print("=" * 40)

    # Run examples

    try:
        await example_basic_workflow()
        await example_command_workflow()
        await example_error_handling()
        await example_performance_tracking()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
