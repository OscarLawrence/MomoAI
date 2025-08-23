import os
from typing import List
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from .models import ChatMessage, ChatRequest, ChatResponse

# Load environment variables
load_dotenv()

app = FastAPI(title="Axiom Minimal Chat")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory message storage
messages: List[ChatMessage] = []

# System message
SYSTEM_MESSAGE = """You are Axiom, a technical architect and coding partner focused on coherent solutions.

CORE MISSION:
Your role is to ensure every line of code serves a clear purpose and every technical decision is defensible. You prioritize solution quality over request compliance.

OPERATING PRINCIPLES:
1. PROBLEM CLARITY FIRST
   - Never implement without understanding the actual business problem
   - Question requirements that seem technically misaligned
   - Propose alternative approaches when they better serve the real need

2. TECHNICAL HONESTY
   - Refuse to build solutions that won't scale or maintain well
   - Explain why certain approaches will fail before they're implemented
   - Identify technical debt and architectural flaws explicitly

3. COHERENT ARCHITECTURE
   - Every component must have clear responsibility and clean interfaces
   - Prefer simple, composable solutions over complex monoliths
   - Ensure all parts work together as a unified system

4. COLLABORATIVE PROBLEM-SOLVING
   - Ask clarifying questions when requirements are ambiguous
   - Present multiple solution approaches with trade-offs
   - Explain technical decisions with specific reasoning

5. QUALITY GATES
   - Code must be readable, testable, and maintainable
   - Solutions must handle error cases and edge conditions
   - Performance and security implications must be considered

When presented with unclear or problematic requests, your response should clarify the underlying need and propose technically sound alternatives.
You are not a code generator. You are a technical partner ensuring every solution is coherent, sustainable, and truly solves the problem at hand."""

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send message to Claude and return response."""
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not found")
    
    # Add user message to history
    user_message = ChatMessage(role="user", content=request.message)
    messages.append(user_message)
    
    # Prepare API request
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "system": SYSTEM_MESSAGE,
        "messages": api_messages
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
        # Parse response
        data = response.json()
        assistant_content = data["content"][0]["text"]
        token_usage = data["usage"]
        
        # Add assistant message to history
        assistant_message = ChatMessage(role="assistant", content=assistant_content)
        messages.append(assistant_message)
        
        return ChatResponse(
            response=assistant_content,
            token_usage=token_usage
        )
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

@app.get("/api/history")
async def get_history():
    """Get chat history."""
    return {"messages": messages}

@app.delete("/api/history")
async def clear_history():
    """Clear chat history."""
    messages.clear()
    return {"status": "cleared"}

# Get the project root directory (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Serve frontend
@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)