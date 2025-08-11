"""
Mom - Universal Command Mapping System

A configurable command mapping system designed for AI-friendly developer tools.
Maps simple, memorable commands to complex underlying shell commands with 
fallback strategies and auto-recovery.
"""

from .config import ConfigManager, ConfigError
from .executor import CommandExecutor
from .discovery import ScriptDiscovery
from .workflow_executor import WorkflowCommandExecutor, WorkflowAgentIntegration

__version__ = "1.0.0"
__all__ = [
    "ConfigManager", 
    "ConfigError", 
    "CommandExecutor", 
    "ScriptDiscovery",
    "WorkflowCommandExecutor",
    "WorkflowAgentIntegration"
]
