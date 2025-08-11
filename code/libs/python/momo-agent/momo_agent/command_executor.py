"""
Agent command executor integrating momo-mom command system.

This module provides the AgentCommandExecutor implementation that wraps
momo-mom's command execution capabilities with agent-specific features
like timeout handling, performance tracking, and error recovery.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional

try:
    from momo_logger import get_logger
    from momo_logger.types import LogLevel

    MOMO_LOGGER_AVAILABLE = True
except ImportError:
    import logging

    MOMO_LOGGER_AVAILABLE = False

from momo_mom.config import ConfigManager
from momo_mom.executor import CommandExecutor

from .types import AgentExecutionContext, CommandResult


class MomCommandResult:
    """Wrapper for momo-mom command execution results."""

    def __init__(
        self,
        success: bool,
        return_code: int,
        stdout: str,
        stderr: str,
        command: str,
        execution_time: float = 0.0,
    ):
        """Initialize command result."""
        self._success = success
        self._return_code = return_code
        self._stdout = stdout
        self._stderr = stderr
        self._command = command
        self._execution_time = execution_time

    @property
    def success(self) -> bool:
        """Whether command executed successfully."""
        return self._success

    @property
    def return_code(self) -> int:
        """Command return code."""
        return self._return_code

    @property
    def stdout(self) -> str:
        """Command standard output."""
        return self._stdout

    @property
    def stderr(self) -> str:
        """Command standard error."""
        return self._stderr

    @property
    def command(self) -> str:
        """Original command that was executed."""
        return self._command

    @property
    def execution_time(self) -> float:
        """Command execution time in seconds."""
        return self._execution_time


class MomAgentCommandExecutor:
    """Agent command executor using momo-mom with fallback strategies."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        verbose: bool = False,
        ai_output: bool = True,
        logger=None,
    ):
        """Initialize agent command executor."""
        if MOMO_LOGGER_AVAILABLE and logger is None:
            self.logger = get_logger(
                "momo-agent.command-executor", level=LogLevel.AI_AGENT
            )
        else:
            self.logger = logger or (
                logging.getLogger(__name__) if not MOMO_LOGGER_AVAILABLE else None
            )
        self._config_manager = ConfigManager()

        # Load configuration
        if config_path and config_path.exists():
            self._config = self._config_manager.load_config(config_path)
        else:
            # Use default configuration
            self._config = {
                "execution": {
                    "retry_count": 2,
                    "auto_reset_on_cache_failure": True,
                    "timeout_seconds": 300,
                },
                "recovery": {
                    "nx_reset": "nx reset",
                    "cache_clean": "nx reset",
                },
                "output": {
                    "format": "structured",
                },
            }

        # Initialize underlying command executor
        self._executor = CommandExecutor(
            config=self._config,
            verbose=verbose,
            ai_output=ai_output,
        )

        # Command execution metrics
        self._execution_count = 0
        self._success_count = 0
        self._total_execution_time = 0.0
        self._command_durations: dict[str, float] = {}

    async def execute_command(
        self,
        command: str,
        context: AgentExecutionContext,
        timeout_seconds: Optional[float] = None,
    ) -> CommandResult:
        """
        Execute command with fallback strategies and error recovery.

        Args:
            command: Command to execute
            context: Agent execution context
            timeout_seconds: Optional timeout (uses config default if None)

        Returns:
            Command execution result with performance metrics
        """
        start_time = time.time()

        # Update execution tracking
        self._execution_count += 1

        # Set working directory from context
        original_cwd = Path.cwd()
        try:
            if context.working_directory != original_cwd:
                context.working_directory.mkdir(parents=True, exist_ok=True)
                # Note: momo-mom executor handles cwd internally

            if MOMO_LOGGER_AVAILABLE:
                await self.logger.info(
                    f"Executing command: {command}",
                    context={
                        "command": command,
                        "session_id": context.session_id,
                        "working_directory": str(context.working_directory),
                        "timeout": timeout,
                        "execution_count": self._execution_count,
                    },
                    agent="command-executor",
                    agent_role="executor",
                )
            else:
                self.logger.info(f"Executing command: {command}")
                self.logger.debug(f"Working directory: {context.working_directory}")

            # Execute with timeout handling
            timeout = timeout_seconds or self._config["execution"].get(
                "timeout_seconds", 300
            )

            try:
                # Use asyncio to add timeout wrapper around sync execution
                result = await asyncio.wait_for(
                    self._execute_sync_command(command, context), timeout=timeout
                )

                end_time = time.time()
                execution_time = end_time - start_time

                # Update metrics
                self._total_execution_time += execution_time
                if result.success:
                    self._success_count += 1

                # Track command duration for estimation
                cmd_base = command.split()[0] if command.split() else command
                self._command_durations[cmd_base] = execution_time

                # Update context performance tracking
                context.update_performance(
                    f"command_{self._execution_count}", execution_time
                )

                if MOMO_LOGGER_AVAILABLE:
                    await self.logger.info(
                        f"Command completed in {execution_time:.2f}s",
                        context={
                            "command": command,
                            "execution_time": execution_time,
                            "success": result.success,
                            "return_code": result.return_code,
                            "session_id": context.session_id,
                            "stdout_length": len(result.stdout),
                            "stderr_length": len(result.stderr),
                        },
                        agent="command-executor",
                        agent_role="monitor",
                    )
                else:
                    self.logger.info(
                        f"Command completed in {execution_time:.2f}s "
                        f"(success={result.success}, code={result.return_code})"
                    )

                return result

            except asyncio.TimeoutError:
                end_time = time.time()
                execution_time = end_time - start_time

                error_msg = f"Command timed out after {timeout}s: {command}"
                if MOMO_LOGGER_AVAILABLE:
                    await self.logger.error(
                        f"Command timed out after {timeout}s",
                        context={
                            "command": command,
                            "timeout": timeout,
                            "execution_time": execution_time,
                            "session_id": context.session_id,
                        },
                        agent="command-executor",
                        agent_role="timeout_handler",
                    )
                else:
                    self.logger.error(error_msg)

                return MomCommandResult(
                    success=False,
                    return_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    command=command,
                    execution_time=execution_time,
                )

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            if MOMO_LOGGER_AVAILABLE:
                await self.logger.error(
                    f"Command execution failed",
                    context={
                        "command": command,
                        "execution_time": execution_time,
                        "session_id": context.session_id,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    },
                    exception=str(e),
                    agent="command-executor",
                    agent_role="error_handler",
                )
            else:
                self.logger.exception(f"Command execution failed: {e}")

            return MomCommandResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Command execution error: {str(e)}",
                command=command,
                execution_time=execution_time,
            )

    async def _execute_sync_command(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> MomCommandResult:
        """Execute command synchronously wrapped for async interface."""

        def run_in_executor():
            # Parse command for momo-mom execution
            parts = command.split()
            if not parts:
                return MomCommandResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr="Empty command",
                    command=command,
                )

            cmd_name = parts[0]
            target = parts[1] if len(parts) > 1 else ""
            args = tuple(parts[2:]) if len(parts) > 2 else ()

            # Execute through momo-mom
            try:
                success = self._executor.execute_command(cmd_name, target, args)

                # Note: momo-mom doesn't expose stdout/stderr directly
                # In a real implementation, we'd need to capture this
                return MomCommandResult(
                    success=success,
                    return_code=0 if success else 1,
                    stdout="Command completed",  # Placeholder
                    stderr="" if success else "Command failed",  # Placeholder
                    command=command,
                )

            except Exception as e:
                return MomCommandResult(
                    success=False,
                    return_code=1,
                    stdout="",
                    stderr=str(e),
                    command=command,
                )

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_in_executor)

    def validate_command(self, command: str) -> bool:
        """Validate command syntax and availability."""
        if not command or not command.strip():
            return False

        parts = command.strip().split()
        if not parts:
            return False

        cmd_name = parts[0]
        target = parts[1] if len(parts) > 1 else ""

        # Check if command mapping exists in momo-mom
        mapping = self._config_manager.get_command_mapping(cmd_name, target)
        return mapping is not None

    def estimate_command_duration(self, command: str) -> float:
        """Estimate command execution duration in seconds."""
        if not command:
            return 1.0

        cmd_base = command.split()[0] if command.split() else command

        # Use historical data if available
        if cmd_base in self._command_durations:
            return self._command_durations[cmd_base]

        # Default estimates based on command type
        duration_estimates = {
            "nx": 5.0,
            "npm": 10.0,
            "python": 2.0,
            "uv": 3.0,
            "git": 1.0,
            "ls": 0.1,
            "mkdir": 0.1,
            "cp": 0.5,
            "mv": 0.5,
        }

        return duration_estimates.get(cmd_base, 1.0)

    def get_execution_statistics(self) -> dict[str, any]:
        """Get command execution statistics."""
        success_rate = (
            self._success_count / self._execution_count
            if self._execution_count > 0
            else 0.0
        )
        avg_duration = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0
            else 0.0
        )

        return {
            "total_executions": self._execution_count,
            "successful_executions": self._success_count,
            "success_rate": success_rate,
            "total_execution_time": self._total_execution_time,
            "average_duration": avg_duration,
            "command_durations": self._command_durations.copy(),
        }

    def reset_statistics(self) -> None:
        """Reset execution statistics."""
        self._execution_count = 0
        self._success_count = 0
        self._total_execution_time = 0.0
        self._command_durations.clear()


# Convenience function for creating executor
def create_agent_command_executor(
    config_path: Optional[Path] = None,
    verbose: bool = False,
    logger=None,
) -> MomAgentCommandExecutor:
    """Create an agent command executor with default configuration."""
    return MomAgentCommandExecutor(
        config_path=config_path,
        verbose=verbose,
        ai_output=True,
        logger=logger,
    )
