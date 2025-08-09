"""AI formatter for momo-logger."""

import json
from typing import Dict, Any
from datetime import datetime
from ..base import BaseLogFormatter
from ..types import LogRecord


class AIFormatter(BaseLogFormatter):
    """AI formatter that outputs structured data optimized for AI consumption."""

    def format(self, record: LogRecord) -> str:
        """Format a log record as AI-optimized structured data."""
        # Create AI-optimized structure
        ai_record: Dict[str, Any] = {
            "timestamp": record.timestamp.isoformat(),
            "type": "log",
            "level": record.level.value,
            "module": record.module,
            "message": record.message,
            "ai_optimized": record.ai_optimized,
            "user_facing": record.user_facing,
        }

        # Add optional fields if present
        if record.agent:
            ai_record["agent"] = record.agent

        if record.agent_role:
            ai_record["agent_role"] = record.agent_role

        if record.context:
            ai_record["context"] = record.context

        if record.metadata:
            ai_record["metadata"] = record.metadata

        if record.exception:
            ai_record["exception"] = record.exception

        if record.trace_id:
            ai_record["trace_id"] = record.trace_id

        return json.dumps(ai_record, ensure_ascii=False)
