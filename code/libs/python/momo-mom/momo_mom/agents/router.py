"""
Interactive agent router that manages command execution with agent mediation.
"""

import subprocess
import select
import sys
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

from .base import InteractiveAgent, ExecutionContext, CommandResult
from .registry import AgentRegistry


class InteractiveAgentRouter:
    """Routes interactive commands to appropriate agents."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.interaction_timeout = 30  # seconds

    def execute_command(self, command: str, context: ExecutionContext) -> CommandResult:
        """Execute command with agent-mediated interactive handling."""

        start_time = time.time()

        # Find appropriate agent
        agent = self.registry.find_agent(command, context)
        if not agent:
            return self._execute_non_interactive(command)

        # Execute with agent mediation
        result = self._execute_with_agent(command, context, agent)
        result.execution_time = time.time() - start_time
        result.agent_used = agent.name

        return result

    def _execute_with_agent(
        self, command: str, context: ExecutionContext, agent: InteractiveAgent
    ) -> CommandResult:
        """Execute command with agent handling interactive prompts."""

        interaction_log = []

        try:
            # Start process
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered
                cwd=context.working_directory,
            )

            stdout_data = []
            stderr_data = []

            while process.poll() is None:
                # Check for available output
                output = self._read_available_output(process)

                if output:
                    stdout_data.append(output)

                    # Check if this looks like a prompt
                    if self._is_interactive_prompt(output):
                        try:
                            # Get response from agent
                            response = agent.handle_prompt(output, command, context)

                            # Log the interaction
                            interaction_log.append(
                                {
                                    "prompt": output.strip(),
                                    "response": response,
                                    "agent": agent.name,
                                    "timestamp": time.time(),
                                }
                            )

                            # Send response to process
                            process.stdin.write(response + "\n")
                            process.stdin.flush()

                        except Exception as e:
                            # If agent fails, try safe default
                            safe_response = self._get_emergency_response(output)
                            process.stdin.write(safe_response + "\n")
                            process.stdin.flush()

                            interaction_log.append(
                                {
                                    "prompt": output.strip(),
                                    "response": safe_response,
                                    "agent": "emergency_fallback",
                                    "error": str(e),
                                    "timestamp": time.time(),
                                }
                            )

                # Small delay to prevent busy waiting
                time.sleep(0.1)

            # Get final output
            final_stdout, final_stderr = process.communicate()
            stdout_data.append(final_stdout)
            stderr_data.append(final_stderr)

            return CommandResult(
                stdout="".join(stdout_data),
                stderr="".join(stderr_data),
                returncode=process.returncode,
                interaction_log=interaction_log,
            )

        except Exception as e:
            return CommandResult(
                stdout="",
                stderr=f"Error executing command: {e}",
                returncode=1,
                interaction_log=interaction_log,
            )

    def _execute_non_interactive(self, command: str) -> CommandResult:
        """Execute command normally without agent mediation."""

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=300
            )

            return CommandResult(
                stdout=result.stdout, stderr=result.stderr, returncode=result.returncode
            )

        except subprocess.TimeoutExpired:
            return CommandResult(stdout="", stderr="Command timed out", returncode=124)
        except Exception as e:
            return CommandResult(
                stdout="", stderr=f"Error executing command: {e}", returncode=1
            )

    def _read_available_output(self, process: subprocess.Popen) -> str:
        """Read available output from process without blocking."""

        if sys.platform == "win32":
            # Windows doesn't support select on pipes
            return self._read_output_windows(process)
        else:
            return self._read_output_unix(process)

    def _read_output_unix(self, process: subprocess.Popen) -> str:
        """Read output on Unix systems using select."""

        ready, _, _ = select.select([process.stdout], [], [], 0.1)

        if ready:
            try:
                # Read available data
                data = process.stdout.read(1024)
                return data if data else ""
            except:
                return ""

        return ""

    def _read_output_windows(self, process: subprocess.Popen) -> str:
        """Read output on Windows (simplified approach)."""

        # This is a simplified approach for Windows
        # In production, you might want to use threading or asyncio
        try:
            # Try to read with a very short timeout
            import msvcrt

            if msvcrt.kbhit():
                return process.stdout.read(1024)
        except:
            pass

        return ""

    def _is_interactive_prompt(self, output: str) -> bool:
        """Detect if output contains an interactive prompt."""

        if not output.strip():
            return False

        # Common prompt indicators
        prompt_indicators = [
            "?",
            ":",
            "(y/n)",
            "(yes/no)",
            "enter",
            "input",
            "select",
            "choose",
            "continue?",
            "proceed?",
            "ok?",
        ]

        output_lower = output.lower()

        # Check for prompt indicators
        if any(indicator in output_lower for indicator in prompt_indicators):
            return True

        # Check if line ends with colon or question mark
        lines = output.strip().split("\n")
        last_line = lines[-1].strip()

        if last_line.endswith((":", "?", "> ")):
            return True

        return False

    def _get_emergency_response(self, prompt: str) -> str:
        """Emergency fallback response when all agents fail."""

        prompt_lower = prompt.lower()

        # Conservative responses for safety
        if any(phrase in prompt_lower for phrase in ["delete", "remove", "destroy"]):
            return "n"

        if "(y/n)" in prompt_lower:
            return "y"

        # Default to empty
        return ""
