"""
Command execution engine with shell-first approach and pluggable language entry points.
"""

import subprocess
import shlex
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re

try:
    from momo_logger import get_logger
    from momo_logger.types import LogLevel

    MOMO_LOGGER_AVAILABLE = True
except ImportError:
    MOMO_LOGGER_AVAILABLE = False

from .output import OutputFormatter, AIOutputRenderer, CommandOutput
from .interactive import MomInteractiveSystem


class CommandExecutor:
    """Executes commands with shell-first approach and intelligent fallbacks."""

    def __init__(
        self, config: Dict[str, Any], verbose: bool = False, ai_output: bool = True
    ):
        self.config = config
        self.verbose = verbose
        self.ai_output = ai_output
        self.execution_config = config.get("execution", {})
        self.recovery_config = config.get("recovery", {})

        # Initialize logging
        if MOMO_LOGGER_AVAILABLE:
            self.logger = get_logger("momo-mom.executor", level=LogLevel.AI_AGENT)
        else:
            self.logger = None

        # Initialize AI output formatting
        self.output_formatter = OutputFormatter(config)
        output_format = config.get("output", {}).get("format", "structured")
        self.output_renderer = AIOutputRenderer(output_format)

        # Initialize interactive system
        self.interactive_system = MomInteractiveSystem(config)

    def execute_command(self, command: str, target: str, args: Tuple[str, ...]) -> bool:
        """Execute a mapped command with fallback strategies."""
        from .config import ConfigManager

        config_manager = ConfigManager()
        command_mapping = config_manager.get_command_mapping(command, target)

        if not command_mapping:
            self._log(f"No mapping found for command '{command}'")
            return False

        # Build context for parameter substitution
        context = {
            "target": target,
            "name": target,
            "args": " ".join(args),
            **dict(os.environ),  # Include environment variables
        }

        # Try primary command
        primary_cmd = command_mapping.get("primary")
        if primary_cmd:
            success = self._execute_with_retries(primary_cmd, context, target)
            if success:
                return True

        # Try fallback command
        fallback_cmd = command_mapping.get("fallback")
        if fallback_cmd:
            self._log("Primary command failed, trying fallback...")
            success = self._execute_with_retries(fallback_cmd, context, target)
            if success:
                return True

        self._log(f"All execution strategies failed for command '{command}'")
        return False

    def execute_script(self, script_path: Path, args: Tuple[str, ...]) -> bool:
        """Execute a script with appropriate interpreter."""
        if not script_path.exists():
            self._log(f"Script not found: {script_path}")
            return False

        # Determine execution method
        if script_path.suffix == ".py":
            cmd = f"python {script_path} {' '.join(args)}"
        elif script_path.suffix == ".sh":
            cmd = f"bash {script_path} {' '.join(args)}"
        elif script_path.suffix == ".js":
            cmd = f"node {script_path} {' '.join(args)}"
        elif script_path.suffix == ".ts":
            cmd = f"npx tsx {script_path} {' '.join(args)}"
        elif os.access(script_path, os.X_OK):
            # Executable file
            cmd = f"{script_path} {' '.join(args)}"
        else:
            # Try to detect shebang
            try:
                with open(script_path, "r") as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("#!"):
                        interpreter = first_line[2:].strip()
                        cmd = f"{interpreter} {script_path} {' '.join(args)}"
                    else:
                        self._log(f"Cannot determine how to execute: {script_path}")
                        return False
            except Exception as e:
                self._log(f"Error reading script {script_path}: {e}")
                return False

        return self._execute_shell_command(cmd, cwd=script_path.parent)

    def _execute_with_retries(
        self, command_template: str, context: Dict[str, Any], current_task: str = ""
    ) -> bool:
        """Execute command with retry logic and auto-recovery."""
        retry_count = self.execution_config.get("retry_count", 2)
        auto_reset = self.execution_config.get("auto_reset_on_cache_failure", True)

        for attempt in range(retry_count + 1):
            if attempt > 0:
                self._log(f"Retry attempt {attempt}/{retry_count}")

                # Auto-recovery on cache failures
                if auto_reset and self._is_cache_failure_likely():
                    self._run_recovery_commands()

            # Substitute parameters in command
            command = self._substitute_parameters(command_template, context)

            success = self._execute_shell_command(command, current_task=current_task)
            if success:
                return True

        return False

    def _execute_shell_command(
        self, command: str, cwd: Optional[Path] = None, current_task: str = ""
    ) -> bool:
        """Execute a shell command with interactive handling and AI-tailored output formatting."""
        if self.verbose:
            self._log(f"Executing: {command}")
            if cwd:
                self._log(f"Working directory: {cwd}")

        try:
            # Create execution context for interactive handling
            context = self.interactive_system.create_execution_context(
                current_task=current_task,
                session_metadata={"cwd": str(cwd) if cwd else str(Path.cwd())},
            )

            # Execute with interactive handling
            result = self.interactive_system.execute_command(command, context)

            # Format output for AI consumption
            if self.ai_output:
                formatted_output = self.output_formatter.format_output(
                    command, result.stdout, result.stderr, result.returncode
                )

                # Add interaction information if there were any
                if result.had_interactions:
                    if not formatted_output.metadata:
                        formatted_output.metadata = {}
                    formatted_output.metadata["interactions"] = len(
                        result.interaction_log
                    )
                    formatted_output.metadata["agent_used"] = result.agent_used
                    formatted_output.summary += f" (handled {len(result.interaction_log)} interactive prompts via {result.agent_used})"

                rendered_output = self.output_renderer.render(formatted_output)
                print(rendered_output)
            else:
                # Traditional output
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)

            return result.success

        except Exception as e:
            self._log(f"Command execution failed: {e}")
            return False

    def _substitute_parameters(self, template: str, context: Dict[str, Any]) -> str:
        """Substitute parameters in command template."""

        # Simple parameter substitution using {param} syntax
        def replace_param(match):
            param_name = match.group(1)
            if param_name in context:
                return str(context[param_name])
            else:
                self._log(f"Warning: Parameter '{param_name}' not found in context")
                return match.group(0)  # Return original if not found

        return re.sub(r"\{(\w+)\}", replace_param, template)

    def _is_cache_failure_likely(self) -> bool:
        """Heuristic to detect if failure might be due to cache issues."""
        # This could be enhanced with more sophisticated detection
        # For now, we'll assume any nx-related failure might be cache-related
        return True  # Conservative approach - always try recovery

    def _run_recovery_commands(self):
        """Run recovery commands (e.g., nx reset)."""
        recovery_commands = self.recovery_config

        for name, command in recovery_commands.items():
            self._log(f"Running recovery command '{name}': {command}")
            self._execute_shell_command(command)

    def _log(self, message: str, level: str = "info"):
        """Log message with momo-logger or fallback to stderr."""
        if MOMO_LOGGER_AVAILABLE and self.logger:
            log_level = getattr(LogLevel, level.upper(), LogLevel.AI_AGENT)
            self.logger._sync_log(
                log_level,
                message,
                context={"component": "mom-executor"},
                agent="mom",
                agent_role="command_executor",
            )
        else:
            print(f"[mom] {message}", file=sys.stderr)


class LanguageEntryPoint:
    """Base class for language-specific entry points."""

    def can_handle(self, file_path: Path) -> bool:
        """Check if this entry point can handle the given file."""
        raise NotImplementedError

    def get_execution_command(self, file_path: Path, args: List[str]) -> str:
        """Get the shell command to execute this file."""
        raise NotImplementedError


class PythonEntryPoint(LanguageEntryPoint):
    """Python script execution."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def get_execution_command(self, file_path: Path, args: List[str]) -> str:
        return f"python {file_path} {' '.join(shlex.quote(arg) for arg in args)}"


class NodeEntryPoint(LanguageEntryPoint):
    """Node.js script execution."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix in [".js", ".mjs"]

    def get_execution_command(self, file_path: Path, args: List[str]) -> str:
        return f"node {file_path} {' '.join(shlex.quote(arg) for arg in args)}"


class TypeScriptEntryPoint(LanguageEntryPoint):
    """TypeScript script execution."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == ".ts"

    def get_execution_command(self, file_path: Path, args: List[str]) -> str:
        return f"npx tsx {file_path} {' '.join(shlex.quote(arg) for arg in args)}"


class BashEntryPoint(LanguageEntryPoint):
    """Bash script execution."""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == ".sh"

    def get_execution_command(self, file_path: Path, args: List[str]) -> str:
        return f"bash {file_path} {' '.join(shlex.quote(arg) for arg in args)}"


# Registry of available entry points
DEFAULT_ENTRY_POINTS = [
    PythonEntryPoint(),
    NodeEntryPoint(),
    TypeScriptEntryPoint(),
    BashEntryPoint(),
]
