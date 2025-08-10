"""Core types and data models for the momo-logger module."""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log levels for different contexts and agent roles."""

    # Standard levels for debugging and system operations
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    # AI-optimized levels for different contexts
    AI_SYSTEM = "ai_system"  # System-level AI operations
    AI_USER = "ai_user"  # User-facing AI communications
    AI_AGENT = "ai_agent"  # Inter-agent communications
    AI_DEBUG = "ai_debug"  # AI-specific debugging information

    # Role-specific levels for specialized agents
    TESTER = "tester"  # Testing-specific logs
    DEVELOPER = "developer"  # Development-specific logs
    ARCHITECT = "architect"  # Architecture-level logs
    OPERATOR = "operator"  # Operations/production logs


class LogRecord(BaseModel):
    """Structured log record with rich metadata for AI consumption."""

    timestamp: datetime
    level: LogLevel
    message: str
    module: str
    agent: Optional[str] = None
    agent_role: Optional[str] = None
    user_facing: bool = False
    ai_optimized: bool = False
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    exception: Optional[str] = None
    trace_id: Optional[str] = None
