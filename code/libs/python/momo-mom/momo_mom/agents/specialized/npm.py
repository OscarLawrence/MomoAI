"""
NPM specialized agent for handling npm interactive commands.
"""

import re
from typing import Optional
from ..base import InteractiveAgent, ExecutionContext


class NpmAgent(InteractiveAgent):
    """Specialized agent for npm commands."""
    
    def __init__(self):
        super().__init__("NpmAgent", priority=70)
    
    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Check if this is an npm command."""
        return any(cmd in command.lower() for cmd in ['npm init', 'npm create', 'yarn create', 'yarn init'])
    
    def handle_prompt(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Handle npm-specific prompts with project context."""
        
        try:
            response = self._get_npm_response(prompt, context)
            self.record_usage(success=True)
            return response
        except Exception as e:
            self.record_usage(success=False)
            return self._get_safe_default(prompt)
    
    def _get_npm_response(self, prompt: str, context: ExecutionContext) -> str:
        """Get npm-specific response based on prompt."""
        
        prompt_lower = prompt.lower()
        
        # Package name
        if 'package name' in prompt_lower or 'name:' in prompt_lower:
            return context.project_info.get('name', 'my-project')
        
        # Version
        if 'version' in prompt_lower:
            return context.project_info.get('version', '1.0.0')
        
        # Description
        if 'description' in prompt_lower:
            project_type = context.project_info.get('type', 'library')
            project_name = context.project_info.get('name', 'project')
            return f"A {project_type} project: {project_name}"
        
        # Entry point
        if 'entry point' in prompt_lower or 'main' in prompt_lower:
            project_type = context.project_info.get('type', 'library')
            if project_type == 'application':
                return 'src/index.js'
            else:
                return 'lib/index.js'
        
        # Test command
        if 'test command' in prompt_lower:
            return 'npm test'
        
        # Git repository
        if 'git repository' in prompt_lower or 'repository url' in prompt_lower:
            # Check if we're in a git repo
            git_remote = context.session_metadata.get('git_remote', '')
            return git_remote
        
        # Keywords
        if 'keywords' in prompt_lower:
            project_type = context.project_info.get('type', '')
            if project_type:
                return project_type
            return ''
        
        # Author
        if 'author' in prompt_lower:
            author = context.user_preferences.get('author', '')
            email = context.user_preferences.get('email', '')
            if author and email:
                return f"{author} <{email}>"
            return author or 'Developer'
        
        # License
        if 'license' in prompt_lower:
            return context.user_preferences.get('license', 'MIT')
        
        # Is this OK?
        if 'is this ok' in prompt_lower or 'is this okay' in prompt_lower:
            return 'yes'
        
        return self._get_safe_default(prompt)
    
    def _get_safe_default(self, prompt: str) -> str:
        """Safe defaults for npm prompts."""
        
        prompt_lower = prompt.lower()
        
        if any(phrase in prompt_lower for phrase in ['ok?', 'okay?', '(yes)']):
            return 'yes'
        
        if '(y/n)' in prompt_lower:
            return 'y'
        
        # Default to empty (use npm defaults)
        return ''