"""Constants and default configurations for momo-logger."""

import os
from .types import LogLevel

# Default configurations
DEFAULT_LOG_LEVEL = LogLevel.INFO
DEFAULT_BACKEND = "console"
DEFAULT_FORMATTER = "text"

# Environment variable overrides
LOG_LEVEL_ENV = os.getenv("MOMO_LOGGER_LEVEL", DEFAULT_LOG_LEVEL.value)
BACKEND_ENV = os.getenv("MOMO_LOGGER_BACKEND", DEFAULT_BACKEND)
FORMATTER_ENV = os.getenv("MOMO_LOGGER_FORMATTER", DEFAULT_FORMATTER)

# File backend defaults
DEFAULT_LOG_FILE = os.getenv("MOMO_LOGGER_FILE", "momo.log")
DEFAULT_LOG_DIR = os.getenv("MOMO_LOGGER_DIR", ".")
