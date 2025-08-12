"""Unit tests for momo-agent core functionality."""

import time
from unittest.mock import Mock

import pytest
from momo_workflow.types import StepStatus

from momo_agent.core import AgentWorkflowEngine, BaseAgentTask, BaseAgentWorkflow
from momo_agent.types import (
    AgentExecutionContext,
    AgentTaskResult,
    AgentTaskType,
    TaskPriority,
)


class TestBaseAgentTask:
    """Test BaseAgentTask functionality."""

    def test_initialization(self):
        """Test task initialization with defaults."""
        task = BaseAgentTask(
            task_id="test-task",
            description="Test task description",
        )

        assert task.metadata.task_id == "test-task"
        assert task.description == "Test task description"
        assert task.metadata.task_type == AgentTaskType.SIMPLE
        assert task.metadata.priority == TaskPriority.NORMAL
        assert task.metadata.estimated_duration == 1.0
        assert task.metadata.is_reversible

    def test_custom_initialization(self):
        """Test task initialization with custom values."""
        task = BaseAgentTask(
            task_id="complex-task",
            description="Complex task",
            task_type=AgentTaskType.COMPLEX,
            priority=TaskPriority.HIGH,
            estimated_duration=5.0,
            is_reversible=False,
        )

        assert task.metadata.task_type == AgentTaskType.COMPLEX
        assert task.metadata.priority == TaskPriority.HIGH
        assert task.metadata.estimated_duration == 5.0
        assert not task.metadata.is_reversible

    def test_validate_preconditions_default(self):
        """Test default precondition validation."""
        task = BaseAgentTask("test-task", "Test description")
        context = AgentExecutionContext(session_id="test-session")

        assert task.validate_preconditions(context)

    def test_estimate_resources(self):
        """Test resource estimation."""
        task = BaseAgentTask(
            task_id="test-task",
            description="Test task",
            estimated_duration=3.0,
        )

        resources = task.estimate_resources()

        assert resources["cpu_seconds"] == 3.0
        assert resources["memory_mb"] == 10.0
        assert resources["disk_mb"] == 1.0

    @pytest.mark.asyncio
    async def test_execute_not_implemented(self):
        """Test that execute raises NotImplementedError."""
        task = BaseAgentTask("test-task", "Test description")
        context = AgentExecutionContext(session_id="test-session")

        with pytest.raises(NotImplementedError):
            await task.execute(context)

    @pytest.mark.asyncio
    async def test_rollback_not_reversible(self):
        """Test rollback on non-reversible task."""
        task = BaseAgentTask(
            task_id="test-task",
            description="Test task",
            is_reversible=False,
        )
        context = AgentExecutionContext(session_id="test-session")
        result = AgentTaskResult(
            task_id="test-task",
            status=StepStatus.SUCCESS,
            metrics=Mock(),
        )

        with pytest.raises(ValueError, match="not reversible"):
            await task.rollback(context, result)

    def test_create_result_helper(self):
        """Test result creation helper."""
        task = BaseAgentTask("test-task", "Test description")
        start_time = time.time()

        result = task._create_result(
            status=StepStatus.SUCCESS,
            start_time=start_time,
            outputs={"key": "value"},
            command_history=["echo test"],
        )

        assert result.task_id == "test-task"
        assert result.status == StepStatus.SUCCESS
        assert result.outputs["key"] == "value"
        assert result.command_history == ["echo test"]
        assert result.metrics.start_time == start_time


class TestConcreteAgentTask:
    """Test concrete agent task implementation."""

    class SimpleTask(BaseAgentTask):
        """Simple test task implementation."""

        def __init__(self, task_id: str, should_fail: bool = False):
            super().__init__(task_id, f"Simple task {task_id}")
            self._should_fail = should_fail

        async def execute(self, context: AgentExecutionContext) -> AgentTaskResult:
            """Execute the simple task."""
            start_time = time.time()

            if self._should_fail:
                return self._create_result(
                    status=StepStatus.FAILED,
                    start_time=start_time,
                    error=Exception("Intentional failure"),
                )

            return self._create_result(
                status=StepStatus.SUCCESS,
                start_time=start_time,
                outputs={"message": f"Task {self.metadata.task_id} completed"},
            )

    @pytest.mark.asyncio
    async def test_simple_task_success(self):
        """Test successful task execution."""
        task = self.SimpleTask("success-task")
        context = AgentExecutionContext(session_id="test-session")

        result = await task.execute(context)

        assert result.success
        assert result.outputs["message"] == "Task success-task completed"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_simple_task_failure(self):
        """Test failed task execution."""
        task = self.SimpleTask("fail-task", should_fail=True)
        context = AgentExecutionContext(session_id="test-session")

        result = await task.execute(context)

        assert not result.success
        assert result.failed
        assert result.error is not None
        assert "Intentional failure" in str(result.error)


class TestBaseAgentWorkflow:
    """Test BaseAgentWorkflow functionality."""

    def test_initialization(self):
        """Test workflow initialization."""
        tasks = [
            TestConcreteAgentTask.SimpleTask("task1"),
            TestConcreteAgentTask.SimpleTask("task2"),
        ]

        workflow = BaseAgentWorkflow(
            workflow_id="test-workflow",
            name="Test Workflow",
            tasks=tasks,
        )

        assert workflow.workflow_id == "test-workflow"
        assert workflow.name == "Test Workflow"
        assert len(workflow.tasks) == 2

    def test_validate_workflow_success(self):
        """Test successful workflow validation."""
        tasks = [
            TestConcreteAgentTask.SimpleTask("task1"),
            TestConcreteAgentTask.SimpleTask("task2"),
        ]

        workflow = BaseAgentWorkflow("test-workflow", "Test Workflow", tasks)
        errors = workflow.validate_workflow()

        assert len(errors) == 0

    def test_validate_empty_workflow(self):
        """Test validation of empty workflow."""
        workflow = BaseAgentWorkflow("empty-workflow", "Empty Workflow", [])
        errors = workflow.validate_workflow()

        assert len(errors) == 1
        assert "at least one task" in errors[0]

    def test_validate_duplicate_task_ids(self):
        """Test validation with duplicate task IDs."""
        tasks = [
            TestConcreteAgentTask.SimpleTask("duplicate"),
            TestConcreteAgentTask.SimpleTask("duplicate"),
        ]

        workflow = BaseAgentWorkflow("test-workflow", "Test Workflow", tasks)
        errors = workflow.validate_workflow()

        assert len(errors) == 1
        assert "duplicate task IDs" in errors[0]


class TestAgentWorkflowEngine:
    """Test AgentWorkflowEngine functionality."""

    def test_initialization(self):
        """Test workflow engine initialization."""
        engine = AgentWorkflowEngine()

        assert engine.logger is not None
        assert len(engine._execution_stack) == 0

    @pytest.mark.asyncio
    async def test_execute_empty_workflow_validation(self):
        """Test workflow execution with validation errors."""
        engine = AgentWorkflowEngine()
        workflow = BaseAgentWorkflow("empty-workflow", "Empty Workflow", [])

        with pytest.raises(ValueError, match="Invalid workflow"):
            await engine.execute_workflow(workflow)

    @pytest.mark.asyncio
    async def test_execute_successful_workflow(self):
        """Test execution of successful workflow."""
        engine = AgentWorkflowEngine()
        tasks = [
            TestConcreteAgentTask.SimpleTask("task1"),
            TestConcreteAgentTask.SimpleTask("task2"),
        ]
        workflow = BaseAgentWorkflow("success-workflow", "Success Workflow", tasks)
        context = AgentExecutionContext(session_id="test-session")

        result = await engine.execute_workflow(workflow, context)

        assert result.status == "SUCCESS"
        assert len(result.task_results) == 2
        assert all(r.success for r in result.task_results)
        assert result.completed_tasks == 2
        assert result.failed_tasks == 0

    @pytest.mark.asyncio
    async def test_execute_workflow_with_failure(self):
        """Test execution of workflow with failure."""
        engine = AgentWorkflowEngine()
        tasks = [
            TestConcreteAgentTask.SimpleTask("task1"),  # Success
            TestConcreteAgentTask.SimpleTask("task2", should_fail=True),  # Failure
        ]
        workflow = BaseAgentWorkflow("fail-workflow", "Fail Workflow", tasks)
        context = AgentExecutionContext(session_id="test-session")

        result = await engine.execute_workflow(
            workflow, context, rollback_on_failure=False
        )

        assert result.status == "FAILED"
        assert len(result.task_results) == 2
        assert result.task_results[0].success
        assert result.task_results[1].failed
        assert result.completed_tasks == 1
        assert result.failed_tasks == 1

    def test_get_execution_summary_empty(self):
        """Test execution summary with no executions."""
        engine = AgentWorkflowEngine()
        summary = engine.get_execution_summary()

        assert summary["total_executions"] == 0
        assert summary["successful_tasks"] == 0
        assert summary["failed_tasks"] == 0
        assert summary["average_duration"] == 0.0
