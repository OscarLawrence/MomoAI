"""
Momo Chat Interface

This module provides the core chat functionality for interacting with Momo
via Ollama. It handles the conversation flow, maintains context, and ensures
Momo's personality shines through.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime

try:
    import ollama
except ImportError:
    ollama = None

from .personality import momo_personality


@dataclass
class ChatMessage:
    """Represents a single message in the chat conversation."""

    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """Represents a chat session with Momo."""

    session_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    model: str = "llama3.2"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MomoChat:
    """
    Main chat interface for conversing with Momo via Ollama.

    This class handles:
    - Ollama connection and model management
    - Chat session management
    - Message history and context
    - Momo's personality integration
    - Error handling and graceful degradation
    """

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.client: Optional[Any] = None
        self.current_session: Optional[ChatSession] = None
        self.is_connected = False

    async def connect(self) -> bool:
        """
        Connect to Ollama and verify the model is available.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if ollama is None:
            return False

        try:
            # Initialize Ollama client
            self.client = ollama.Client(host=self.host)

            # Test connection by listing models with timeout
            models = await asyncio.wait_for(asyncio.to_thread(self.client.list), timeout=5.0)
            available_models = [
                model.get("name", model.get("model", "")) for model in models.get("models", [])
            ]

            # Check if our preferred model is available
            if self.model not in available_models:
                # If preferred model not available, use first available model
                if available_models:
                    old_model = self.model
                    self.model = available_models[0]
                    print(f"Model '{old_model}' not found. Using '{self.model}' instead.")
                else:
                    return False

            self.is_connected = True
            return True

        except asyncio.TimeoutError:
            self.is_connected = False
            return False
        except Exception:
            self.is_connected = False
            return False

    def start_new_session(self, session_id: Optional[str] = None) -> ChatSession:
        """
        Start a new chat session with Momo.

        Args:
            session_id: Optional custom session ID

        Returns:
            ChatSession: The new chat session
        """
        if session_id is None:
            session_id = f"momo_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = ChatSession(
            session_id=session_id, model=self.model, metadata={"momo_version": "1.0.0"}
        )

        # Add system message with Momo's personality
        system_message = ChatMessage(
            role="system",
            content=momo_personality.system_prompt,
            metadata={"type": "personality_injection"},
        )
        self.current_session.messages.append(system_message)

        return self.current_session

    async def send_message(self, message: str, stream: bool = True) -> AsyncGenerator[str, None]:
        """
        Send a message to Momo and get her response.

        Args:
            message: User's message
            stream: Whether to stream the response

        Yields:
            str: Chunks of Momo's response
        """
        if not self.is_connected or not self.client:
            yield "I'm sorry, I'm having trouble connecting to my chat system right now. Please make sure Ollama is running and try again."
            return

        if not self.current_session:
            self.start_new_session()

        # Add user message to session
        user_message = ChatMessage(role="user", content=message)
        self.current_session.messages.append(user_message)

        try:
            # Prepare messages for Ollama (exclude metadata)
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in self.current_session.messages
            ]

            # Get response from Ollama
            if stream:
                response_content = ""
                stream_response = self.client.chat(
                    model=self.model, messages=ollama_messages, stream=True
                )

                for chunk in stream_response:
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        response_content += content
                        yield content

                # Add complete response to session
                assistant_message = ChatMessage(
                    role="assistant",
                    content=response_content,
                    metadata={"model": self.model, "streamed": True},
                )
                self.current_session.messages.append(assistant_message)

            else:
                response = self.client.chat(
                    model=self.model, messages=ollama_messages, stream=False
                )

                content = response["message"]["content"]

                # Add response to session
                assistant_message = ChatMessage(
                    role="assistant",
                    content=content,
                    metadata={"model": self.model, "streamed": False},
                )
                self.current_session.messages.append(assistant_message)

                yield content

        except Exception as e:
            error_message = f"I encountered an error while processing your message: {str(e)}. Let me try to help you anyway!"
            yield error_message

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current chat session."""
        if not self.current_session:
            return {"status": "no_session"}

        return {
            "session_id": self.current_session.session_id,
            "model": self.current_session.model,
            "message_count": len(self.current_session.messages),
            "created_at": self.current_session.created_at.isoformat(),
            "is_connected": self.is_connected,
            "last_message_time": (
                self.current_session.messages[-1].timestamp.isoformat()
                if self.current_session.messages
                else None
            ),
        }

    def get_conversation_history(self, include_system: bool = False) -> List[Dict[str, Any]]:
        """
        Get the conversation history for the current session.

        Args:
            include_system: Whether to include system messages

        Returns:
            List of message dictionaries
        """
        if not self.current_session:
            return []

        history = []
        for msg in self.current_session.messages:
            if not include_system and msg.role == "system":
                continue

            history.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
            )

        return history

    async def get_momo_greeting(self, first_time: bool = False) -> str:
        """Get a personalized greeting from Momo."""
        return momo_personality.get_greeting(first_time)

    def get_momo_farewell(self) -> str:
        """Get a farewell message from Momo."""
        return momo_personality.get_farewell()

    async def check_ollama_status(self) -> Dict[str, Any]:
        """
        Check the status of Ollama connection and available models.

        Returns:
            Dictionary with connection status and available models
        """
        status = {
            "connected": False,
            "host": self.host,
            "current_model": self.model,
            "available_models": [],
            "error": None,
        }

        if ollama is None:
            status["error"] = "Ollama Python package not installed"
            return status

        try:
            if not self.client:
                self.client = ollama.Client(host=self.host)

            # Use asyncio.to_thread for sync operations with timeout
            models = await asyncio.wait_for(asyncio.to_thread(self.client.list), timeout=5.0)
            status["available_models"] = [
                model.get("name", model.get("model", "")) for model in models.get("models", [])
            ]
            status["connected"] = True

        except asyncio.TimeoutError:
            status["error"] = "Connection timeout"
        except Exception as e:
            status["error"] = str(e)

        return status
