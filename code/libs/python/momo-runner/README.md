# Momo Runner - AI Chat Interface

**Chat with Momo, your warm and intelligent AI assistant**

Momo is an AI assistant named after the developer's daughter, serving as the primary interface for the MomoAI multi-agent system. She brings warmth and intelligence to technology, helping with development tasks, system guidance, and thoughtful conversation.

## 🌟 Features

- **Warm Personality**: Momo embodies the caring, intelligent qualities that inspire meaningful technology
- **MomoAI Integration**: Deep knowledge of the MomoAI system architecture and components
- **Ollama Powered**: Local LLM integration for privacy and performance
- **Beautiful CLI**: Rich, interactive terminal interface with streaming responses
- **Session Management**: Persistent conversation history and context
- **Agent Coordination**: Can work with other agents in the MomoAI ecosystem

## 🚀 Quick Start

### Prerequisites

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Pull a model**: `ollama pull llama3.2`
3. **Start Ollama**: Make sure Ollama is running (usually automatic)

### Installation

```bash
# Install dependencies
cd code/libs/python/momo-runner
uv sync

# Run Momo chat
./scripts/momo
```

### Usage

```bash
# Start chatting with Momo
momo

# Check connection status
momo status

# Get information about Momo
momo info

# Use specific model
momo chat --model llama3.1

# Use custom Ollama host
momo chat --host http://remote-server:11434
```

## 💬 Chat Commands

Once in a chat session with Momo:

- **Regular conversation**: Just type your message and press Enter
- `/help` - Show available commands
- `/status` - Display connection and session information
- `/clear` - Clear the screen
- `/quit` - End the chat session
- `Ctrl+C` - Quick exit

## 🤖 About Momo

Momo is more than just an AI assistant - she represents the human heart of artificial intelligence:

### Identity
- Named after the developer's daughter, bringing personal warmth to technology
- Embodies curiosity, intelligence, and helpfulness
- Serves as the bridge between users and the MomoAI system

### Capabilities
- **Natural Conversation**: Warm, supportive dialogue with technical expertise
- **MomoAI Guidance**: Expert knowledge of system architecture and components
- **Agent Coordination**: Can work with specialized agents for different tasks
- **Development Help**: Assistance with Python development and MomoAI tools
- **Knowledge Management**: Help with vector, graph, and document storage systems
- **Problem Solving**: Thoughtful analysis and solution development

### MomoAI System Knowledge
Momo has deep understanding of:
- Multi-agent architecture and self-extension capabilities
- Knowledge base systems (vector + graph + document storage)
- Development tools (momo-kb, momo-logger, momo-vector-store, etc.)
- Command systems (mom for development, momo for conversation)
- Workflow management and agent coordination

## 🛠️ Development

### Project Structure

```
momo-runner/
├── momo_runner/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # Command-line interface
│   ├── chat.py              # Core chat functionality
│   └── personality.py       # Momo's identity and knowledge
├── scripts/
│   └── momo                 # Shell wrapper script
├── tests/
│   └── unit/                # Unit tests
├── pyproject.toml           # Package configuration
└── README.md                # This file
```

### Running Tests

```bash
# Run unit tests
nx run momo-runner:test-fast

# Run all tests with coverage
nx run momo-runner:test-all

# Format code
nx run momo-runner:format

# Type checking
nx run momo-runner:typecheck
```

### API Usage

```python
from momo_runner import MomoChat

# Create chat instance
chat = MomoChat(model="llama3.2")

# Connect to Ollama
await chat.connect()

# Start conversation
chat.start_new_session()

# Send message and get streaming response
async for chunk in chat.send_message("Hello Momo!"):
    print(chunk, end="")
```

## 🔧 Configuration

### Environment Variables

- `OLLAMA_HOST`: Override default Ollama host (default: http://localhost:11434)
- `MOMO_MODEL`: Default model to use (default: llama3.2)

### Ollama Models

Momo works with any Ollama model, but recommended models:
- `llama3.2` (default) - Good balance of capability and speed
- `llama3.1` - More capable for complex tasks
- `mistral` - Fast and efficient
- `codellama` - Specialized for development tasks

## 🎯 Integration with MomoAI

Momo is designed to work seamlessly with the broader MomoAI ecosystem:

### Command Systems
- **`mom`**: Development command mapping (momo-mom package)
- **`momo`**: Chat interface (this package)

### Knowledge Integration
- Can reference MomoAI knowledge base (momo-kb)
- Understands system architecture and components
- Coordinates with specialized agents when needed

### Development Workflow
- Integrates with nx monorepo structure
- Follows MomoAI development standards
- Supports the research-driven development philosophy

## 🤝 Contributing

1. Follow the MomoAI development standards
2. Write comprehensive tests for new features
3. Ensure Momo's personality remains warm and helpful
4. Test with multiple Ollama models
5. Update documentation for new capabilities

## 📜 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 💝 Acknowledgments

Named after Momo, who inspires the pursuit of genuine intelligence and meaningful technology that serves humanity with warmth and care.

---

**Built with ❤️ as part of the MomoAI multi-agent system**