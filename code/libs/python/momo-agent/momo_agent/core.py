"""
Core agent task execution engine integrating momo-workflow and momo-mom.

This module implements the unified AI agent framework that connects scientific
workflow management with command execution and fallback strategies.
"""

import time
import uuid
from typing import Optional

try:
    from momo_logger import get_logger
    from momo_logger.types import LogLevel

    MOMO_LOGGER_AVAILABLE = True
except ImportError:
    import logging

    MOMO_LOGGER_AVAILABLE = False

from momo_workflow.core import WorkflowEngine
from momo_workflow.types import ExecutionMetrics, StepStatus

from .types import (
    AgentExecutionContext,
    AgentTask,
    AgentTaskResult,
    AgentTaskType,
    AgentWorkflow,
    AgentWorkflowResult,
    TaskMetadata,
    TaskPriority,
)


class BaseAgentTask:
    """Base implementation for agent tasks with scientific measurement."""

    def __init__(
        self,
        task_id: str,
        description: str,
        task_type: AgentTaskType = AgentTaskType.SIMPLE,
        priority: TaskPriority = TaskPriority.NORMAL,
        estimated_duration: float = 1.0,
        is_reversible: bool = True,
    ):
        """Initialize base agent task."""
        self._metadata = TaskMetadata(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            estimated_duration=estimated_duration,
            is_reversible=is_reversible,
        )
        self._description = description
        if MOMO_LOGGER_AVAILABLE:
            self._logger = get_logger(
                f"momo-agent.task.{task_id}", level=LogLevel.DEVELOPER
            )
        else:
            self._logger = logging.getLogger(f"{__name__}.{task_id}")

    @property
    def metadata(self) -> TaskMetadata:
        """Task metadata including ID, type, and execution parameters."""
        return self._metadata

    @property
    def description(self) -> str:
        """Task description."""
        return self._description

    def validate_preconditions(self, context: AgentExecutionContext) -> bool:
        """Default validation - always passes unless overridden."""
        return True

    async def execute(self, context: AgentExecutionContext) -> AgentTaskResult:
        """Execute task - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")

    async def rollback(
        self, context: AgentExecutionContext, result: AgentTaskResult
    ) -> None:
        """Default rollback - no action unless overridden."""
        if not self.metadata.is_reversible:
            raise ValueError(f"Task {self.metadata.task_id} is not reversible")

        if MOMO_LOGGER_AVAILABLE:
            await self._logger.info(
                f"No rollback action required for task {self.metadata.task_id}",
                context={"task_id": self.metadata.task_id, "operation": "rollback"},
            )
        else:
            self._logger.info(
                f"No rollback action required for task {self.metadata.task_id}"
            )

    def estimate_resources(self) -> dict[str, float]:
        """Default resource estimation."""
        return {
            "cpu_seconds": self.metadata.estimated_duration,
            "memory_mb": 10.0,
            "disk_mb": 1.0,
        }

    def _create_result(
        self,
        status: StepStatus,
        start_time: float,
        end_time: Optional[float] = None,
        error: Optional[Exception] = None,
        outputs: Optional[dict] = None,
        rollback_data: Optional[dict] = None,
        command_history: Optional[list[str]] = None,
    ) -> AgentTaskResult:
        """Helper to create standardized task result."""
        if end_time is None:
            end_time = time.time()

        return AgentTaskResult(
            task_id=self.metadata.task_id,
            status=status,
            metrics=ExecutionMetrics(start_time=start_time, end_time=end_time),
            outputs=outputs or {},
            error=error,
            rollback_data=rollback_data,
            command_history=command_history or [],
        )


class AgentWorkflowEngine:
    """Scientific workflow execution engine for AI agent tasks."""

    def __init__(self, logger=None):
        """Initialize agent workflow engine."""
        if MOMO_LOGGER_AVAILABLE and logger is None:
            self.logger = get_logger(
                "momo-agent.workflow-engine", level=LogLevel.AI_SYSTEM
            )
        else:
            self.logger = logger or (
                logging.getLogger(__name__) if not MOMO_LOGGER_AVAILABLE else None
            )

        self._workflow_engine = WorkflowEngine(
            self.logger if not MOMO_LOGGER_AVAILABLE else None
        )
        self._execution_stack: list[AgentTaskResult] = []

    async def execute_workflow(
        self,
        workflow: AgentWorkflow,
        context: Optional[AgentExecutionContext] = None,
        rollback_on_failure: bool = True,
    ) -> AgentWorkflowResult:
        """
        Execute agent workflow with scientific measurement and rollback capability.

        Args:
            workflow: Agent workflow to execute
            context: Optional execution context (creates default if None)
            rollback_on_failure: Whether to rollback on task failure

        Returns:
            Complete workflow result with metrics and rollback information
        """
        # Validate workflow
        validation_errors = workflow.validate_workflow()
        if validation_errors:
            raise ValueError(f"Invalid workflow: {validation_errors}")

        # Initialize context if needed
        if context is None:
            context = AgentExecutionContext(
                session_id=str(uuid.uuid4()),
                current_task=workflow.name,
            )

        # Start execution tracking
        overall_start = time.time()
        if MOMO_LOGGER_AVAILABLE:
            await self.logger.info(
                f"Starting agent workflow: {workflow.name}",
                context={
                    "workflow_id": workflow.workflow_id,
                    "workflow_name": workflow.name,
                    "session_id": context.session_id,
                    "total_tasks": len(workflow.tasks),
                },
                agent="workflow-engine",
                agent_role="orchestrator",
            )
        else:
            self.logger.info(
                f"Starting agent workflow: {workflow.name} ({workflow.workflow_id})"
            )

        task_results = []
        rollback_points = []
        status = None

        try:
            # Execute tasks sequentially with tracking
            for i, task in enumerate(workflow.tasks):
                task_num = f"{i + 1}/{len(workflow.tasks)}"
                if MOMO_LOGGER_AVAILABLE:
                    await self.logger.info(
                        f"Executing task {task_num}: {task.metadata.task_id}",
                        context={
                            "task_id": task.metadata.task_id,
                            "task_number": i + 1,
                            "total_tasks": len(workflow.tasks),
                            "task_type": task.metadata.task_type.value,
                            "session_id": context.session_id,
                        },
                        agent="workflow-engine",
                        agent_role="executor",
                    )
                else:
                    task_info = f"Executing task {task_num}: {task.metadata.task_id}"
                    self.logger.info(task_info)

                # Update context with current task
                context.current_task = task.metadata.task_id

                # Validate preconditions
                if not task.validate_preconditions(context):
                    error_msg = (
                        f"Preconditions not met for task: {task.metadata.task_id}"
                    )
                    if MOMO_LOGGER_AVAILABLE:
                        await self.logger.error(
                            error_msg,
                            context={
                                "task_id": task.metadata.task_id,
                                "session_id": context.session_id,
                                "failure_reason": "preconditions_not_met",
                            },
                            agent="workflow-engine",
                            agent_role="validator",
                        )
                    else:
                        self.logger.error(error_msg)

                    result = AgentTaskResult(
                        task_id=task.metadata.task_id,
                        status=StepStatus.FAILED,
                        metrics=ExecutionMetrics(
                            start_time=time.time(), end_time=time.time()
                        ),
                        error=ValueError(error_msg),
                    )
                    task_results.append(result)

                    if rollback_on_failure:
                        rollback_points = await self._rollback_executed_tasks(
                            task_results[:-1], context
                        )

                    status = "FAILED"
                    break

                # Execute task with error handling
                try:
                    result = await task.execute(context)
                    task_results.append(result)

                    if not result.success:
                        if MOMO_LOGGER_AVAILABLE:
                            await self.logger.error(
                                f"Task {task.metadata.task_id} failed",
                                context={
                                    "task_id": task.metadata.task_id,
                                    "session_id": context.session_id,
                                    "error_type": type(result.error).__name__
                                    if result.error
                                    else "unknown",
                                    "error_message": str(result.error)
                                    if result.error
                                    else "no_error_details",
                                },
                                exception=str(result.error) if result.error else None,
                                agent="workflow-engine",
                                agent_role="monitor",
                            )
                        else:
                            self.logger.error(
                                f"Task {task.metadata.task_id} failed: {result.error}"
                            )

                        if rollback_on_failure:
                            rollback_points = await self._rollback_executed_tasks(
                                task_results[:-1], context
                            )

                        status = "FAILED"
                        break

                    # Track successful task for potential rollback
                    if task.metadata.is_reversible:
                        self._execution_stack.append(result)

                    # Add to context history
                    context.add_task_to_history(task.metadata.task_id)

                except Exception as e:
                    if MOMO_LOGGER_AVAILABLE:
                        await self.logger.error(
                            f"Task {task.metadata.task_id} failed with exception",
                            context={
                                "task_id": task.metadata.task_id,
                                "session_id": context.session_id,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                            },
                            exception=str(e),
                            agent="workflow-engine",
                            agent_role="error_handler",
                        )
                    else:
                        self.logger.exception(
                            f"Task {task.metadata.task_id} failed with exception: {e}"
                        )

                    result = AgentTaskResult(
                        task_id=task.metadata.task_id,
                        status=StepStatus.FAILED,
                        metrics=ExecutionMetrics(
                            start_time=time.time(), end_time=time.time()
                        ),
                        error=e,
                    )
                    task_results.append(result)

                    if rollback_on_failure:
                        rollback_points = await self._rollback_executed_tasks(
                            self._execution_stack, context
                        )

                    status = "FAILED"
                    break

            else:
                # All tasks completed successfully
                status = "SUCCESS"
                if MOMO_LOGGER_AVAILABLE:
                    await self.logger.info(
                        f"Agent workflow completed successfully: {workflow.name}",
                        context={
                            "workflow_id": workflow.workflow_id,
                            "workflow_name": workflow.name,
                            "session_id": context.session_id,
                            "completed_tasks": len(workflow.tasks),
                            "total_duration": time.time() - overall_start,
                        },
                        agent="workflow-engine",
                        agent_role="orchestrator",
                    )
                else:
                    self.logger.info(
                        f"Agent workflow completed successfully: {workflow.name}"
                    )

        except Exception as e:
            if MOMO_LOGGER_AVAILABLE:
                await self.logger.error(
                    f"Workflow execution failed with exception",
                    context={
                        "workflow_id": workflow.workflow_id,
                        "session_id": context.session_id,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    },
                    exception=str(e),
                    agent="workflow-engine",
                    agent_role="error_handler",
                )
            else:
                self.logger.exception(f"Workflow execution failed with exception: {e}")
            status = "FAILED"

            if rollback_on_failure and self._execution_stack:
                rollback_points = await self._rollback_executed_tasks(
                    self._execution_stack, context
                )

        # Finalize metrics
        overall_metrics = ExecutionMetrics(
            start_time=overall_start,
            end_time=time.time(),
        )

        return AgentWorkflowResult(
            workflow_id=workflow.workflow_id,
            status=status,  # Will be properly typed in final implementation
            overall_metrics=overall_metrics,
            task_results=task_results,
            context=context,
            rollback_points=rollback_points,
        )

    async def _rollback_executed_tasks(
        self, task_results: list[AgentTaskResult], context: AgentExecutionContext
    ) -> list[int]:
        """Rollback executed tasks in reverse order."""
        rollback_points = []

        # Find corresponding tasks and rollback in reverse order
        for i, result in enumerate(reversed(task_results)):
            if result.success and result.rollback_data is not None:
                try:
                    # Find corresponding task (needs task registry in real impl)
                    # For now, we'll log the rollback attempt
                    if MOMO_LOGGER_AVAILABLE:
                        await self.logger.info(
                            f"Rolling back task: {result.task_id}",
                            context={
                                "task_id": result.task_id,
                                "rollback_position": len(task_results) - i - 1,
                                "total_rollbacks": len(task_results),
                            },
                            agent="workflow-engine",
                            agent_role="recovery",
                        )
                    else:
                        self.logger.info(f"Rolling back task: {result.task_id}")
                    rollback_points.append(len(task_results) - i - 1)

                    # Update status
                    result.status = StepStatus.ROLLED_BACK

                except Exception as e:
                    if MOMO_LOGGER_AVAILABLE:
                        await self.logger.error(
                            f"Failed to rollback task {result.task_id}",
                            context={
                                "task_id": result.task_id,
                                "rollback_error": str(e),
                                "error_type": type(e).__name__,
                            },
                            exception=str(e),
                            agent="workflow-engine",
                            agent_role="recovery",
                        )
                    else:
                        self.logger.error(
                            f"Failed to rollback task {result.task_id}: {e}"
                        )

        return rollback_points

    def get_execution_summary(self) -> dict[str, any]:
        """Get summary of workflow execution performance."""
        return {
            "total_executions": len(self._execution_stack),
            "successful_tasks": len([r for r in self._execution_stack if r.success]),
            "failed_tasks": len([r for r in self._execution_stack if r.failed]),
            "average_duration": sum(
                r.metrics.duration_seconds for r in self._execution_stack
            )
            / len(self._execution_stack)
            if self._execution_stack
            else 0.0,
        }


class BaseAgentWorkflow:
    """Base implementation for agent workflows."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        tasks: list[AgentTask],
    ):
        """Initialize agent workflow."""
        self._workflow_id = workflow_id
        self._name = name
        self._tasks = tasks
        if MOMO_LOGGER_AVAILABLE:
            self._logger = get_logger(
                f"momo-agent.workflow.{workflow_id}", level=LogLevel.ARCHITECT
            )
        else:
            self._logger = logging.getLogger(f"{__name__}.{workflow_id}")

    @property
    def workflow_id(self) -> str:
        """Unique workflow identifier."""
        return self._workflow_id

    @property
    def name(self) -> str:
        """Human-readable workflow name."""
        return self._name

    @property
    def tasks(self) -> list[AgentTask]:
        """Ordered list of tasks in workflow."""
        return self._tasks

    def validate_workflow(self) -> list[str]:
        """Validate workflow definition and task dependencies."""
        errors = []

        if not self._tasks:
            errors.append("Workflow must contain at least one task")

        # Check for duplicate task IDs
        task_ids = [task.metadata.task_id for task in self._tasks]
        if len(task_ids) != len(set(task_ids)):
            errors.append("Workflow contains duplicate task IDs")

        # Validate task dependencies exist
        for task in self._tasks:
            for dep in task.metadata.dependencies:
                if dep not in task_ids:
                    task_id = task.metadata.task_id
                    error_msg = f"Task {task_id} depends on non-existent task {dep}"
                    errors.append(error_msg)

        return errors

    async def execute_workflow(
        self, context: AgentExecutionContext
    ) -> AgentWorkflowResult:
        """Execute complete workflow using AgentWorkflowEngine."""
        engine = AgentWorkflowEngine(self._logger)
        return await engine.execute_workflow(self, context)
