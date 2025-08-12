"""Unit tests for momo-agent types and protocols."""

import time
from pathlib import Path

from momo_workflow.types import ExecutionMetrics, StepStatus

from momo_agent.types import (
    AgentExecutionContext,
    AgentTaskResult,
    AgentTaskType,
    TaskMetadata,
    TaskPriority,
)


class TestAgentExecutionContext:
    """Test AgentExecutionContext functionality."""

    def test_initialization(self):
        """Test context initialization with defaults."""
        context = AgentExecutionContext(session_id="test-session")

        assert context.session_id == "test-session"
        assert context.current_task == ""
        assert context.working_directory == Path.cwd()
        assert context.environment_vars == {}
        assert context.task_history == []
        assert context.shared_state == {}
        assert context.performance_tracking == {}

    def test_update_performance(self):
        """Test performance tracking updates."""
        context = AgentExecutionContext(session_id="test-session")

        context.update_performance("task_1", 1.5)
        context.update_performance("task_2", 2.3)

        assert context.performance_tracking["task_1"] == 1.5
        assert context.performance_tracking["task_2"] == 2.3

    def test_add_task_to_history(self):
        """Test task history tracking."""
        context = AgentExecutionContext(session_id="test-session")

        context.add_task_to_history("task_1")
        context.add_task_to_history("task_2")

        assert context.task_history == ["task_1", "task_2"]


class TestTaskMetadata:
    """Test TaskMetadata functionality."""

    def test_initialization(self):
        """Test metadata initialization."""
        metadata = TaskMetadata(
            task_id="test-task",
            task_type=AgentTaskType.SIMPLE,
            priority=TaskPriority.NORMAL,
        )

        assert metadata.task_id == "test-task"
        assert metadata.task_type == AgentTaskType.SIMPLE
        assert metadata.priority == TaskPriority.NORMAL
        assert metadata.estimated_duration == 0.0
        assert metadata.max_retries == 3
        assert not metadata.requires_user_input
        assert metadata.is_reversible
        assert metadata.tags == []
        assert metadata.dependencies == []
        assert isinstance(metadata.created_at, float)

    def test_with_dependencies(self):
        """Test metadata with dependencies and tags."""
        metadata = TaskMetadata(
            task_id="test-task",
            task_type=AgentTaskType.MULTI_STEP,
            priority=TaskPriority.HIGH,
            dependencies=["task_1", "task_2"],
            tags=["important", "test"],
        )

        assert metadata.dependencies == ["task_1", "task_2"]
        assert metadata.tags == ["important", "test"]
        assert metadata.priority == TaskPriority.HIGH


class TestAgentTaskResult:
    """Test AgentTaskResult functionality."""

    def test_success_property(self):
        """Test success property detection."""
        metrics = ExecutionMetrics(start_time=time.time(), end_time=time.time())

        success_result = AgentTaskResult(
            task_id="test-task",
            status=StepStatus.SUCCESS,
            metrics=metrics,
        )

        assert success_result.success
        assert not success_result.failed

    def test_failed_property(self):
        """Test failed property detection."""
        metrics = ExecutionMetrics(start_time=time.time(), end_time=time.time())

        failed_result = AgentTaskResult(
            task_id="test-task",
            status=StepStatus.FAILED,
            metrics=metrics,
            error=Exception("Test error"),
        )

        assert not failed_result.success
        assert failed_result.failed

    def test_with_outputs_and_artifacts(self):
        """Test result with outputs and artifacts."""
        metrics = ExecutionMetrics(start_time=time.time(), end_time=time.time())

        result = AgentTaskResult(
            task_id="test-task",
            status=StepStatus.SUCCESS,
            metrics=metrics,
            outputs={"result": "test_value"},
            artifacts=[Path("/tmp/test_file.txt")],
            command_history=["echo hello", "ls -la"],
        )

        assert result.outputs["result"] == "test_value"
        assert len(result.artifacts) == 1
        assert result.artifacts[0] == Path("/tmp/test_file.txt")
        assert len(result.command_history) == 2
        assert result.command_history[0] == "echo hello"


class TestEnums:
    """Test enum values and behavior."""

    def test_agent_task_type_values(self):
        """Test AgentTaskType enum values."""
        assert AgentTaskType.SIMPLE.value == "simple"
        assert AgentTaskType.MULTI_STEP.value == "multi_step"
        assert AgentTaskType.COMPLEX.value == "complex"
        assert AgentTaskType.COMMAND.value == "command"
        assert AgentTaskType.WORKFLOW.value == "workflow"

    def test_task_priority_values(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.HIGH.value == 3
        assert TaskPriority.CRITICAL.value == 4

        # Test priority ordering
        assert TaskPriority.CRITICAL.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value > TaskPriority.LOW.value
