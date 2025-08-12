"""
Momo Runner - AI Chat Interface

This package provides the terminal interface for chatting with Momo,
the AI assistant named after the developer's daughter. Momo serves as
the warm, intelligent guide for the MomoAI multi-agent system.

Main components:
- MomoChat: Core chat functionality with Ollama integration
- MomoPersonality: Momo's identity, knowledge, and personality traits
- MomoCLI: Beautiful command-line interface for conversations

Usage:
    # Start a chat session
    from momo_runner import MomoChat

    chat = MomoChat()
    await chat.connect()
    async for response in chat.send_message("Hello Momo!"):
        print(response, end="")

    # Or use the CLI
    from momo_runner.cli import main
    main()
"""

from .chat import MomoChat, ChatSession, ChatMessage
from .personality import MomoPersonality, momo_personality
from .cli import MomoCLI

__version__ = "0.1.0"
__author__ = "Vincent"
__email__ = "vincent@momoai.dev"

__all__ = [
    "MomoChat",
    "ChatSession",
    "ChatMessage",
    "MomoPersonality",
    "momo_personality",
    "MomoCLI",
]
