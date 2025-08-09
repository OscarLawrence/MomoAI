"""JSON formatter for momo-logger."""

import json
from datetime import datetime
from ..base import BaseLogFormatter
from ..types import LogRecord


class JSONFormatter(BaseLogFormatter):
    """JSON formatter that outputs structured log records."""

    def format(self, record: LogRecord) -> str:
        """Format a log record as JSON."""
        # Convert record to dict and handle datetime serialization
        record_dict = record.model_dump()
        record_dict["timestamp"] = record_dict["timestamp"].isoformat()

        return json.dumps(record_dict, ensure_ascii=False)
