from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$", description="Must be 'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=100000, description="Message content")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=100000, description="User message")
    
    @field_validator('message')
    @classmethod
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    token_usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage information")