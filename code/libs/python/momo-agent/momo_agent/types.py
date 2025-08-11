"""
Core types and protocols for the AI agent framework.

This module defines the fundamental protocols and types for structured AI agent
task execution, integrating momo-workflow scientific rigor with momo-mom command
execution capabilities.
"""

import time
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Protocol

# Re-export key types from momo_workflow for consistency
from momo_workflow.types import (
    ExecutionMetrics,
    StepStatus,
    WorkflowStatus,
)


class AgentTaskType(Enum):
    """Types of agent tasks by complexity and execution pattern."""

    SIMPLE = "simple"  # Single-step atomic tasks
    MULTI_STEP = "multi_step"  # Decomposable multi-step tasks
    COMPLEX = "complex"  # Tasks requiring ADR workflow integration
    COMMAND = "command"  # Direct command execution tasks
    WORKFLOW = "workflow"  # Full workflow orchestration


class TaskPriority(Enum):
    """Task execution priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskMetadata:
    """Metadata for agent task execution tracking."""

    task_id: str
    task_type: AgentTaskType
    priority: TaskPriority
    estimated_duration: float = 0.0
    max_retries: int = 3
    requires_user_input: bool = False
    is_reversible: bool = True
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class AgentTaskResult:
    """Result of agent task execution with comprehensive tracking."""

    task_id: str
    status: StepStatus
    metrics: ExecutionMetrics
    outputs: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Path] = field(default_factory=list)
    error: Optional[Exception] = None
    rollback_data: Optional[dict[str, Any]] = None
    command_history: list[str] = field(default_factory=list)
    validation_results: dict[str, bool] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Whether task completed successfully."""
        return self.status == StepStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Whether task failed."""
        return self.status == StepStatus.FAILED


@dataclass
class AgentExecutionContext:
    """Execution context for agent task completion."""

    session_id: str
    current_task: str = ""
    working_directory: Path = field(default_factory=Path.cwd)
    environment_vars: dict[str, str] = field(default_factory=dict)
    task_history: list[str] = field(default_factory=list)
    shared_state: dict[str, Any] = field(default_factory=dict)
    performance_tracking: dict[str, float] = field(default_factory=dict)

    def update_performance(self, metric_name: str, value: float) -> None:
        """Update performance tracking metrics."""
        self.performance_tracking[metric_name] = value

    def add_task_to_history(self, task_id: str) -> None:
        """Add completed task to execution history."""
        self.task_history.append(task_id)


class AgentTask(Protocol):
    """Protocol for agent task definition and execution."""

    @property
    def metadata(self) -> TaskMetadata:
        """Task metadata including ID, type, and execution parameters."""
        ...

    @abstractmethod
    def validate_preconditions(self, context: AgentExecutionContext) -> bool:
        """Validate that task can be executed in current context."""
        ...

    @abstractmethod
    async def execute(self, context: AgentExecutionContext) -> AgentTaskResult:
        """Execute the task with comprehensive tracking and measurement."""
        ...

    @abstractmethod
    async def rollback(
        self, context: AgentExecutionContext, result: AgentTaskResult
    ) -> None:
        """Rollback task execution using stored rollback data."""
        ...

    def estimate_resources(self) -> dict[str, float]:
        """Estimate resource requirements for task execution."""
        return {"cpu_seconds": 1.0, "memory_mb": 10.0, "disk_mb": 1.0}


class AgentWorkflow(Protocol):
    """Protocol for multi-step agent workflow orchestration."""

    @property
    def workflow_id(self) -> str:
        """Unique workflow identifier."""
        ...

    @property
    def name(self) -> str:
        """Human-readable workflow name."""
        ...

    @property
    def tasks(self) -> list[AgentTask]:
        """Ordered list of tasks in workflow."""
        ...

    @abstractmethod
    def validate_workflow(self) -> list[str]:
        """Validate workflow definition and task dependencies."""
        ...

    @abstractmethod
    async def execute_workflow(
        self, context: AgentExecutionContext
    ) -> "AgentWorkflowResult":
        """Execute complete workflow with rollback capability."""
        ...


@dataclass
class AgentWorkflowResult:
    """Result of complete workflow execution."""

    workflow_id: str
    status: WorkflowStatus
    overall_metrics: ExecutionMetrics
    task_results: list[AgentTaskResult] = field(default_factory=list)
    context: Optional[AgentExecutionContext] = None
    rollback_points: list[int] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Whether workflow completed successfully."""
        return self.status == WorkflowStatus.SUCCESS

    @property
    def total_tasks(self) -> int:
        """Total number of tasks in workflow."""
        return len(self.task_results)

    @property
    def completed_tasks(self) -> int:
        """Number of successfully completed tasks."""
        return sum(1 for result in self.task_results if result.success)

    @property
    def failed_tasks(self) -> int:
        """Number of failed tasks."""
        return sum(1 for result in self.task_results if result.failed)


class CommandResult(Protocol):
    """Protocol for command execution results from momo-mom integration."""

    @property
    def success(self) -> bool:
        """Whether command executed successfully."""
        ...

    @property
    def return_code(self) -> int:
        """Command return code."""
        ...

    @property
    def stdout(self) -> str:
        """Command standard output."""
        ...

    @property
    def stderr(self) -> str:
        """Command standard error."""
        ...

    @property
    def command(self) -> str:
        """Original command that was executed."""
        ...


class AgentCommandExecutor(Protocol):
    """Protocol for agent command execution with momo-mom integration."""

    @abstractmethod
    async def execute_command(
        self,
        command: str,
        context: AgentExecutionContext,
        timeout_seconds: Optional[float] = None,
    ) -> CommandResult:
        """Execute command with fallback strategies and error recovery."""
        ...

    @abstractmethod
    def validate_command(self, command: str) -> bool:
        """Validate command syntax and availability."""
        ...

    @abstractmethod
    def estimate_command_duration(self, command: str) -> float:
        """Estimate command execution duration in seconds."""
        ...


# Type aliases for common usage patterns
TaskCollection = list[AgentTask]
WorkflowCollection = list[AgentWorkflow]
TaskResultCollection = list[AgentTaskResult]
