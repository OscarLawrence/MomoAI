# Mom - Universal Command Mapping System

A configurable command mapping system designed for AI-friendly developer tools. Maps simple, memorable commands to complex underlying executables with fallback strategies and auto-recovery.

## Features

- **Simple Command Interface**: `mom create python my-module` instead of complex tool-specific syntax
- **Configurable Mappings**: YAML-based command definitions with parameter transformation
- **Intelligent Fallbacks**: Automatic retry with alternative commands when primary fails
- **Script Discovery**: Find and execute scripts from multiple locations
- **AI-Optimized**: Designed for predictable, memorable interactions with AI agents
- **Universal**: Works with any toolchain (nx, npm, cargo, etc.)

## Quick Start

```bash
# Install and configure
pip install momo-mom
mom --init-config

# Use simple commands
mom create python my-project
mom test my-project
mom script benchmark-performance
```

## Configuration

Mom searches for `mom.yaml` configuration files in:
1. Current directory
2. Parent directories (walking up)
3. User home directory
4. System-wide locations

See documentation for full configuration options.
