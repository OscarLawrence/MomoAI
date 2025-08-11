"""
Universal command interface for MomoAI.

Provides context-aware, intelligent command execution through a single entry point.
"""

from .router import ContextAwareCommandRouter
from .context import WorkspaceContext, ModuleInfo
from .cli import mom

__all__ = ["ContextAwareCommandRouter", "WorkspaceContext", "ModuleInfo", "mom"]
