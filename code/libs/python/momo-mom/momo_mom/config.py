"""
Configuration management for Mom command mapping system.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import os


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = self._find_config_file(config_path)
        self.config = self._load_config()
    
    def _find_config_file(self, explicit_path: Optional[str] = None) -> Optional[Path]:
        """Find mom.yaml configuration file."""
        if explicit_path:
            path = Path(explicit_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Config file not found: {explicit_path}")
        
        # Search order: current dir -> parents -> home -> system
        search_paths = [
            Path.cwd() / "mom.yaml",
            *[p / "mom.yaml" for p in Path.cwd().parents],
            Path.home() / ".mom.yaml",
            Path("/etc/mom/config.yaml"),
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if not self.config_path:
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Merge with defaults
            default_config = self._get_default_config()
            return self._merge_configs(default_config, config)
            
        except Exception as e:
            raise ConfigError(f"Failed to load config from {self.config_path}: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'command_name': 'mom',
            'commands': {
                'create': {
                    'python': 'python -m venv {name} && echo "Created {name}"',
                },
                'test': {
                    'pattern': 'pytest {target}',
                },
                'build': {
                    'pattern': 'python -m build {target}',
                },
                'format': {
                    'pattern': 'python -m black {target}',
                },
            },
            'script_paths': ['scripts'],
            'execution': {
                'auto_reset_on_cache_failure': True,
                'retry_count': 2,
                'timeout': 300,
            },
            'recovery': {},
            'interactive': {
                'enable_executing_agent': True,
                'enable_specialized_agents': True,
                'enable_general_agent': True,
                'plugins': [],
            },
            'user_preferences': {
                'author': 'Developer',
                'email': 'dev@example.com',
                'license': 'MIT',
                'git_username': 'developer',
                'git_email': 'dev@example.com',
            },
        }
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_command_mapping(self, command: str, target_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get command mapping configuration."""
        commands = self.config.get('commands', {})
        
        if command not in commands:
            return None
        
        command_config = commands[command]
        
        # If target_type specified, look for specific mapping
        if target_type and target_type in command_config:
            return {'primary': command_config[target_type], **command_config}
        
        # Use pattern as primary if available
        if 'pattern' in command_config:
            return {'primary': command_config['pattern'], **command_config}
        
        return command_config
    
    def get_script_paths(self) -> List[Path]:
        """Get script search paths relative to config file location."""
        paths = self.config.get('script_paths', ['scripts'])
        base_dir = self.config_path.parent if self.config_path else Path.cwd()
        
        resolved_paths = []
        for path_pattern in paths:
            if '*' in path_pattern:
                # Handle glob patterns
                for resolved in base_dir.glob(path_pattern):
                    if resolved.is_dir():
                        resolved_paths.append(resolved)
            else:
                resolved_paths.append(base_dir / path_pattern)
        
        return resolved_paths
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration."""
        return self.config.get('execution', {})
    
    def get_recovery_config(self) -> Dict[str, Any]:
        """Get recovery command configuration."""
        return self.config.get('recovery', {})
    
    def get_command_name(self) -> str:
        """Get the configured command name."""
        return self.config.get('command_name', 'mom')


class ConfigError(Exception):
    """Configuration-related errors."""
    pass