from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    token_usage: dict