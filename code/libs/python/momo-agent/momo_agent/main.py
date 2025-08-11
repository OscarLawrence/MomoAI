"""
Main entry point for momo-agent framework.

Provides convenience functions for creating and executing agent workflows
with scientific measurement and command integration.
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from .command_executor import create_agent_command_executor
from .core import AgentWorkflowEngine, BaseAgentTask, BaseAgentWorkflow
from .types import (
    AgentExecutionContext,
    AgentTaskResult,
    AgentTaskType,
    AgentWorkflowResult,
    TaskPriority,
)


class CommandTask(BaseAgentTask):
    """Simple agent task that executes a single command."""

    def __init__(
        self,
        task_id: str,
        command: str,
        description: Optional[str] = None,
        working_directory: Optional[Path] = None,
        expected_return_code: int = 0,
    ):
        """Initialize command task."""
        super().__init__(
            task_id=task_id,
            description=description or f"Execute command: {command}",
            task_type=AgentTaskType.COMMAND,
            priority=TaskPriority.NORMAL,
            estimated_duration=1.0,
            is_reversible=False,  # Commands are generally not reversible
        )
        self._command = command
        self._working_directory = working_directory
        self._expected_return_code = expected_return_code
        self._executor = create_agent_command_executor()

    async def execute(self, context: AgentExecutionContext) -> AgentTaskResult:
        """Execute the command task."""
        start_time = time.time()

        try:
            # Update working directory if specified
            if self._working_directory:
                context.working_directory = self._working_directory

            # Execute command
            result = await self._executor.execute_command(self._command, context)

            # Check result
            success = (
                result.success and result.return_code == self._expected_return_code
            )

            return self._create_result(
                status="SUCCESS" if success else "FAILED",
                start_time=start_time,
                outputs={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.return_code,
                },
                command_history=[self._command],
                error=None
                if success
                else Exception(f"Command failed: {result.stderr}"),
            )

        except Exception as e:
            return self._create_result(
                status="FAILED",
                start_time=start_time,
                error=e,
                command_history=[self._command],
            )


def create_command_workflow(
    workflow_name: str,
    commands: list[str],
    working_directory: Optional[Path] = None,
) -> BaseAgentWorkflow:
    """
    Create a simple workflow from a list of commands.

    Args:
        workflow_name: Name for the workflow
        commands: List of commands to execute in sequence
        working_directory: Optional working directory for all commands

    Returns:
        Agent workflow ready for execution
    """
    tasks = []

    for i, command in enumerate(commands):
        task_id = f"{workflow_name}_cmd_{i + 1}"
        task = CommandTask(
            task_id=task_id,
            command=command,
            working_directory=working_directory,
        )
        tasks.append(task)

    return BaseAgentWorkflow(
        workflow_id=str(uuid.uuid4()),
        name=workflow_name,
        tasks=tasks,
    )


async def execute_command_workflow(
    workflow_name: str,
    commands: list[str],
    working_directory: Optional[Path] = None,
    session_id: Optional[str] = None,
) -> AgentWorkflowResult:
    """
    Execute a simple command workflow with full tracking.

    Args:
        workflow_name: Name for the workflow
        commands: List of commands to execute in sequence
        working_directory: Optional working directory
        session_id: Optional session identifier

    Returns:
        Complete workflow execution result
    """
    # Create workflow
    workflow = create_command_workflow(workflow_name, commands, working_directory)

    # Create execution context
    context = AgentExecutionContext(
        session_id=session_id or str(uuid.uuid4()),
        current_task=workflow_name,
        working_directory=working_directory or Path.cwd(),
    )

    # Execute workflow
    engine = AgentWorkflowEngine()
    return await engine.execute_workflow(workflow, context)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging for momo-agent framework."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("momo_agent")


# Convenience function for quick testing
async def quick_test():
    """Quick test of momo-agent framework."""
    logger = setup_logging("DEBUG")
    logger.info("Starting momo-agent quick test")

    # Test simple command workflow
    commands = [
        "echo 'Hello from momo-agent'",
        "ls -la",
        "pwd",
    ]

    result = await execute_command_workflow(
        workflow_name="quick_test",
        commands=commands,
    )

    logger.info(f"Workflow completed with status: {result.status}")
    logger.info(f"Executed {result.total_tasks} tasks")
    logger.info(f"Success rate: {result.completed_tasks}/{result.total_tasks}")

    return result


if __name__ == "__main__":
    # Run quick test if executed directly
    asyncio.run(quick_test())
