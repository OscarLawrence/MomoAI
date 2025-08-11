"""
Command detection system for intelligent command classification.

Detectors analyze command arguments and determine the appropriate
execution strategy through a priority-based chain.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .context import WorkspaceContext
    from .strategies.base import ExecutionStrategy


class CommandDetector(ABC):
    """Base class for command detectors."""

    @abstractmethod
    def can_handle(self, args: List[str], context: "WorkspaceContext") -> bool:
        """Check if this detector can handle the command."""
        pass

    @abstractmethod
    def create_strategy(
        self, args: List[str], context: "WorkspaceContext"
    ) -> "ExecutionStrategy":
        """Create appropriate execution strategy."""
        pass


class CommandDetectorRegistry:
    """Registry of command detectors for intelligent routing."""

    def __init__(self):
        # Import strategies here to avoid circular imports
        from .strategies.file import ContextAwareFileStrategy
        from .strategies.module import ContextAwareModuleStrategy
        from .strategies.passthrough import PassthroughCommandStrategy

        self.detectors = [
            FileExecutionDetector(),  # Highest priority
            ModuleCommandDetector(),  # Module-specific commands
            ToolchainCommandDetector(),  # nx, npm, cargo, etc.
            PassthroughDetector(),  # Lowest priority - catch-all
        ]

    def get_detectors(self) -> List["CommandDetector"]:
        return self.detectors


class FileExecutionDetector(CommandDetector):
    """Detect direct file execution: mom test.py, mom build.ts"""

    def can_handle(self, args: List[str], context: "WorkspaceContext") -> bool:
        if not args:
            return False

        first_arg = args[0]

        # Check if it's a file path (has extension)
        if "." not in first_arg:
            return False

        # Check if file exists (resolve relative paths)
        file_path = self._resolve_path(first_arg, context.cwd)
        return file_path.exists() and file_path.is_file()

    def create_strategy(self, args: List[str], context: "WorkspaceContext"):
        from .strategies.file import ContextAwareFileStrategy

        return ContextAwareFileStrategy(args[0], args[1:], context)

    def _resolve_path(self, filename: str, cwd: Path) -> Path:
        """Resolve file path relative to current directory."""
        file_path = Path(filename)
        if not file_path.is_absolute():
            file_path = cwd / file_path
        return file_path.resolve()


class ModuleCommandDetector(CommandDetector):
    """Detect module commands: mom test-fast, mom format momo-agent"""

    COMMON_MODULE_COMMANDS = {
        "test-fast",
        "test-all",
        "format",
        "lint",
        "typecheck",
        "install",
        "benchmark",
        "build",
        "clean",
    }

    def can_handle(self, args: List[str], context: "WorkspaceContext") -> bool:
        if not args:
            return False

        command = args[0]

        # Check if it's a known module command
        if command in self.COMMON_MODULE_COMMANDS:
            return True

        # Check if it's available in current module context
        if context.current_module:
            module_info = context.get_module_info()
            if module_info and command in module_info.available_commands:
                return True

        return False

    def create_strategy(self, args: List[str], context: "WorkspaceContext"):
        from .strategies.module import ContextAwareModuleStrategy

        return ContextAwareModuleStrategy(args[0], args[1:], context)


class ToolchainCommandDetector(CommandDetector):
    """Detect toolchain commands: mom nx run, mom npm install"""

    TOOLCHAIN_COMMANDS = {"nx", "npm", "pnpm", "yarn", "cargo", "go", "make"}

    def can_handle(self, args: List[str], context: "WorkspaceContext") -> bool:
        if not args:
            return False

        return args[0] in self.TOOLCHAIN_COMMANDS

    def create_strategy(self, args: List[str], context: "WorkspaceContext"):
        from .strategies.passthrough import PassthroughCommandStrategy

        return PassthroughCommandStrategy(args, context)


class PassthroughDetector(CommandDetector):
    """Catch-all detector for arbitrary commands."""

    def can_handle(self, args: List[str], context: "WorkspaceContext") -> bool:
        # Always can handle as a fallback
        return True

    def create_strategy(self, args: List[str], context: "WorkspaceContext"):
        from .strategies.passthrough import PassthroughCommandStrategy

        return PassthroughCommandStrategy(args, context)
