"""Tests for log levels and hierarchy."""

import pytest
from momo_logger.levels import should_log, LOG_LEVEL_HIERARCHY
from momo_logger.types import LogLevel


def test_log_level_hierarchy():
    """Test that log level hierarchy is properly defined."""
    # Test that all levels have ranks
    assert LogLevel.DEBUG in LOG_LEVEL_HIERARCHY
    assert LogLevel.INFO in LOG_LEVEL_HIERARCHY
    assert LogLevel.WARNING in LOG_LEVEL_HIERARCHY
    assert LogLevel.ERROR in LOG_LEVEL_HIERARCHY
    assert LogLevel.CRITICAL in LOG_LEVEL_HIERARCHY

    assert LogLevel.AI_DEBUG in LOG_LEVEL_HIERARCHY
    assert LogLevel.AI_SYSTEM in LOG_LEVEL_HIERARCHY
    assert LogLevel.AI_AGENT in LOG_LEVEL_HIERARCHY
    assert LogLevel.AI_USER in LOG_LEVEL_HIERARCHY

    assert LogLevel.TESTER in LOG_LEVEL_HIERARCHY
    assert LogLevel.DEVELOPER in LOG_LEVEL_HIERARCHY
    assert LogLevel.ARCHITECT in LOG_LEVEL_HIERARCHY
    assert LogLevel.OPERATOR in LOG_LEVEL_HIERARCHY


def test_should_log_basic():
    """Test basic log level filtering."""
    # INFO should log INFO and above
    assert should_log(LogLevel.INFO, LogLevel.INFO) is True
    assert should_log(LogLevel.INFO, LogLevel.WARNING) is True
    assert should_log(LogLevel.INFO, LogLevel.ERROR) is True
    assert should_log(LogLevel.INFO, LogLevel.CRITICAL) is True
    assert should_log(LogLevel.INFO, LogLevel.DEBUG) is False

    # DEBUG should log everything
    assert should_log(LogLevel.DEBUG, LogLevel.DEBUG) is True
    assert should_log(LogLevel.DEBUG, LogLevel.INFO) is True
    assert should_log(LogLevel.DEBUG, LogLevel.WARNING) is True
    assert should_log(LogLevel.DEBUG, LogLevel.ERROR) is True
    assert should_log(LogLevel.DEBUG, LogLevel.CRITICAL) is True

    # CRITICAL should only log critical
    assert should_log(LogLevel.CRITICAL, LogLevel.CRITICAL) is True
    assert should_log(LogLevel.CRITICAL, LogLevel.ERROR) is False
    assert should_log(LogLevel.CRITICAL, LogLevel.WARNING) is False
    assert should_log(LogLevel.CRITICAL, LogLevel.INFO) is False
    assert should_log(LogLevel.CRITICAL, LogLevel.DEBUG) is False


def test_should_log_ai_levels():
    """Test AI-specific log level filtering."""
    # Test AI levels
    assert should_log(LogLevel.INFO, LogLevel.AI_DEBUG) is True
    assert should_log(LogLevel.INFO, LogLevel.AI_SYSTEM) is True
    assert should_log(LogLevel.INFO, LogLevel.AI_AGENT) is True
    assert should_log(LogLevel.INFO, LogLevel.AI_USER) is True

    # Test role-specific levels
    assert should_log(LogLevel.INFO, LogLevel.TESTER) is True
    assert should_log(LogLevel.INFO, LogLevel.DEVELOPER) is True
    assert should_log(LogLevel.INFO, LogLevel.ARCHITECT) is True
    assert should_log(LogLevel.INFO, LogLevel.OPERATOR) is True
