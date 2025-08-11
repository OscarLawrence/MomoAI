"""
Main interactive system that integrates all agents.
"""

from typing import Dict, Any, Optional, Callable
from pathlib import Path
import os

from .agents import (
    AgentRegistry, InteractiveAgentRouter, ExecutingAgent, GeneralAgent,
    ExecutionContext, CommandResult, AgentCallback
)
from .agents.specialized import NpmAgent, GitAgent, DockerAgent, PythonAgent


class MomInteractiveSystem:
    """Main system integrating all interactive handling."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.registry = AgentRegistry()
        self.router = InteractiveAgentRouter(self.registry)
        self._setup_agents()
    
    def set_executing_agent_callback(self, callback: Callable[[Dict[str, Any]], str]):
        """Set the callback function for the executing agent."""
        if self.registry.executing_agent:
            self.registry.executing_agent.callback = AgentCallback(callback)
    
    def execute_command(self, command: str, context: ExecutionContext) -> CommandResult:
        """Execute command with interactive handling."""
        return self.router.execute_command(command, context)
    
    def _setup_agents(self):
        """Setup available agents based on configuration."""
        
        interactive_config = self.config.get('interactive', {})
        
        # 1. Register executing agent (highest priority)
        if interactive_config.get('enable_executing_agent', True):
            # Create with placeholder callback - will be set later
            executing_agent = ExecutingAgent(AgentCallback(lambda x: 'y'))
            self.registry.register_executing_agent(executing_agent)
        
        # 2. Register specialized agents
        if interactive_config.get('enable_specialized_agents', True):
            self._register_specialized_agents()
        
        # 3. Register general agent
        if interactive_config.get('enable_general_agent', True):
            general_config = interactive_config.get('general_agent', {})
            general_agent = GeneralAgent(general_config)
            self.registry.register_general_agent(general_agent)
        
        # 4. Register custom agents from plugins
        for plugin_config in interactive_config.get('plugins', []):
            agent = self._load_plugin_agent(plugin_config)
            if agent:
                self.registry.register_custom_agent(agent)
    
    def _register_specialized_agents(self):
        """Register all specialized agents."""
        
        # NPM Agent
        npm_patterns = [r'npm (init|create)', r'yarn (init|create)']
        for pattern in npm_patterns:
            self.registry.register_specialized_agent(pattern, NpmAgent())
        
        # Git Agent
        git_patterns = [r'git (commit|config|init|clone|merge|rebase)']
        for pattern in git_patterns:
            self.registry.register_specialized_agent(pattern, GitAgent())
        
        # Docker Agent
        docker_patterns = [r'docker (run|build|exec)', r'docker-compose']
        for pattern in docker_patterns:
            self.registry.register_specialized_agent(pattern, DockerAgent())
        
        # Python Agent
        python_patterns = [r'pip install', r'python setup\.py', r'poetry init', r'uv init']
        for pattern in python_patterns:
            self.registry.register_specialized_agent(pattern, PythonAgent())
    
    def _load_plugin_agent(self, plugin_config: Dict[str, Any]) -> Optional[object]:
        """Load custom agent from plugin configuration."""
        
        try:
            plugin_path = plugin_config.get('path')
            if not plugin_path:
                return None
            
            # This would implement dynamic plugin loading
            # For now, return None
            return None
            
        except Exception as e:
            print(f"Failed to load plugin agent: {e}")
            return None
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        return {
            'agents': self.registry.get_agent_stats(),
            'total_agents': len(self.registry.get_all_agents()),
        }
    
    def create_execution_context(self, current_task: str = "", **kwargs) -> ExecutionContext:
        """Create execution context with sensible defaults."""
        
        # Extract project info from current directory
        cwd = Path.cwd()
        project_info = self._extract_project_info(cwd)
        
        # Get user preferences from config
        user_preferences = self.config.get('user_preferences', {})
        
        return ExecutionContext(
            current_task=current_task,
            project_info=project_info,
            command_history=kwargs.get('command_history', []),
            environment_vars=dict(os.environ),
            working_directory=str(cwd),
            user_preferences=user_preferences,
            session_metadata=kwargs.get('session_metadata', {}),
        )
    
    def _extract_project_info(self, project_path: Path) -> Dict[str, Any]:
        """Extract project information from directory."""
        
        info = {
            'name': project_path.name,
            'path': str(project_path),
        }
        
        # Check for package.json
        package_json = project_path / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                    info.update({
                        'name': data.get('name', info['name']),
                        'version': data.get('version'),
                        'type': 'javascript',
                        'description': data.get('description'),
                    })
            except:
                pass
        
        # Check for pyproject.toml
        pyproject = project_path / 'pyproject.toml'
        if pyproject.exists():
            info['type'] = 'python'
            # Could parse TOML for more info
        
        # Check for Dockerfile
        dockerfile = project_path / 'Dockerfile'
        if dockerfile.exists():
            info['has_docker'] = True
        
        return info