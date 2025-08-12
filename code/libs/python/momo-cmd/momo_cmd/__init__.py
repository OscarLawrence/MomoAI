"""
Universal command interface for MomoAI.

Provides context-aware, intelligent command execution through a single entry point.
"""

from .cli import mo
from .context import ModuleInfo, WorkspaceContext
from .router import ContextAwareCommandRouter

__all__ = ["ContextAwareCommandRouter", "WorkspaceContext", "ModuleInfo", "mo"]
