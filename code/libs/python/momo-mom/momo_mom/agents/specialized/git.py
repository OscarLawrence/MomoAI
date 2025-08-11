"""
Git specialized agent for handling git interactive commands.
"""

from ..base import InteractiveAgent, ExecutionContext


class GitAgent(InteractiveAgent):
    """Specialized agent for git commands."""
    
    def __init__(self):
        super().__init__("GitAgent", priority=70)
    
    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Check if this is a git command."""
        git_commands = ['git commit', 'git config', 'git init', 'git clone', 'git merge', 'git rebase']
        return any(cmd in command.lower() for cmd in git_commands)
    
    def handle_prompt(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Handle git-specific prompts."""
        
        try:
            response = self._get_git_response(prompt, context)
            self.record_usage(success=True)
            return response
        except Exception as e:
            self.record_usage(success=False)
            return self._get_safe_default(prompt)
    
    def _get_git_response(self, prompt: str, context: ExecutionContext) -> str:
        """Get git-specific response based on prompt."""
        
        prompt_lower = prompt.lower()
        
        # Commit message
        if 'commit message' in prompt_lower or 'enter message' in prompt_lower:
            task = context.current_task
            if task:
                return f"feat: {task}"
            return "chore: update files"
        
        # Username configuration
        if 'user.name' in prompt_lower or 'username' in prompt_lower:
            return context.user_preferences.get('git_username', 'Developer')
        
        # Email configuration
        if 'user.email' in prompt_lower or 'email' in prompt_lower:
            return context.user_preferences.get('git_email', 'dev@example.com')
        
        # Editor choice
        if 'editor' in prompt_lower:
            return context.user_preferences.get('editor', 'nano')
        
        # Merge conflict resolution
        if 'merge' in prompt_lower and 'conflict' in prompt_lower:
            return 'abort'  # Safe default
        
        # Continue/abort prompts
        if 'continue' in prompt_lower:
            return 'y'
        
        if 'abort' in prompt_lower:
            return 'n'
        
        # Branch name
        if 'branch name' in prompt_lower:
            task = context.current_task.lower().replace(' ', '-') if context.current_task else 'feature'
            return f"feature/{task}"
        
        return self._get_safe_default(prompt)
    
    def _get_safe_default(self, prompt: str) -> str:
        """Safe defaults for git prompts."""
        
        prompt_lower = prompt.lower()
        
        # Be conservative with destructive operations
        if any(phrase in prompt_lower for phrase in ['delete', 'remove', 'force', 'reset --hard']):
            return 'n'
        
        # Continue with safe operations
        if any(phrase in prompt_lower for phrase in ['continue', 'proceed']):
            return 'y'
        
        # Default to empty
        return ''