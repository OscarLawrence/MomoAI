# Momo Petals

A showcase module for distributed inference using Petals - a decentralized platform for running large language models.

## Overview

This module demonstrates how to use Petals for distributed inference, allowing you to run large language models collaboratively across multiple peers in a decentralized network.

## Features

- Simple client wrapper for Petals
- Error handling for common network issues
- Rich console output for better visibility
- Demo scripts showcasing basic usage

## Installation

```bash
poetry install
```

## Usage

### Basic Example

```python
from momo_petals import PetalsClient

# Initialize client
client = PetalsClient(model_name="bigscience/bloom-560m")

# Connect to the network
await client.connect()

# Generate text
result = await client.generate("Once upon a time")
print(result.text)

# Get network info
info = await client.get_network_info()
print(f"Connected peers: {info.peer_count}")
```

### Running the Demo

```bash
python scripts/01_basic_usage.py
```

## Architecture

- `client.py` - Main client interface for Petals
- `models.py` - Pydantic models for configuration and results
- `showcase.py` - High-level showcase interface
- `exceptions.py` - Custom exceptions for error handling

## Error Handling

The module gracefully handles common issues:

- No peers available in the network
- Network connectivity problems
- Model loading failures

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint
poetry run ruff check .
```
