"""
Unified AI Agent Framework (momo-agent).

This module provides a scientific, testable framework for AI agent task execution
that integrates momo-workflow's scientific rigor with momo-mom's command execution
capabilities and ADR system integration.

Key Components:
- AgentTask and AgentWorkflow protocols for structured task definition
- AgentWorkflowEngine for multi-step task orchestration with rollback
- MomAgentCommandExecutor for command execution with fallback strategies
- Scientific measurement and performance tracking
- Local AI model testing support
"""

from .command_executor import MomAgentCommandExecutor, create_agent_command_executor
from .core import AgentWorkflowEngine, BaseAgentTask, BaseAgentWorkflow
from .types import (
    AgentExecutionContext,
    AgentTask,
    AgentTaskResult,
    AgentTaskType,
    AgentWorkflow,
    AgentWorkflowResult,
    CommandResult,
    TaskMetadata,
    TaskPriority,
)

__version__ = "1.0.0"

# Public API
__all__ = [
    # Core protocols and types
    "AgentTask",
    "AgentWorkflow",
    "AgentExecutionContext",
    "AgentTaskResult",
    "AgentWorkflowResult",
    "CommandResult",
    "TaskMetadata",
    "TaskPriority",
    "AgentTaskType",
    # Core implementations
    "BaseAgentTask",
    "BaseAgentWorkflow",
    "AgentWorkflowEngine",
    # Command execution
    "MomAgentCommandExecutor",
    "create_agent_command_executor",
]
