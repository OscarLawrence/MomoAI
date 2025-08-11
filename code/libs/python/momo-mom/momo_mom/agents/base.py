"""
Base classes and interfaces for interactive agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import time


@dataclass
class ExecutionContext:
    """Rich context passed to interactive agents."""
    current_task: str
    project_info: Dict[str, Any] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    working_directory: str = ""
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.working_directory:
            self.working_directory = str(Path.cwd())


@dataclass
class CommandResult:
    """Result of command execution with interaction log."""
    stdout: str
    stderr: str
    returncode: int
    interaction_log: List[Dict[str, Any]] = field(default_factory=list)
    agent_used: Optional[str] = None
    execution_time: float = 0.0
    
    @property
    def success(self) -> bool:
        return self.returncode == 0
    
    @property
    def had_interactions(self) -> bool:
        return len(self.interaction_log) > 0


class InteractiveAgent(ABC):
    """Abstract base class for interactive command agents."""
    
    def __init__(self, name: str, priority: int = 50):
        self.name = name
        self.priority = priority
        self.usage_count = 0
        self.success_count = 0
    
    @abstractmethod
    def can_handle(self, command: str, context: ExecutionContext) -> bool:
        """Check if this agent can handle the interactive command."""
        pass
    
    @abstractmethod
    def handle_prompt(self, prompt: str, command: str, context: ExecutionContext) -> str:
        """Handle an interactive prompt and return response."""
        pass
    
    def get_priority(self) -> int:
        """Return priority (higher = preferred)."""
        return self.priority
    
    def record_usage(self, success: bool = True):
        """Record usage statistics."""
        self.usage_count += 1
        if success:
            self.success_count += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count
    
    def __str__(self) -> str:
        return f"{self.name}(priority={self.priority}, usage={self.usage_count}, success_rate={self.success_rate:.2f})"


class AgentCallback:
    """Wrapper for agent callback functions."""
    
    def __init__(self, callback_fn: Callable[[Dict[str, Any]], str]):
        self.callback_fn = callback_fn
    
    def __call__(self, request: Dict[str, Any]) -> str:
        return self.callback_fn(request)