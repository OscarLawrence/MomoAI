# Momo Petals Usage Guide

## Installation

First, navigate to the module directory and install dependencies:

```bash
cd code/libs/python/momo-petals
poetry install
```

## Running the Demo

### Basic Usage Script

The easiest way to try Petals is to run the basic usage script:

```bash
poetry run python scripts/01_basic_usage.py
```

This script will:

1. Connect to the Petals network
2. Show network information
3. Allow you to interactively generate text from prompts

### Using the Showcase

For a more automated demo:

```python
import asyncio
from momo_petals.showcase import run_showcase

# Run the showcase with default model (bloom-560m)
asyncio.run(run_showcase())

# Or specify a different model
asyncio.run(run_showcase("bigscience/bloom-1b7"))
```

### Direct Client Usage

For more control, use the client directly:

```python
import asyncio
from momo_petals import PetalsClient, PetalsConfig, GenerationConfig

async def main():
    # Configure client
    config = PetalsConfig(model_name="bigscience/bloom-560m")
    client = PetalsClient(config)

    # Connect to network
    await client.connect()

    # Generate text
    gen_config = GenerationConfig(
        max_new_tokens=50,
        temperature=0.8,
        top_p=0.9
    )

    result = await client.generate("Once upon a time", gen_config)
    print(f"Generated: {result.text}")

    # Get network info
    info = await client.get_network_info()
    print(f"Active peers: {info.peer_count}")

    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

## Common Issues

### No Peers Available

If you get a "No peers available" error:

- The model might not be served by anyone on the network
- Try using a more popular model like `bigscience/bloom-560m`
- Check https://health.petals.dev for network status

### Installation Issues

If Petals fails to install:

- Make sure you have Python 3.8+ installed
- On some systems, you might need to install additional dependencies:

  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev build-essential

  # macOS
  brew install python3
  ```

### Network Connectivity

Petals requires internet connectivity to connect to the distributed network. Make sure:

- You have a stable internet connection
- No firewall is blocking the connection
- Your network allows P2P connections

## Model Selection

Popular models that are often available:

- `bigscience/bloom-560m` - Smallest, most likely to have peers
- `bigscience/bloom-1b7` - Medium size
- `bigscience/bloom-3b` - Larger model
- `bigscience/bloom-7b1` - Even larger
- `bigscience/bloom` - Full 176B model (requires many peers)

Smaller models are more likely to have available peers and faster generation times.
