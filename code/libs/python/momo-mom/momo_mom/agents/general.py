"""
General purpose agent for handling common interactive prompts.
"""

import re
from typing import Dict, Any, Optional
from .base import InteractiveAgent, ExecutionContext


class GeneralAgent(InteractiveAgent):
    """General purpose agent with built-in knowledge for common prompts."""
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        super().__init__("GeneralAgent", priority=10)
        self.model_config = model_config or {}
        self.response_patterns = self._build_response_patterns()
    
    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Can handle any command as fallback."""
        return True
    
    def handle_prompt(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Handle prompt using pattern matching and context."""
        
        try:
            # Try pattern-based responses first
            response = self._try_pattern_response(prompt, context)
            if response:
                self.record_usage(success=True)
                return response
            
            # Try model-based response if configured
            if self.model_config.get('enabled', False):
                response = self._try_model_response(prompt, command, context)
                if response:
                    self.record_usage(success=True)
                    return response
            
            # Fall back to safe defaults
            response = self._get_safe_default(prompt)
            self.record_usage(success=True)
            return response
            
        except Exception as e:
            self.record_usage(success=False)
            return self._get_safe_default(prompt)
    
    def _build_response_patterns(self) -> Dict[str, str]:
        """Build common response patterns."""
        
        return {
            # Confirmation patterns
            r'(?i).*continue.*\(y/n\)': 'y',
            r'(?i).*proceed.*\(y/n\)': 'y',
            r'(?i).*overwrite.*\(y/n\)': 'n',
            r'(?i).*delete.*\(y/n\)': 'n',
            
            # Version patterns
            r'(?i).*version.*:': '1.0.0',
            r'(?i).*initial version.*:': '0.1.0',
            
            # License patterns
            r'(?i).*license.*:': 'MIT',
            
            # Author patterns
            r'(?i).*author.*:': 'Developer',
            
            # Description patterns
            r'(?i).*description.*:': 'A new project',
            
            # Entry point patterns
            r'(?i).*entry.*point.*:': 'index.js',
            r'(?i).*main.*file.*:': 'main.py',
            
            # Test patterns
            r'(?i).*test.*command.*:': 'npm test',
            r'(?i).*test.*script.*:': 'pytest',
            
            # Repository patterns
            r'(?i).*repository.*:': '',
            r'(?i).*git.*repository.*:': '',
            
            # Keywords patterns
            r'(?i).*keywords.*:': '',
            
            # Package name patterns (use project context)
            r'(?i).*package.*name.*:': '{project_name}',
            r'(?i).*project.*name.*:': '{project_name}',
        }
    
    def _try_pattern_response(self, prompt: str, context: ExecutionContext) -> Optional[str]:
        """Try to match prompt against known patterns."""
        
        for pattern, response_template in self.response_patterns.items():
            if re.search(pattern, prompt):
                # Format response with context
                response = response_template.format(
                    project_name=context.project_info.get('name', 'my-project'),
                    project_type=context.project_info.get('type', 'library'),
                    author=context.user_preferences.get('author', 'Developer'),
                    email=context.user_preferences.get('email', ''),
                    license=context.user_preferences.get('license', 'MIT'),
                )
                return response
        
        return None
    
    def _try_model_response(self, prompt: str, command: str, context: ExecutionContext) -> Optional[str]:
        """Try to get response from configured model."""
        
        # This would integrate with actual model inference
        # For now, return None to fall back to safe defaults
        return None
    
    def _get_safe_default(self, prompt: str) -> str:
        """Provide safe default responses."""
        
        prompt_lower = prompt.lower()
        
        # Confirmation prompts - be conservative
        if any(phrase in prompt_lower for phrase in ['delete', 'remove', 'overwrite']):
            return 'n'
        
        if any(phrase in prompt_lower for phrase in ['continue', 'proceed', 'install']):
            return 'y'
        
        # Selection prompts - choose first option
        if re.search(r'\[1-9\]', prompt):
            return '1'
        
        # Default to empty (skip)
        return ''