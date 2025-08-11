"""
Passthrough command strategy with intelligent enhancements.

Executes arbitrary commands with useful enhancements for common tools.
"""

import shlex
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..context import WorkspaceContext

from .base import ExecutionStrategy


class PassthroughCommandStrategy(ExecutionStrategy):
    """Execute commands with intelligent enhancements."""

    def __init__(self, args: List[str], context: "WorkspaceContext"):
        super().__init__(context)
        self.args = args

    def execute(self) -> bool:
        enhanced_args = self._enhance_command(self.args)
        cmd = " ".join(shlex.quote(arg) for arg in enhanced_args)

        print(f"🔗 Passthrough: {cmd}")
        return self._execute_shell_command(cmd, cwd=self.context.workspace_root)

    def get_execution_preview(self) -> str:
        enhanced_args = self._enhance_command(self.args)
        return f"Execute: {' '.join(enhanced_args)}"

    def _enhance_command(self, args: List[str]) -> List[str]:
        """Add intelligent enhancements to common commands."""
        if not args:
            return args

        command = args[0]

        # Git command enhancements
        if command == "git":
            return self._enhance_git_command(args)

        # Find command enhancements
        if command == "find":
            return self._enhance_find_command(args)

        # Directory listing enhancements
        if command == "ls" and len(args) == 1:
            return ["ls", "-la", "--color=auto"]

        # Grep enhancements
        if command == "grep":
            return self._enhance_grep_command(args)

        # Tree enhancements
        if command == "tree" and len(args) == 1:
            return ["tree", "-I", "node_modules|__pycache__|.venv|.git"]

        return args

    def _enhance_git_command(self, args: List[str]) -> List[str]:
        """Enhance git commands with useful flags."""
        if len(args) >= 2:
            subcommand = args[1]

            # Git status with short and branch info
            if subcommand == "status" and len(args) == 2:
                return args + ["--short", "--branch"]

            # Git diff with stats
            elif subcommand == "diff" and len(args) == 2:
                return args + ["--stat"]

            # Git log with oneline, graph, and limited entries
            elif subcommand == "log" and len(args) == 2:
                return args + ["--oneline", "--graph", "-10"]

            # Git branch with verbose info
            elif subcommand == "branch" and len(args) == 2:
                return args + ["-v"]

            # Git remote with verbose info
            elif subcommand == "remote" and len(args) == 2:
                return args + ["-v"]

        return args

    def _enhance_find_command(self, args: List[str]) -> List[str]:
        """Enhance find commands to exclude common directories."""
        enhanced = args[:]

        # Check if we're searching for code files
        if any(
            pattern in arg
            for pattern in ["*.py", "*.js", "*.ts", "*.rs", "*.go"]
            for arg in args
        ):
            # Add exclusions for common directories
            exclusions = [
                "-not",
                "-path",
                "*/__pycache__/*",
                "-not",
                "-path",
                "*/.venv/*",
                "-not",
                "-path",
                "*/node_modules/*",
                "-not",
                "-path",
                "*/.git/*",
                "-not",
                "-path",
                "*/target/*",  # Rust
                "-not",
                "-path",
                "*/dist/*",
                "-not",
                "-path",
                "*/build/*",
            ]
            enhanced.extend(exclusions)

        return enhanced

    def _enhance_grep_command(self, args: List[str]) -> List[str]:
        """Enhance grep commands with useful options."""
        enhanced = args[:]

        # Add useful flags if not already present
        useful_flags = ["--color=auto", "-n", "-H"]
        for flag in useful_flags:
            if flag not in enhanced and flag.split("=")[0] not in enhanced:
                enhanced.insert(1, flag)  # Insert after 'grep'

        # Add exclusions for common directories
        if not any("--exclude-dir" in arg for arg in enhanced):
            enhanced.extend(
                [
                    "--exclude-dir=__pycache__",
                    "--exclude-dir=.venv",
                    "--exclude-dir=node_modules",
                    "--exclude-dir=.git",
                ]
            )

        return enhanced

    def _enhance_docker_command(self, args: List[str]) -> List[str]:
        """Enhance docker commands with useful defaults."""
        if len(args) >= 2:
            subcommand = args[1]

            # Docker ps with all containers and formatting
            if subcommand == "ps" and len(args) == 2:
                return args + [
                    "-a",
                    "--format",
                    "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}",
                ]

            # Docker images with formatting
            elif subcommand == "images" and len(args) == 2:
                return args + [
                    "--format",
                    "table {{.Repository}}:{{.Tag}}\\t{{.Size}}\\t{{.CreatedSince}}",
                ]

        return args

    def _enhance_npm_command(self, args: List[str]) -> List[str]:
        """Enhance npm commands."""
        if len(args) >= 2:
            subcommand = args[1]

            # npm list with depth limit
            if subcommand == "list" and "--depth" not in " ".join(args):
                return args + ["--depth=0"]

        return args
