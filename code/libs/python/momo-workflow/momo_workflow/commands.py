"""
Command registry and execution system for workflow steps.

This module provides a scientific approach to command management with:
- Type-safe command registration
- Execution metrics and error handling
- Pluggable command implementations
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .types import Command, ExecutionMetrics, StepResult, StepStatus, WorkflowContext


class CommandRegistry:
    """Thread-safe registry for workflow commands."""

    def __init__(self):
        """Initialize command registry."""
        self._commands: Dict[str, Command] = {}
        self._factories: Dict[str, Callable[..., Command]] = {}

    def register_command(self, name: str, command_class: Type[Command]) -> None:
        """Register a command class."""
        if name in self._commands:
            raise ValueError(f"Command '{name}' already registered")

        self._factories[name] = command_class

    def register_function(
        self, name: str, func: Callable, description: str = ""
    ) -> None:
        """Register a function as a command."""
        command = FunctionCommand(name, func, description)
        self._commands[name] = command

    def get_command(self, name: str) -> Optional[Command]:
        """Get command by name."""
        if name in self._commands:
            return self._commands[name]

        if name in self._factories:
            # Create command instance
            command = self._factories[name]()
            self._commands[name] = command
            return command

        return None

    def list_commands(self) -> List[str]:
        """List all registered command names."""
        return list(set(self._commands.keys()) | set(self._factories.keys()))

    def create_command_step(self, command_name: str, **kwargs) -> "CommandStep":
        """Create a workflow step from a registered command."""
        command = self.get_command(command_name)
        if not command:
            raise ValueError(f"Command '{command_name}' not found")

        return CommandStep(command, **kwargs)


# Global command registry
_global_registry = CommandRegistry()


def register_command(name: str, description: str = ""):
    """Decorator to register a function as a workflow command."""

    def decorator(func: Callable) -> Callable:
        _global_registry.register_function(name, func, description)
        return func

    return decorator


def get_command_registry() -> CommandRegistry:
    """Get the global command registry."""
    return _global_registry


class FunctionCommand:
    """Wrapper to make functions implement the Command protocol."""

    def __init__(self, name: str, func: Callable, description: str = ""):
        """Initialize function command."""
        self._name = name
        self._func = func
        self._description = description or func.__doc__ or "No description"

    @property
    def name(self) -> str:
        """Command name."""
        return self._name

    @property
    def description(self) -> str:
        """Command description."""
        return self._description

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the wrapped function."""
        try:
            result = self._func(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_args(self, **kwargs) -> bool:
        """Basic argument validation."""
        try:
            # Try calling with provided arguments
            import inspect

            sig = inspect.signature(self._func)
            sig.bind(**kwargs)
            return True
        except TypeError:
            return False


class ShellCommand:
    """Command that executes shell commands with proper error handling."""

    def __init__(self, name: str, command_template: str, description: str = ""):
        """Initialize shell command."""
        self._name = name
        self._command_template = command_template
        self._description = description

    @property
    def name(self) -> str:
        """Command name."""
        return self._name

    @property
    def description(self) -> str:
        """Command description."""
        return self._description

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute shell command with substitution."""
        try:
            # Substitute variables in command template
            command = self._command_template.format(**kwargs)

            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300),
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
            }

        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "error": f"Command timed out after {e.timeout}s",
                "command": command,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_args(self, **kwargs) -> bool:
        """Validate that all template variables are provided."""
        try:
            self._command_template.format(**kwargs)
            return True
        except KeyError:
            return False


class CommandStep:
    """Workflow step that executes a registered command."""

    def __init__(
        self,
        command: Command,
        step_id: Optional[str] = None,
        reversible: bool = False,
        rollback_command: Optional[Command] = None,
        **command_kwargs,
    ):
        """Initialize command step."""
        self._command = command
        self._step_id = step_id or f"cmd_{command.name}"
        self._reversible = reversible
        self._rollback_command = rollback_command
        self._command_kwargs = command_kwargs

    @property
    def step_id(self) -> str:
        """Step identifier."""
        return self._step_id

    @property
    def description(self) -> str:
        """Step description."""
        return f"Execute command: {self._command.description}"

    @property
    def is_reversible(self) -> bool:
        """Whether step can be rolled back."""
        return self._reversible and self._rollback_command is not None

    def validate_preconditions(self, context: WorkflowContext) -> bool:
        """Validate command arguments."""
        # Merge context variables with command kwargs
        args = {**context.variables, **self._command_kwargs}
        return self._command.validate_args(**args)

    def execute(self, context: WorkflowContext) -> StepResult:
        """Execute command and return result."""
        start_time = time.time()

        # Merge arguments
        args = {**context.variables, **self._command_kwargs}

        # Execute command
        command_result = self._command.execute(**args)

        # Create step result
        success = command_result.get("success", False)
        status = StepStatus.SUCCESS if success else StepStatus.FAILED
        error = (
            None if success else Exception(command_result.get("error", "Unknown error"))
        )

        # Store rollback data if reversible
        rollback_data = None
        if self.is_reversible and success:
            rollback_data = {
                "command_result": command_result,
                "context_snapshot": context.variables.copy(),
            }

        return StepResult(
            step_id=self.step_id,
            status=status,
            metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
            error=error,
            rollback_data=rollback_data,
        )

    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        """Execute rollback command if available."""
        if not self.is_reversible or not self._rollback_command:
            raise ValueError(f"Step {self.step_id} is not reversible")

        if result.rollback_data is None:
            raise ValueError("No rollback data available")

        # Execute rollback command
        args = {**context.variables, **self._command_kwargs}
        rollback_result = self._rollback_command.execute(**args)

        if not rollback_result.get("success", False):
            raise RuntimeError(f"Rollback failed: {rollback_result.get('error')}")

    def estimate_resources(self, context: WorkflowContext) -> Dict[str, float]:
        """Estimate resource requirements."""
        # Basic estimation - could be enhanced with command-specific logic
        return {"cpu_seconds": 5.0, "memory_mb": 50.0, "disk_mb": 10.0}


# Built-in commands for common operations
@register_command("create_directory", "Create a directory")
def create_directory(path: str) -> str:
    """Create a directory and return its path."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return str(dir_path.absolute())


@register_command("create_file", "Create a file with content")
def create_file(path: str, content: str = "") -> str:
    """Create a file with specified content."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return str(file_path.absolute())


@register_command("copy_file", "Copy a file")
def copy_file(source: str, destination: str) -> str:
    """Copy a file from source to destination."""
    import shutil

    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(dest_path.absolute())


@register_command("delete_path", "Delete a file or directory")
def delete_path(path: str) -> str:
    """Delete a file or directory."""
    import shutil

    path_obj = Path(path)
    if path_obj.is_file():
        path_obj.unlink()
    elif path_obj.is_dir():
        shutil.rmtree(path_obj)
    return str(path_obj.absolute())
