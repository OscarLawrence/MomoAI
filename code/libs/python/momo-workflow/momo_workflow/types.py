"""
Scientific workflow system - Core type definitions and protocols.

This module defines the fundamental types and protocols for the workflow system,
following scientific computing principles of reproducibility and measurability.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union
from uuid import UUID, uuid4


class StepStatus(Enum):
    """Execution status of workflow steps."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Overall workflow execution status."""

    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIALLY_ROLLED_BACK = "partially_rolled_back"
    FULLY_ROLLED_BACK = "fully_rolled_back"


@dataclass(frozen=True)
class ExecutionMetrics:
    """Scientific metrics for workflow execution analysis."""

    start_time: float
    end_time: Optional[float] = None
    cpu_time: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    disk_io_mb: Optional[float] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def is_complete(self) -> bool:
        """Check if metrics collection is complete."""
        return self.end_time is not None


@dataclass
class StepResult:
    """Result of a single workflow step execution."""

    step_id: str
    status: StepStatus
    metrics: ExecutionMetrics
    artifacts: List[Path] = field(default_factory=list)
    error: Optional[Exception] = None
    rollback_data: Optional[Dict[str, Any]] = None

    @property
    def success(self) -> bool:
        """Check if step executed successfully."""
        return self.status == StepStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "duration_seconds": self.metrics.duration_seconds,
            "artifacts": [str(p) for p in self.artifacts],
            "error": str(self.error) if self.error else None,
            "memory_peak_mb": self.metrics.memory_peak_mb,
        }


@dataclass
class WorkflowContext:
    """Context passed between workflow steps."""

    workflow_id: UUID = field(default_factory=uuid4)
    working_directory: Path = field(default_factory=lambda: Path.cwd())
    variables: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Path] = field(default_factory=list)
    step_results: Dict[str, StepResult] = field(default_factory=dict)

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get context variable with default."""
        return self.variables.get(key, default)

    def set_variable(self, key: str, value: Any) -> None:
        """Set context variable."""
        self.variables[key] = value

    def add_artifact(self, path: Path) -> None:
        """Register an artifact produced during workflow."""
        if path not in self.artifacts:
            self.artifacts.append(path)


class WorkflowStep(Protocol):
    """Protocol for workflow steps with scientific guarantees."""

    @property
    def step_id(self) -> str:
        """Unique identifier for this step."""
        ...

    @property
    def description(self) -> str:
        """Human-readable step description."""
        ...

    @property
    def is_reversible(self) -> bool:
        """Whether this step can be rolled back."""
        ...

    def validate_preconditions(self, context: WorkflowContext) -> bool:
        """Validate that step can execute in current context."""
        ...

    def execute(self, context: WorkflowContext) -> StepResult:
        """Execute the step and return result with metrics."""
        ...

    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        """Rollback changes made by this step."""
        ...

    def estimate_resources(self, context: WorkflowContext) -> Dict[str, float]:
        """Estimate resource requirements for this step."""
        ...


class Command(Protocol):
    """Protocol for executable commands within workflow steps."""

    @property
    def name(self) -> str:
        """Command identifier."""
        ...

    @property
    def description(self) -> str:
        """Command description."""
        ...

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute command and return result."""
        ...

    def validate_args(self, **kwargs) -> bool:
        """Validate command arguments."""
        ...


@dataclass
class WorkflowDefinition:
    """Scientific workflow definition with metadata."""

    workflow_id: str
    name: str
    description: str
    version: str
    author: str
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate workflow definition and return errors."""
        errors = []

        if not self.workflow_id:
            errors.append("Workflow ID is required")

        if not self.steps:
            errors.append("Workflow must have at least one step")

        # Check for duplicate step IDs
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Duplicate step IDs found")

        return errors


@dataclass
class WorkflowResult:
    """Complete workflow execution result with scientific metrics."""

    workflow_id: str
    definition: WorkflowDefinition
    status: WorkflowStatus
    context: WorkflowContext
    step_results: List[StepResult]
    overall_metrics: ExecutionMetrics
    rollback_points: List[int] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate step success rate."""
        if not self.step_results:
            return 0.0
        successful = sum(1 for r in self.step_results if r.success)
        return successful / len(self.step_results)

    @property
    def total_duration(self) -> float:
        """Total execution time in seconds."""
        return self.overall_metrics.duration_seconds

    @property
    def artifacts_produced(self) -> List[Path]:
        """All artifacts produced by workflow."""
        artifacts = list(self.context.artifacts)
        for result in self.step_results:
            artifacts.extend(result.artifacts)
        return artifacts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis and reporting."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.definition.name,
            "status": self.status.value,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "steps_executed": len(self.step_results),
            "artifacts_count": len(self.artifacts_produced),
            "rollback_points": self.rollback_points,
            "step_results": [r.to_dict() for r in self.step_results],
        }
