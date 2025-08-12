"""
Scientific testing framework for workflow validation and verification.

This module provides comprehensive testing capabilities for workflows:
- Reproducible test execution
- Performance benchmarking
- Failure scenario testing
- Rollback verification
"""

import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import Mock

from .commands import CommandRegistry, FunctionCommand
from .core import BaseWorkflowStep, WorkflowEngine
from .types import (
    ExecutionMetrics,
    StepResult,
    StepStatus,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStatus,
)


class TestWorkflowStep(BaseWorkflowStep):
    """Test step with configurable behavior for testing scenarios."""

    def __init__(
        self,
        step_id: str,
        description: str = "",
        should_fail: bool = False,
        execution_time: float = 0.1,
        reversible: bool = True,
        artifacts: Optional[List[Path]] = None,
        rollback_action: Optional[callable] = None,
    ):
        """Initialize test step with configurable behavior."""
        super().__init__(step_id, description or f"Test step: {step_id}", reversible)
        self.should_fail = should_fail
        self.execution_time = execution_time
        self.artifacts = artifacts or []
        self.rollback_action = rollback_action
        self._executed = False
        self._rolled_back = False

    def execute(self, context: WorkflowContext) -> StepResult:
        """Execute test step with configurable behavior."""
        start_time = time.time()

        # Simulate execution time
        time.sleep(self.execution_time)

        self._executed = True

        if self.should_fail:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
                error=Exception(f"Intentional failure in test step: {self.step_id}"),
            )

        # Create artifacts if specified
        created_artifacts = []
        for artifact_name in self.artifacts:
            artifact_path = context.working_directory / artifact_name
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(f"Test artifact from {self.step_id}")
            created_artifacts.append(artifact_path)
            context.add_artifact(artifact_path)

        # Store rollback data
        rollback_data = None
        if self.is_reversible:
            rollback_data = {
                "artifacts": created_artifacts,
                "step_id": self.step_id,
                "context_vars": context.variables.copy(),
            }

        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SUCCESS,
            metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
            artifacts=created_artifacts,
            rollback_data=rollback_data,
        )

    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        """Rollback test step changes."""
        if not self.is_reversible:
            raise ValueError(f"Step {self.step_id} is not reversible")

        self._rolled_back = True

        # Execute custom rollback action
        if self.rollback_action:
            self.rollback_action(context, result)

        # Clean up artifacts
        if result.rollback_data and "artifacts" in result.rollback_data:
            for artifact in result.rollback_data["artifacts"]:
                if isinstance(artifact, Path) and artifact.exists():
                    artifact.unlink()

    @property
    def executed(self) -> bool:
        """Check if step was executed."""
        return self._executed

    @property
    def rolled_back(self) -> bool:
        """Check if step was rolled back."""
        return self._rolled_back


class MockCommand:
    """Mock command for testing workflow command execution."""

    def __init__(
        self,
        name: str,
        description: str = "",
        should_fail: bool = False,
        return_value: Any = None,
        execution_time: float = 0.1,
    ):
        """Initialize mock command."""
        self._name = name
        self._description = description or f"Mock command: {name}"
        self.should_fail = should_fail
        self.return_value = return_value
        self.execution_time = execution_time
        self.call_count = 0
        self.call_args = []

    @property
    def name(self) -> str:
        """Command name."""
        return self._name

    @property
    def description(self) -> str:
        """Command description."""
        return self._description

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute mock command."""
        self.call_count += 1
        self.call_args.append(kwargs)

        # Simulate execution time
        time.sleep(self.execution_time)

        if self.should_fail:
            return {"success": False, "error": f"Mock failure in command: {self.name}"}

        return {
            "success": True,
            "result": self.return_value,
            "call_count": self.call_count,
        }

    def validate_args(self, **kwargs) -> bool:
        """Always valid for mock commands."""
        return True


class WorkflowTestFixture:
    """Test fixture for workflow testing with isolated environment."""

    def __init__(self, temp_dir: Optional[Path] = None):
        """Initialize test fixture."""
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
        self.engine = WorkflowEngine()
        self.command_registry = CommandRegistry()
        self._cleanup_paths: List[Path] = []

    def create_test_context(self, **variables) -> WorkflowContext:
        """Create isolated test context."""
        return WorkflowContext(working_directory=self.temp_dir, variables=variables)

    def create_simple_workflow(
        self,
        steps: List[TestWorkflowStep],
        workflow_id: str = "test_workflow",
        **variables,
    ) -> WorkflowDefinition:
        """Create simple test workflow."""
        return WorkflowDefinition(
            workflow_id=workflow_id,
            name=f"Test workflow: {workflow_id}",
            description="Generated test workflow",
            version="1.0.0",
            author="test_framework",
            steps=steps,
            variables=variables,
        )

    def register_mock_command(self, command: MockCommand) -> None:
        """Register mock command for testing."""
        self.command_registry._commands[command.name] = command

    def cleanup(self) -> None:
        """Clean up test resources."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class WorkflowTestCase:
    """Base class for workflow test cases with common assertions."""

    def __init__(self, fixture: WorkflowTestFixture):
        """Initialize test case with fixture."""
        self.fixture = fixture

    def assert_workflow_success(self, result: WorkflowResult) -> None:
        """Assert workflow completed successfully."""
        assert result.status == WorkflowStatus.SUCCESS, (
            f"Workflow failed: {result.status}"
        )
        assert result.success_rate == 1.0, f"Success rate: {result.success_rate}"
        assert all(r.success for r in result.step_results), "Some steps failed"

    def assert_workflow_failure(
        self, result: WorkflowResult, expected_failed_step: Optional[str] = None
    ) -> None:
        """Assert workflow failed as expected."""
        assert result.status in [
            WorkflowStatus.FAILED,
            WorkflowStatus.PARTIALLY_ROLLED_BACK,
            WorkflowStatus.FULLY_ROLLED_BACK,
        ]

        if expected_failed_step:
            failed_steps = [r for r in result.step_results if not r.success]
            assert any(r.step_id == expected_failed_step for r in failed_steps), (
                f"Expected step {expected_failed_step} to fail"
            )

    def assert_step_rollback(self, result: WorkflowResult, step_id: str) -> None:
        """Assert specific step was rolled back."""
        step_result = next(
            (r for r in result.step_results if r.step_id == step_id), None
        )
        assert step_result is not None, f"Step {step_id} not found in results"
        assert step_result.status == StepStatus.ROLLED_BACK, (
            f"Step {step_id} was not rolled back"
        )

    def assert_performance_bounds(
        self,
        result: WorkflowResult,
        max_duration: float,
        max_memory_mb: Optional[float] = None,
    ) -> None:
        """Assert workflow performance is within bounds."""
        assert result.total_duration <= max_duration, (
            f"Workflow took {result.total_duration}s, expected <= {max_duration}s"
        )

        if max_memory_mb is not None:
            peak_memory = result.overall_metrics.memory_peak_mb or 0
            assert peak_memory <= max_memory_mb, (
                f"Peak memory {peak_memory}MB, expected <= {max_memory_mb}MB"
            )


def create_failure_test_scenario(
    failing_step_index: int, total_steps: int = 5, enable_rollback: bool = True
) -> Tuple[WorkflowDefinition, WorkflowContext]:
    """Create test scenario with failure at specific step."""
    fixture = WorkflowTestFixture()

    steps = []
    for i in range(total_steps):
        step = TestWorkflowStep(
            step_id=f"step_{i + 1}",
            description=f"Test step {i + 1}",
            should_fail=(i == failing_step_index),
            execution_time=0.05,
            artifacts=[f"artifact_{i + 1}.txt"] if enable_rollback else [],
        )
        steps.append(step)

    workflow = fixture.create_simple_workflow(steps)
    context = fixture.create_test_context()

    return workflow, context


def create_performance_test_scenario(
    num_steps: int = 10, execution_time_per_step: float = 0.1
) -> Tuple[WorkflowDefinition, WorkflowContext]:
    """Create performance test scenario."""
    fixture = WorkflowTestFixture()

    steps = []
    for i in range(num_steps):
        step = TestWorkflowStep(
            step_id=f"perf_step_{i + 1}", execution_time=execution_time_per_step
        )
        steps.append(step)

    workflow = fixture.create_simple_workflow(steps)
    context = fixture.create_test_context()

    return workflow, context


def run_workflow_test_suite(engine: WorkflowEngine) -> Dict[str, Any]:
    """Run comprehensive workflow test suite and return results."""
    results = {"test_count": 0, "passed": 0, "failed": 0, "test_results": []}

    test_scenarios = [
        ("success_scenario", _test_successful_workflow),
        ("failure_scenario", _test_workflow_failure),
        ("rollback_scenario", _test_workflow_rollback),
        ("performance_scenario", _test_workflow_performance),
    ]

    for test_name, test_func in test_scenarios:
        results["test_count"] += 1
        try:
            test_func(engine)
            results["passed"] += 1
            results["test_results"].append({"name": test_name, "status": "PASSED"})
        except Exception as e:
            results["failed"] += 1
            results["test_results"].append(
                {"name": test_name, "status": "FAILED", "error": str(e)}
            )

    return results


def _test_successful_workflow(engine: WorkflowEngine) -> None:
    """Test successful workflow execution."""
    workflow, context = create_performance_test_scenario(3, 0.05)
    result = engine.execute_workflow(workflow, context)

    test_case = WorkflowTestCase(WorkflowTestFixture())
    test_case.assert_workflow_success(result)


def _test_workflow_failure(engine: WorkflowEngine) -> None:
    """Test workflow failure handling."""
    workflow, context = create_failure_test_scenario(2, 5, False)
    result = engine.execute_workflow(workflow, context, rollback_on_failure=False)

    test_case = WorkflowTestCase(WorkflowTestFixture())
    test_case.assert_workflow_failure(result, "step_3")


def _test_workflow_rollback(engine: WorkflowEngine) -> None:
    """Test workflow rollback functionality."""
    workflow, context = create_failure_test_scenario(3, 5, True)
    result = engine.execute_workflow(workflow, context, rollback_on_failure=True)

    test_case = WorkflowTestCase(WorkflowTestFixture())
    test_case.assert_workflow_failure(result)
    # Note: Rollback testing would need more sophisticated implementation


def _test_workflow_performance(engine: WorkflowEngine) -> None:
    """Test workflow performance."""
    workflow, context = create_performance_test_scenario(5, 0.02)
    result = engine.execute_workflow(workflow, context)

    test_case = WorkflowTestCase(WorkflowTestFixture())
    test_case.assert_workflow_success(result)
    test_case.assert_performance_bounds(result, max_duration=1.0)
