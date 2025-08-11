"""
Docker specialized agent for handling docker interactive commands.
"""

from ..base import InteractiveAgent, ExecutionContext


class DockerAgent(InteractiveAgent):
    """Specialized agent for docker commands."""
    
    def __init__(self):
        super().__init__("DockerAgent", priority=70)
    
    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Check if this is a docker command."""
        docker_commands = ['docker run', 'docker build', 'docker exec', 'docker-compose']
        return any(cmd in command.lower() for cmd in docker_commands)
    
    def handle_prompt(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Handle docker-specific prompts."""
        
        try:
            response = self._get_docker_response(prompt, context)
            self.record_usage(success=True)
            return response
        except Exception as e:
            self.record_usage(success=False)
            return self._get_safe_default(prompt)
    
    def _get_docker_response(self, prompt: str, context: ExecutionContext) -> str:
        """Get docker-specific response based on prompt."""
        
        prompt_lower = prompt.lower()
        
        # Container name
        if 'container name' in prompt_lower or 'name:' in prompt_lower:
            project_name = context.project_info.get('name', 'app')
            return f"{project_name}-container"
        
        # Port mapping
        if 'port' in prompt_lower:
            return '3000'  # Common default
        
        # Environment variables
        if 'environment' in prompt_lower or 'env' in prompt_lower:
            return 'production'
        
        # Volume mounting
        if 'volume' in prompt_lower or 'mount' in prompt_lower:
            return '/app'
        
        # Image selection
        if 'image' in prompt_lower or 'base image' in prompt_lower:
            return 'node:alpine'  # Common lightweight base
        
        # Continue/proceed prompts
        if 'continue' in prompt_lower or 'proceed' in prompt_lower:
            return 'y'
        
        return self._get_safe_default(prompt)
    
    def _get_safe_default(self, prompt: str) -> str:
        """Safe defaults for docker prompts."""
        
        prompt_lower = prompt.lower()
        
        # Be careful with destructive operations
        if any(phrase in prompt_lower for phrase in ['remove', 'delete', 'prune']):
            return 'n'
        
        if '(y/n)' in prompt_lower:
            return 'y'
        
        return ''