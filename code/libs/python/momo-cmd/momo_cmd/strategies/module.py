"""
Module command strategy with intelligent fallback chains.

Executes module-specific commands with context awareness and fallback strategies.
"""

import subprocess
import shlex
from typing import TYPE_CHECKING, Optional, Tuple, List

if TYPE_CHECKING:
    from ..context import WorkspaceContext, ModuleInfo

from .base import ExecutionStrategy


class ContextAwareModuleStrategy(ExecutionStrategy):
    """Execute module-specific commands with intelligent fallbacks."""

    def __init__(self, command: str, args: List[str], context: "WorkspaceContext"):
        super().__init__(context)
        self.command = command
        self.args = args

    def execute(self) -> bool:
        target_module, extra_args = self._determine_target_module()

        if not target_module:
            return self._show_context_help()

        return self._execute_module_command(target_module, extra_args)

    def get_execution_preview(self) -> str:
        target_module, extra_args = self._determine_target_module()
        if target_module:
            return f"Execute {self.command} for {target_module}"
        else:
            return f"Execute {self.command} (context-dependent)"

    def _determine_target_module(self) -> Tuple[Optional[str], List[str]]:
        """Determine target module and remaining arguments."""

        # Case 1: Explicit module specified (mom test-fast momo-agent)
        if self.args:
            potential_module = self.args[0]

            # Check if first arg is actually a module name
            if self.context.get_module_info(potential_module):
                return potential_module, self.args[1:]
            else:
                # First arg might be command parameter, not module
                if self.context.current_module:
                    return self.context.current_module, self.args

        # Case 2: Context-aware execution (mom test-fast from within module)
        if self.context.current_module:
            return self.context.current_module, self.args

        return None, self.args

    def _execute_module_command(self, module: str, extra_args: List[str]) -> bool:
        """Execute command for specific module with fallback chain."""

        print(f"🎯 Executing {self.command} for {module}")

        # Strategy 1: Try nx command (highest priority)
        if self._try_nx_command(module, extra_args):
            return True

        # Strategy 2: Try uv command in module directory
        if self._try_uv_command(module, extra_args):
            return True

        # Strategy 3: Try common command patterns
        if self._try_common_patterns(module, extra_args):
            return True

        print(f"❌ No execution strategy found for {self.command} in {module}")
        self._show_available_commands(module)
        return False

    def _try_nx_command(self, module: str, extra_args: List[str]) -> bool:
        """Try executing as nx command."""
        cmd = f"nx run {module}:{self.command}"
        if extra_args:
            cmd += f" {' '.join(shlex.quote(arg) for arg in extra_args)}"

        # Quick check if command exists
        check_cmd = f"nx show project {module} 2>/dev/null | grep -q '{self.command}:'"
        check_result = subprocess.run(
            check_cmd, shell=True, capture_output=True, text=True
        )

        if check_result.returncode == 0:
            print(f"📦 Using nx: {cmd}")
            return self._execute_shell_command(cmd)

        return False

    def _try_uv_command(self, module: str, extra_args: List[str]) -> bool:
        """Try executing as uv command in module directory."""
        module_info = self.context.get_module_info(module)
        if not module_info or not module_info.has_uv:
            return False

        cmd = f"cd {module_info.path} && uv run {self.command}"
        if extra_args:
            cmd += f" {' '.join(shlex.quote(arg) for arg in extra_args)}"

        print(f"🐍 Using uv: {cmd}")
        return self._execute_shell_command(cmd)

    def _try_common_patterns(self, module: str, extra_args: List[str]) -> bool:
        """Try common command patterns as fallbacks."""
        module_info = self.context.get_module_info(module)
        if not module_info:
            return False

        patterns = {
            "test-fast": self._build_test_fast_command(module_info),
            "test-all": self._build_test_all_command(module_info),
            "format": self._build_format_command(module_info),
            "lint": self._build_lint_command(module_info),
            "typecheck": self._build_typecheck_command(module_info),
            "install": self._build_install_command(module_info),
            "benchmark": self._build_benchmark_command(module_info),
        }

        pattern_cmd = patterns.get(self.command)
        if pattern_cmd:
            if extra_args:
                pattern_cmd += f" {' '.join(shlex.quote(arg) for arg in extra_args)}"

            print(f"🔧 Using pattern: {pattern_cmd}")
            return self._execute_shell_command(pattern_cmd)

        return False

    def _build_test_fast_command(self, module_info: "ModuleInfo") -> str:
        """Build test-fast command for module."""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run pytest tests/unit tests/e2e -v"
        else:
            return f"cd {module_info.path} && pytest tests/unit tests/e2e -v"

    def _build_test_all_command(self, module_info: "ModuleInfo") -> str:
        """Build test-all command for module."""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run pytest tests/ --cov --cov-report=term-missing"
        else:
            return f"cd {module_info.path} && pytest tests/ --cov --cov-report=term-missing"

    def _build_format_command(self, module_info: "ModuleInfo") -> str:
        """Build format command for module."""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run ruff format ."
        else:
            return f"cd {module_info.path} && ruff format ."

    def _build_lint_command(self, module_info: "ModuleInfo") -> str:
        """Build lint command for module."""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run ruff check ."
        else:
            return f"cd {module_info.path} && ruff check ."

    def _build_typecheck_command(self, module_info: "ModuleInfo") -> str:
        """Build typecheck command for module."""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run pyright"
        else:
            return f"cd {module_info.path} && pyright"

    def _build_install_command(self, module_info: "ModuleInfo") -> str:
        """Build install command for module."""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv sync"
        elif module_info.has_npm:
            return f"cd {module_info.path} && npm install"
        else:
            return f"cd {module_info.path} && pip install -e ."

    def _build_benchmark_command(self, module_info: "ModuleInfo") -> str:
        """Build benchmark command for module."""
        benchmark_script = module_info.path / "benchmarks" / "performance_benchmarks.py"
        if benchmark_script.exists():
            if module_info.has_uv:
                return f"cd {module_info.path} && uv run python benchmarks/performance_benchmarks.py"
            else:
                return f"cd {module_info.path} && python benchmarks/performance_benchmarks.py"
        else:
            # Fallback to pytest benchmark
            if module_info.has_uv:
                return f"cd {module_info.path} && uv run pytest benchmarks/ -v"
            else:
                return f"cd {module_info.path} && pytest benchmarks/ -v"

    def _show_context_help(self) -> bool:
        """Show help when no module context available."""
        print(f"❌ Cannot determine target module for command: {self.command}")
        print()
        print("Options:")
        print(f"  1. Specify module explicitly: mom {self.command} <module-name>")
        print(f"  2. Run from within module directory")
        print(f"  3. Use --context to see current context")
        print()

        # Show available modules
        available_modules = self._get_available_modules()
        if available_modules:
            print("Available modules:")
            for module in available_modules[:5]:  # Show max 5
                print(f"  - {module}")

        return False

    def _show_available_commands(self, module: str) -> None:
        """Show available commands for the module."""
        module_info = self.context.get_module_info(module)
        if module_info:
            print(
                f"💡 Available commands for {module}: {', '.join(module_info.available_commands)}"
            )

    def _get_available_modules(self) -> List[str]:
        """Get list of available modules in the workspace."""
        modules = []

        # Check Python modules
        python_libs = self.context.workspace_root / "code" / "libs" / "python"
        if python_libs.exists():
            for item in python_libs.iterdir():
                if item.is_dir() and self.context._is_module_directory(item):
                    modules.append(item.name)

        # Check root-level modules
        for item in self.context.workspace_root.iterdir():
            if (
                item.is_dir()
                and item.name.startswith("momo-")
                and self.context._is_module_directory(item)
            ):
                modules.append(item.name)

        return sorted(modules)
