"""
Python specialized agent for handling python interactive commands.
"""

from ..base import InteractiveAgent, ExecutionContext


class PythonAgent(InteractiveAgent):
    """Specialized agent for python commands."""

    def __init__(self):
        super().__init__("PythonAgent", priority=70)

    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Check if this is a python command."""
        python_commands = ["pip install", "python setup.py", "poetry init", "uv init"]
        return any(cmd in command.lower() for cmd in python_commands)

    def handle_prompt(
        self, prompt: str, command: str, context: ExecutionContext
    ) -> str:
        """Handle python-specific prompts."""

        try:
            response = self._get_python_response(prompt, context)
            self.record_usage(success=True)
            return response
        except Exception as e:
            self.record_usage(success=False)
            return self._get_safe_default(prompt)

    def _get_python_response(self, prompt: str, context: ExecutionContext) -> str:
        """Get python-specific response based on prompt."""

        prompt_lower = prompt.lower()

        # Package name
        if "package name" in prompt_lower or "project name" in prompt_lower:
            return context.project_info.get("name", "my-package")

        # Version
        if "version" in prompt_lower:
            return "0.1.0"

        # Description
        if "description" in prompt_lower:
            return f"Python package: {context.project_info.get('name', 'my-package')}"

        # Author
        if "author" in prompt_lower:
            return context.user_preferences.get("author", "Developer")

        # License
        if "license" in prompt_lower:
            return context.user_preferences.get("license", "MIT")

        # Python version
        if "python version" in prompt_lower or "requires-python" in prompt_lower:
            return ">=3.8"

        # Dependencies
        if "dependencies" in prompt_lower:
            return ""  # Start with no dependencies

        # Entry points
        if "entry point" in prompt_lower or "console_scripts" in prompt_lower:
            return ""

        # Continue prompts
        if "continue" in prompt_lower or "proceed" in prompt_lower:
            return "y"

        return self._get_safe_default(prompt)

    def _get_safe_default(self, prompt: str) -> str:
        """Safe defaults for python prompts."""

        prompt_lower = prompt.lower()

        if "(y/n)" in prompt_lower:
            return "y"

        return ""
