# Momo Logger Context

This directory contains the momo-logger module, which provides structured logging for the Momo AI system. The logger is designed specifically for multi-agent AI systems with different log levels for various agent roles and contexts.

Key components:
- Logger: Main logging class with async support
- Backends: Console, file, and buffer implementations
- Formatters: JSON, text, and AI-optimized output
- Levels: Standard, AI-optimized, and role-specific log levels
- Factory: Dynamic backend loading system

The logger supports context management, structured data, and is optimized for both human and AI consumption.