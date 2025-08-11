"""
Base classes for command execution strategies.

Defines the interface and common functionality for all execution strategies.
"""

import subprocess
import shlex
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import WorkspaceContext


class ExecutionStrategy(ABC):
    """Base class for command execution strategies."""

    def __init__(self, context: "WorkspaceContext"):
        self.context = context

    @abstractmethod
    def execute(self) -> bool:
        """Execute the command and return success status."""
        pass

    @abstractmethod
    def get_execution_preview(self) -> str:
        """Get human-readable preview of what will be executed."""
        pass

    def _execute_shell_command(
        self, command: str, cwd: Path = None, timeout: int = 300
    ) -> bool:
        """Execute shell command with comprehensive error handling."""
        cwd = cwd or self.context.workspace_root

        try:
            # Use subprocess with proper shell handling
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                timeout=timeout,
                capture_output=False,  # Stream output to console
            )
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"⏰ Command timed out after {timeout} seconds")
            return False
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return False


class FileExecutor(ABC):
    """Base class for file execution."""

    @abstractmethod
    def get_command(self, file_path: Path, args: list[str]) -> str:
        """Get shell command to execute this file."""
        pass


class PythonFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = " ".join(shlex.quote(arg) for arg in args)
        return f"python {file_path} {args_str}".strip()


class TypeScriptFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = " ".join(shlex.quote(arg) for arg in args)
        return f"npx tsx {file_path} {args_str}".strip()


class JavaScriptFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = " ".join(shlex.quote(arg) for arg in args)
        return f"node {file_path} {args_str}".strip()


class BashFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = " ".join(shlex.quote(arg) for arg in args)
        return f"bash {file_path} {args_str}".strip()
