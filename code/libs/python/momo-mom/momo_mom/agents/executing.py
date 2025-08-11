"""
Executing agent that routes back to the main agent.
"""

from typing import Dict, Any
from .base import InteractiveAgent, ExecutionContext, AgentCallback


class ExecutingAgent(InteractiveAgent):
    """Routes interactive prompts back to the original executing agent."""
    
    def __init__(self, callback: AgentCallback):
        super().__init__("ExecutingAgent", priority=100)
        self.callback = callback
    
    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Only handle if no other agent can handle it (ultimate fallback)."""
        # ExecutingAgent should be the fallback, not the first choice
        # This will be called by the registry as last resort
        return True
    
    def handle_prompt(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Route back to executing agent with full context."""
        
        request = {
            'type': 'interactive_prompt',
            'prompt': prompt,
            'command': command,
            'context': {
                'current_task': context.current_task,
                'project_info': context.project_info,
                'working_directory': context.working_directory,
                'command_history': context.command_history[-5:],  # Last 5 commands
            },
            'message': self._build_prompt_message(prompt, command, context)
        }
        
        try:
            response = self.callback(request)
            self.record_usage(success=True)
            return response.strip()
        except Exception as e:
            self.record_usage(success=False)
            # Fallback to safe default
            return self._get_safe_default(prompt)
    
    def _build_prompt_message(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Build a comprehensive prompt message for the executing agent."""
        
        return f"""Interactive prompt encountered while executing command.

Command: {command}
Current Task: {context.current_task}
Working Directory: {context.working_directory}

Prompt from command:
{prompt}

Please provide the appropriate response to continue execution.
Consider the project context and provide a sensible default.
Respond with ONLY the input value needed, no explanation."""
    
    def _get_safe_default(self, prompt: str) -> str:
        """Provide safe default responses for common prompts."""
        
        prompt_lower = prompt.lower()
        
        # Common confirmation prompts
        if any(phrase in prompt_lower for phrase in ['continue?', 'proceed?', '(y/n)']):
            return 'y'
        
        # Version prompts
        if 'version' in prompt_lower:
            return '1.0.0'
        
        # License prompts
        if 'license' in prompt_lower:
            return 'MIT'
        
        # Default to empty (skip)
        return ''