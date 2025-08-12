"""
Scientific workflow execution engine with reversible operations.

This module implements the core workflow execution engine following scientific
computing principles: reproducibility, measurability, and failure recovery.
"""

import resource
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from momo_logger import get_logger
    from momo_logger.types import LogLevel

    MOMO_LOGGER_AVAILABLE = True
except ImportError:
    import logging

    MOMO_LOGGER_AVAILABLE = False

from .types import (
    ExecutionMetrics,
    StepResult,
    StepStatus,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
)


class WorkflowEngine:
    """Scientific workflow execution engine with rollback capabilities."""

    def __init__(self, logger=None):
        """Initialize workflow engine."""
        if MOMO_LOGGER_AVAILABLE and logger is None:
            self.logger = get_logger("momo-workflow.engine", level=LogLevel.AI_SYSTEM)
        else:
            self.logger = logger or (
                logging.getLogger(__name__) if not MOMO_LOGGER_AVAILABLE else None
            )

        self._execution_stack: List[StepResult] = []

    def execute_workflow(
        self,
        definition: WorkflowDefinition,
        context: Optional[WorkflowContext] = None,
        rollback_on_failure: bool = True,
    ) -> WorkflowResult:
        """
        Execute workflow with scientific measurement and rollback capability.

        Args:
            definition: Workflow definition to execute
            context: Optional execution context (creates default if None)
            rollback_on_failure: Whether to rollback on step failure

        Returns:
            Complete workflow result with metrics and artifacts
        """
        # Validate workflow definition
        validation_errors = definition.validate()
        if validation_errors:
            raise ValueError(f"Invalid workflow: {validation_errors}")

        # Initialize context and metrics
        if context is None:
            context = WorkflowContext(variables=definition.variables.copy())

        overall_start = time.time()
        overall_metrics = ExecutionMetrics(start_time=overall_start)

        if MOMO_LOGGER_AVAILABLE:
            if hasattr(self.logger, "info"):
                # Use async logging if available, otherwise use sync fallback
                try:
                    # This would work in an async context
                    import asyncio

                    if asyncio.iscoroutinefunction(self.logger.info):
                        # We're not in an async context, so we need to handle this differently
                        # For now, use sync equivalent or skip detailed logging
                        pass
                    else:
                        # Sync logging method available
                        self.logger.info(
                            f"Starting workflow: {definition.name}",
                            context={
                                "workflow_id": definition.workflow_id,
                                "workflow_name": definition.name,
                                "total_steps": len(definition.steps),
                                "variables": definition.variables,
                            },
                            agent="workflow-engine",
                            agent_role="orchestrator",
                        )
                except Exception:
                    # Fallback to basic logging
                    pass
            # Always provide sync fallback
            if hasattr(self.logger, "_sync_log"):
                self.logger._sync_log(
                    LogLevel.AI_SYSTEM,
                    f"Starting workflow: {definition.name} ({definition.workflow_id})",
                )
        else:
            self.logger.info(
                f"Starting workflow: {definition.name} ({definition.workflow_id})"
            )

        # Execute steps
        step_results = []
        rollback_points = []
        status = WorkflowStatus.RUNNING

        try:
            for i, step in enumerate(definition.steps):
                if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, "_sync_log"):
                    self.logger._sync_log(
                        LogLevel.AI_SYSTEM,
                        f"Executing step {i + 1}/{len(definition.steps)}: {step.step_id}",
                    )
                elif not MOMO_LOGGER_AVAILABLE:
                    self.logger.info(
                        f"Executing step {i + 1}/{len(definition.steps)}: {step.step_id}"
                    )

                # Execute step with rollback tracking
                result = self._execute_step_with_tracking(step, context)
                step_results.append(result)

                if not result.success:
                    if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, "_sync_log"):
                        self.logger._sync_log(
                            LogLevel.ERROR,
                            f"Step {step.step_id} failed: {result.error}",
                        )
                    elif not MOMO_LOGGER_AVAILABLE:
                        self.logger.error(f"Step {step.step_id} failed: {result.error}")
                    status = WorkflowStatus.FAILED

                    if rollback_on_failure:
                        rollback_points = self._rollback_executed_steps(
                            step_results[:-1],
                            context,  # Exclude failed step
                        )
                        status = WorkflowStatus.PARTIALLY_ROLLED_BACK

                    break

                # Track successful step for potential rollback
                if step.is_reversible:
                    self._execution_stack.append(result)

            else:
                # All steps completed successfully
                status = WorkflowStatus.SUCCESS
                if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, "_sync_log"):
                    self.logger._sync_log(
                        LogLevel.AI_SYSTEM,
                        f"Workflow completed successfully: {definition.name}",
                    )
                elif not MOMO_LOGGER_AVAILABLE:
                    self.logger.info(
                        f"Workflow completed successfully: {definition.name}"
                    )

        except Exception as e:
            if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, "_sync_log"):
                self.logger._sync_log(
                    LogLevel.ERROR, f"Workflow execution failed with exception: {e}"
                )
            elif not MOMO_LOGGER_AVAILABLE:
                self.logger.exception(f"Workflow execution failed with exception: {e}")
            status = WorkflowStatus.FAILED

            if rollback_on_failure and self._execution_stack:
                rollback_points = self._rollback_executed_steps(
                    self._execution_stack, context
                )
                status = WorkflowStatus.FULLY_ROLLED_BACK

        # Finalize metrics
        overall_metrics = ExecutionMetrics(
            start_time=overall_start,
            end_time=time.time(),
            memory_peak_mb=self._get_peak_memory_mb(),
        )

        return WorkflowResult(
            workflow_id=definition.workflow_id,
            definition=definition,
            status=status,
            context=context,
            step_results=step_results,
            overall_metrics=overall_metrics,
            rollback_points=rollback_points,
        )

    def _execute_step_with_tracking(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> StepResult:
        """Execute a single step with comprehensive tracking."""
        # Validate preconditions
        if not step.validate_preconditions(context):
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                metrics=ExecutionMetrics(start_time=time.time(), end_time=time.time()),
                error=ValueError(f"Preconditions not met for step: {step.step_id}"),
            )

        # Start execution with resource tracking
        start_time = time.time()
        start_memory = self._get_current_memory_mb()

        try:
            # Execute step
            result = step.execute(context)

            # Update metrics with resource usage
            end_time = time.time()
            end_memory = self._get_current_memory_mb()

            result.metrics = ExecutionMetrics(
                start_time=start_time,
                end_time=end_time,
                memory_peak_mb=max(start_memory, end_memory),
            )

            # Store result in context
            context.step_results[step.step_id] = result

            if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, '_sync_log'):
                self.logger._sync_log(
                    LogLevel.AI_SYSTEM,
                    f"Step {step.step_id} completed in {result.metrics.duration_seconds:.2f}s"
                )
            elif not MOMO_LOGGER_AVAILABLE:
                self.logger.info(
                    f"Step {step.step_id} completed in {result.metrics.duration_seconds:.2f}s"
                )

            return result

        except Exception as e:
            end_time = time.time()
            if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, '_sync_log'):
                self.logger._sync_log(
                    LogLevel.ERROR,
                    f"Step {step.step_id} failed with exception: {e}"
                )
            elif not MOMO_LOGGER_AVAILABLE:
                self.logger.exception(f"Step {step.step_id} failed with exception: {e}")

            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                metrics=ExecutionMetrics(start_time=start_time, end_time=end_time),
                error=e,
            )

    def _rollback_executed_steps(
        self, step_results: List[StepResult], context: WorkflowContext
    ) -> List[int]:
        """Rollback executed steps in reverse order."""
        rollback_points = []

        # Find corresponding step definitions for rollback
        for i, result in enumerate(reversed(step_results)):
            if result.success and result.rollback_data is not None:
                try:
                    # Find step definition to execute rollback
                    step_def = self._find_step_by_id(result.step_id, context)
                    if step_def and step_def.is_reversible:
                        if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, '_sync_log'):
                            self.logger._sync_log(
                                LogLevel.AI_SYSTEM,
                                f"Rolling back step: {result.step_id}"
                            )
                        elif not MOMO_LOGGER_AVAILABLE:
                            self.logger.info(f"Rolling back step: {result.step_id}")
                        step_def.rollback(context, result)
                        rollback_points.append(len(step_results) - i - 1)

                        # Update status
                        result.status = StepStatus.ROLLED_BACK

                except Exception as e:
                    if MOMO_LOGGER_AVAILABLE and hasattr(self.logger, '_sync_log'):
                        self.logger._sync_log(
                            LogLevel.ERROR,
                            f"Failed to rollback step {result.step_id}: {e}"
                        )
                    elif not MOMO_LOGGER_AVAILABLE:
                        self.logger.error(f"Failed to rollback step {result.step_id}: {e}")

        return rollback_points

    def _find_step_by_id(
        self, step_id: str, context: WorkflowContext
    ) -> Optional[WorkflowStep]:
        """Find step definition by ID (would need access to definition)."""
        # This is a simplified implementation
        # In practice, would need to store definition reference
        return None

    def _get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            # Get memory usage in KB, convert to MB
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except (OSError, AttributeError):
            return 0.0

    def _get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        return self._get_current_memory_mb()


class BaseWorkflowStep:
    """Base implementation for workflow steps with common functionality."""

    def __init__(self, step_id: str, description: str, reversible: bool = True):
        """Initialize base step."""
        self._step_id = step_id
        self._description = description
        self._reversible = reversible

    @property
    def step_id(self) -> str:
        """Step identifier."""
        return self._step_id

    @property
    def description(self) -> str:
        """Step description."""
        return self._description

    @property
    def is_reversible(self) -> bool:
        """Whether step can be rolled back."""
        return self._reversible

    def validate_preconditions(self, context: WorkflowContext) -> bool:
        """Default validation - always passes."""
        return True

    def execute(self, context: WorkflowContext) -> StepResult:
        """Execute step - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")

    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        """Default rollback - no action."""
        if not self.is_reversible:
            raise ValueError(f"Step {self.step_id} is not reversible")

    def estimate_resources(self, context: WorkflowContext) -> Dict[str, float]:
        """Default resource estimation."""
        return {"cpu_seconds": 1.0, "memory_mb": 10.0, "disk_mb": 1.0}
