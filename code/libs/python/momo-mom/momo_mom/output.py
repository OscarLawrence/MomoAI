"""
AI-tailored output formatting system for Mom commands.
Provides structured, digestible output with smart filtering and expandable details.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib


@dataclass
class CommandOutput:
    """Structured command output for AI consumption."""

    command: str
    status: str  # "success", "error", "warning"
    summary: str
    head_lines: List[str]
    tail_lines: List[str]
    total_lines: int
    filtered_duplicates: int
    expandable_body: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class OutputFormatter:
    """AI-tailored output formatter with intelligent filtering and structuring."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_config = config.get("output", {})
        self.head_lines = self.output_config.get("head_lines", 10)
        self.tail_lines = self.output_config.get("tail_lines", 10)
        self.max_line_length = self.output_config.get("max_line_length", 200)
        self.duplicate_threshold = self.output_config.get("duplicate_threshold", 3)

        # Command-specific formatters
        self.command_formatters = {
            "test": self._format_test_output,
            "build": self._format_build_output,
            "lint": self._format_lint_output,
            "create": self._format_create_output,
            "install": self._format_install_output,
        }

        # Pattern-based formatters for command groups
        self.pattern_formatters = [
            (r"nx run.*:test", self._format_nx_test_output),
            (r"nx run.*:build", self._format_nx_build_output),
            (r"pytest.*", self._format_pytest_output),
            (r"npm.*", self._format_npm_output),
            (r"uv.*", self._format_uv_output),
        ]

    def format_output(
        self, command: str, stdout: str, stderr: str, returncode: int
    ) -> CommandOutput:
        """Format command output for AI consumption."""
        # Determine status
        status = "success" if returncode == 0 else "error"

        # Combine and clean output
        full_output = self._combine_output(stdout, stderr)
        cleaned_lines, filtered_count = self._clean_and_filter_lines(full_output)

        # Apply command-specific formatting
        formatted_output = self._apply_command_formatting(
            command, (cleaned_lines, filtered_count), status
        )

        if formatted_output:
            return formatted_output

        # Default formatting
        return self._format_default_output(
            command, (cleaned_lines, filtered_count), status
        )

    def _combine_output(self, stdout: str, stderr: str) -> List[str]:
        """Combine stdout and stderr intelligently."""
        lines = []

        if stdout:
            lines.extend(stdout.strip().split("\n"))

        if stderr:
            # Mark stderr lines for identification
            stderr_lines = [f"[STDERR] {line}" for line in stderr.strip().split("\n")]
            lines.extend(stderr_lines)

        return [line for line in lines if line.strip()]

    def _clean_and_filter_lines(self, lines: List[str]) -> Tuple[List[str], int]:
        """Clean and filter lines for AI consumption."""
        cleaned = []
        seen_hashes = {}

        for line in lines:
            # Truncate very long lines
            if len(line) > self.max_line_length:
                line = line[: self.max_line_length - 3] + "..."

            # Remove ANSI color codes
            line = re.sub(r"\x1b\[[0-9;]*m", "", line)

            # Skip empty lines
            if not line.strip():
                continue

            # Detect and filter duplicates
            line_hash = hashlib.md5(line.encode()).hexdigest()
            if line_hash in seen_hashes:
                seen_hashes[line_hash] += 1
                if seen_hashes[line_hash] <= self.duplicate_threshold:
                    cleaned.append(line)
            else:
                seen_hashes[line_hash] = 1
                cleaned.append(line)

        # Calculate filtered duplicates
        filtered_count = sum(
            max(0, count - self.duplicate_threshold) for count in seen_hashes.values()
        )

        return cleaned, filtered_count

    def _apply_command_formatting(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> Optional[CommandOutput]:
        """Apply command-specific formatting."""
        lines, filtered_count = lines_and_filtered

        # Try exact command match
        for cmd_pattern, formatter in self.command_formatters.items():
            if cmd_pattern in command:
                return formatter(command, lines_and_filtered, status)

        # Try pattern matching
        for pattern, formatter in self.pattern_formatters:
            if re.search(pattern, command):
                return formatter(command, lines_and_filtered, status)

        return None

    def _format_default_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Default output formatting."""
        lines, filtered_count = lines_and_filtered

        total_lines = len(lines)

        # Extract head and tail
        if total_lines <= (self.head_lines + self.tail_lines):
            head_lines = lines
            tail_lines = []
            expandable_body = None
        else:
            head_lines = lines[: self.head_lines]
            tail_lines = lines[-self.tail_lines :]
            expandable_body = "\n".join(lines[self.head_lines : -self.tail_lines])

        # Generate summary
        summary = self._generate_summary(command, lines, status)

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=head_lines,
            tail_lines=tail_lines,
            total_lines=total_lines,
            filtered_duplicates=filtered_count,
            expandable_body=expandable_body,
        )

    def _format_test_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format test command output."""
        lines, filtered_count = lines_and_filtered

        # Extract test results
        test_summary = self._extract_test_summary(lines)

        # Find important lines (failures, errors)
        important_lines = []
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["failed", "error", "assertion", "traceback"]
            ):
                important_lines.append(line)

        summary = f"Tests: {test_summary.get('status', 'unknown')} - {test_summary.get('passed', 0)} passed, {test_summary.get('failed', 0)} failed"

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=lines[:5] + important_lines[:5],
            tail_lines=lines[-5:],
            total_lines=len(lines),
            filtered_duplicates=filtered_count,
            expandable_body="\n".join(lines[10:-5]) if len(lines) > 15 else None,
            metadata=test_summary,
        )

    def _format_build_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format build command output."""
        lines, filtered_count = lines_and_filtered

        # Extract build info
        build_info = self._extract_build_info(lines)

        # Focus on errors and warnings
        important_lines = []
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["error", "warning", "built", "compiled"]
            ):
                important_lines.append(line)

        summary = (
            f"Build: {status} - {build_info.get('artifacts', 'unknown')} artifacts"
        )

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=important_lines[:10],
            tail_lines=lines[-5:],
            total_lines=len(lines),
            filtered_duplicates=filtered_count,
            metadata=build_info,
        )

    def _format_pytest_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format pytest-specific output."""
        lines, filtered_count = lines_and_filtered

        # Parse pytest output
        test_results = self._parse_pytest_output(lines)

        # Extract failure details
        failure_lines = []
        in_failure = False
        for line in lines:
            if "FAILURES" in line or "ERRORS" in line:
                in_failure = True
            elif in_failure and line.startswith("="):
                in_failure = False
            elif in_failure:
                failure_lines.append(line)

        summary = f"Pytest: {test_results['passed']} passed, {test_results['failed']} failed, {test_results['skipped']} skipped"

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=lines[:3] + failure_lines[:7],
            tail_lines=lines[-3:],
            total_lines=len(lines),
            filtered_duplicates=filtered_count,
            expandable_body="\n".join(failure_lines[7:])
            if len(failure_lines) > 7
            else None,
            metadata=test_results,
        )

    def _format_nx_test_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format Nx test command output."""
        return self._format_test_output(
            command, lines_and_filtered, status, filtered_count
        )

    def _format_nx_build_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format Nx build command output."""
        return self._format_build_output(
            command, lines_and_filtered, status, filtered_count
        )

    def _format_lint_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format lint command output."""
        lines, filtered_count = lines_and_filtered

        # Extract lint issues
        issues = []
        for line in lines:
            if re.search(r":\d+:\d+:", line):  # File:line:col pattern
                issues.append(line)

        summary = (
            f"Lint: {len(issues)} issues found" if issues else "Lint: No issues found"
        )

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=issues[:10],
            tail_lines=lines[-3:],
            total_lines=len(lines),
            filtered_duplicates=filtered_count,
            expandable_body="\n".join(issues[10:]) if len(issues) > 10 else None,
            metadata={"issues_count": len(issues)},
        )

    def _format_create_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format create command output."""
        lines, filtered_count = lines_and_filtered

        # Extract created files
        created_files = []
        for line in lines:
            if "CREATE" in line or "created" in line.lower():
                created_files.append(line)

        summary = f"Created: {len(created_files)} files/directories"

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=created_files,
            tail_lines=lines[-3:],
            total_lines=len(lines),
            filtered_duplicates=filtered_count,
            metadata={"created_files": len(created_files)},
        )

    def _format_install_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format install command output."""
        lines, filtered_count = lines_and_filtered

        # Extract package info
        packages = []
        for line in lines:
            if "+" in line and any(
                keyword in line for keyword in ["installed", "added", "updated"]
            ):
                packages.append(line)

        summary = f"Install: {len(packages)} packages processed"

        return CommandOutput(
            command=command,
            status=status,
            summary=summary,
            head_lines=packages[:10],
            tail_lines=lines[-3:],
            total_lines=len(lines),
            filtered_duplicates=filtered_count,
            metadata={"packages_count": len(packages)},
        )

    def _format_npm_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format npm command output."""
        return self._format_install_output(
            command, lines_and_filtered, status, filtered_count
        )

    def _format_uv_output(
        self, command: str, lines_and_filtered: Tuple[List[str], int], status: str
    ) -> CommandOutput:
        """Format uv command output."""
        return self._format_install_output(
            command, lines_and_filtered, status, filtered_count
        )

    def _extract_test_summary(self, lines: List[str]) -> Dict[str, Any]:
        """Extract test summary information."""
        summary = {"passed": 0, "failed": 0, "skipped": 0, "status": "unknown"}

        for line in lines:
            # Look for test result patterns
            if "passed" in line and "failed" in line:
                # Try to extract numbers
                numbers = re.findall(r"\d+", line)
                if len(numbers) >= 2:
                    summary["passed"] = int(numbers[0])
                    summary["failed"] = int(numbers[1])
                    summary["status"] = "completed"

        return summary

    def _extract_build_info(self, lines: List[str]) -> Dict[str, Any]:
        """Extract build information."""
        info = {"artifacts": 0, "warnings": 0, "errors": 0}

        for line in lines:
            if "built" in line.lower() or "compiled" in line.lower():
                info["artifacts"] += 1
            if "warning" in line.lower():
                info["warnings"] += 1
            if "error" in line.lower():
                info["errors"] += 1

        return info

    def _parse_pytest_output(self, lines: List[str]) -> Dict[str, int]:
        """Parse pytest output for test results."""
        results = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}

        for line in lines:
            if "passed" in line and (
                "failed" in line or "error" in line or "skipped" in line
            ):
                # Parse summary line like "5 passed, 2 failed, 1 skipped"
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "passed" in part:
                        results["passed"] = int(re.search(r"\d+", part).group())
                    elif "failed" in part:
                        results["failed"] = int(re.search(r"\d+", part).group())
                    elif "skipped" in part:
                        results["skipped"] = int(re.search(r"\d+", part).group())
                    elif "error" in part:
                        results["errors"] = int(re.search(r"\d+", part).group())
                break

        return results

    def _generate_summary(self, command: str, lines: List[str], status: str) -> str:
        """Generate a concise summary of the command execution."""
        if not lines:
            return f"Command '{command}' completed with {status}"

        # Look for key indicators
        if status == "error":
            error_line = next((line for line in lines if "error" in line.lower()), None)
            if error_line:
                return f"Error: {error_line[:100]}..."

        # Default summary
        return f"Command '{command}' {status} - {len(lines)} lines of output"


class AIOutputRenderer:
    """Renders formatted output for AI consumption."""

    def __init__(self, format_type: str = "structured"):
        self.format_type = format_type  # "structured", "json", "markdown"

    def render(self, output: CommandOutput) -> str:
        """Render formatted output."""
        if self.format_type == "json":
            return self._render_json(output)
        elif self.format_type == "markdown":
            return self._render_markdown(output)
        else:
            return self._render_structured(output)

    def _render_structured(self, output: CommandOutput) -> str:
        """Render structured text output."""
        lines = []

        # Status header
        status_emoji = "✅" if output.status == "success" else "❌"
        lines.append(f"{status_emoji} {output.summary}")

        if output.filtered_duplicates > 0:
            lines.append(f"🔄 Filtered {output.filtered_duplicates} duplicate lines")

        # Head output
        if output.head_lines:
            lines.append("\n📋 Output (head):")
            for line in output.head_lines:
                lines.append(f"  {line}")

        # Expandable body indicator
        if output.expandable_body:
            lines.append(
                f"\n⚡ {len(output.expandable_body.split())} lines available (use --expand for full output)"
            )

        # Tail output
        if output.tail_lines:
            lines.append("\n📋 Output (tail):")
            for line in output.tail_lines:
                lines.append(f"  {line}")

        # Metadata
        if output.metadata:
            lines.append(f"\n📊 Metadata: {output.metadata}")

        return "\n".join(lines)

    def _render_json(self, output: CommandOutput) -> str:
        """Render JSON output."""
        return json.dumps(output.to_dict(), indent=2)

    def _render_markdown(self, output: CommandOutput) -> str:
        """Render markdown output."""
        lines = []

        # Header
        status_emoji = "✅" if output.status == "success" else "❌"
        lines.append(f"## {status_emoji} {output.summary}")

        # Head output
        if output.head_lines:
            lines.append("\n### Output (Head)")
            lines.append("```")
            lines.extend(output.head_lines)
            lines.append("```")

        # Expandable body
        if output.expandable_body:
            lines.append(
                f"\n<details><summary>Full Output ({output.total_lines} lines)</summary>"
            )
            lines.append("\n```")
            lines.append(output.expandable_body)
            lines.append("```")
            lines.append("</details>")

        # Tail output
        if output.tail_lines:
            lines.append("\n### Output (Tail)")
            lines.append("```")
            lines.extend(output.tail_lines)
            lines.append("```")

        return "\n".join(lines)
