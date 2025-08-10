"""Log level definitions and utilities."""

from .types import LogLevel

# Log level hierarchy for filtering
LOG_LEVEL_HIERARCHY = {
    LogLevel.DEBUG: 0,
    LogLevel.INFO: 1,
    LogLevel.WARNING: 2,
    LogLevel.ERROR: 3,
    LogLevel.CRITICAL: 4,
    LogLevel.AI_DEBUG: 5,
    LogLevel.AI_SYSTEM: 6,
    LogLevel.AI_AGENT: 7,
    LogLevel.AI_USER: 8,
    LogLevel.TESTER: 9,
    LogLevel.DEVELOPER: 10,
    LogLevel.ARCHITECT: 11,
    LogLevel.OPERATOR: 12,
}


def should_log(current_level: LogLevel, target_level: LogLevel) -> bool:
    """Determine if a log record should be processed based on level hierarchy."""
    current_rank = LOG_LEVEL_HIERARCHY.get(current_level, 0)
    target_rank = LOG_LEVEL_HIERARCHY.get(target_level, 0)
    return target_rank >= current_rank
