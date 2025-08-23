# Minimal Web Chat Implementation Plan

## Overview
Build a clean, minimal web chat interface from scratch with direct Anthropic API integration. No SDKs, no frameworks, no abstractions - just pure HTTP communication.

## Architecture Philosophy
- **Micro-modules**: Each file has single clear responsibility
- **No sys.path hacks**: Use standard Python imports only
- **Auto-resolving environment**: `load_dotenv()` without parameters finds .env automatically up the tree
- **Direct HTTP**: No SDK pollution, pure httpx requests
- **Zero overengineering**: Minimal functional implementation

## File Structure
```
axiom/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── models.py         # Pydantic models  
│   └── requirements.txt  # Dependencies
├── frontend/
│   ├── index.html        # Chat interface
│   ├── script.js         # API calls + DOM manipulation
│   └── style.css         # Basic styling
└── .env                  # ANTHROPIC_API_KEY (already exists)
```

## Backend Implementation (FastAPI)

### Dependencies (already clean in pyproject.toml)
```toml
fastapi>=0.100.0      # Web framework
uvicorn[standard]     # ASGI server  
pydantic>=2.0.0       # Data validation
httpx>=0.25.0         # HTTP client (NOT requests)
python-dotenv>=1.0.0  # Environment loading
python-multipart      # Form handling
```
**Note**: No anthropic SDK, no websockets, no requests - pure minimal stack

### models.py
```python
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
```

### main.py
```python
import os
from typing import List
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from models import ChatMessage, ChatRequest, ChatResponse

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

# Serve frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

app.mount("/", StaticFiles(directory="frontend"), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Frontend Implementation

### index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Axiom Chat</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Axiom</h1>
            <button id="clearBtn" class="clear-btn">Clear History</button>
        </div>
        
        <div id="chatHistory" class="chat-history"></div>
        
        <form id="chatForm" class="chat-form">
            <textarea 
                id="messageInput" 
                placeholder="Type your message here..."
                rows="4"
                required
            ></textarea>
            <button type="submit" id="sendBtn">Send</button>
        </form>
        
        <div id="status" class="status"></div>
    </div>
    
    <script src="script.js"></script>
</body>
</html>
```

### script.js
```javascript
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const chatHistory = document.getElementById('chatHistory');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const status = document.getElementById('status');

// Load chat history on page load
window.addEventListener('load', loadHistory);

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Disable form while processing
    setLoading(true);
    
    try {
        // Add user message to display
        addMessage('user', message);
        
        // Clear input
        messageInput.value = '';
        
        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response to display
        addMessage('assistant', data.response);
        
        // Update status with token usage
        const tokens = data.token_usage;
        setStatus(`Tokens: ${tokens.input_tokens} in, ${tokens.output_tokens} out`);
        
    } catch (error) {
        console.error('Error:', error);
        setStatus(`Error: ${error.message}`, 'error');
        
    } finally {
        setLoading(false);
        messageInput.focus();
    }
});

// Clear history
clearBtn.addEventListener('click', async () => {
    try {
        await fetch('/api/history', { method: 'DELETE' });
        chatHistory.innerHTML = '';
        setStatus('History cleared');
    } catch (error) {
        setStatus(`Error clearing history: ${error.message}`, 'error');
    }
});

// Handle Ctrl+Enter to submit
messageInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        chatForm.dispatchEvent(new Event('submit'));
    }
});

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        chatHistory.innerHTML = '';
        data.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
        });
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const roleLabel = document.createElement('div');
    roleLabel.className = 'role';
    roleLabel.textContent = role === 'user' ? 'You' : 'Axiom';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(roleLabel);
    messageDiv.appendChild(contentDiv);
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function setLoading(loading) {
    sendBtn.disabled = loading;
    messageInput.disabled = loading;
    sendBtn.textContent = loading ? 'Sending...' : 'Send';
}

function setStatus(message, type = 'info') {
    status.textContent = message;
    status.className = `status ${type}`;
    
    // Clear status after 3 seconds
    setTimeout(() => {
        status.textContent = '';
        status.className = 'status';
    }, 3000);
}
```

### style.css
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f5f5;
    color: #333;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: white;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}

.header {
    padding: 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header h1 {
    color: #2563eb;
    font-size: 24px;
}

.clear-btn {
    background: #ef4444;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.clear-btn:hover {
    background: #dc2626;
}

.chat-history {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.message {
    margin-bottom: 20px;
}

.message.user .role {
    color: #059669;
    font-weight: 600;
}

.message.assistant .role {
    color: #2563eb;
    font-weight: 600;
}

.role {
    font-size: 14px;
    margin-bottom: 4px;
}

.content {
    background: #f8fafc;
    padding: 12px;
    border-radius: 8px;
    white-space: pre-wrap;
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 14px;
    line-height: 1.5;
    border-left: 3px solid #e5e7eb;
}

.message.user .content {
    background: #ecfdf5;
    border-left-color: #059669;
}

.message.assistant .content {
    background: #eff6ff;
    border-left-color: #2563eb;
}

.chat-form {
    padding: 20px;
    border-top: 1px solid #eee;
}

.chat-form textarea {
    width: 100%;
    min-height: 80px;
    padding: 12px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-family: inherit;
    font-size: 14px;
    resize: vertical;
    margin-bottom: 12px;
}

.chat-form textarea:focus {
    outline: none;
    border-color: #2563eb;
}

.chat-form button {
    background: #2563eb;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
}

.chat-form button:hover:not(:disabled) {
    background: #1d4ed8;
}

.chat-form button:disabled {
    background: #94a3b8;
    cursor: not-allowed;
}

.status {
    text-align: center;
    padding: 8px;
    font-size: 12px;
    color: #6b7280;
}

.status.error {
    color: #ef4444;
}
```

## Setup Instructions

1. **Delete existing backend** (axiom/axiom/backend/)
2. **Create new structure** following file structure above
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Ensure .env exists** with `ANTHROPIC_API_KEY=your_key`
5. **Run**: `python main.py`
6. **Open**: http://localhost:8000

## Features

- **Direct Anthropic API** integration
- **Chat history** preserved in session
- **Copy-paste friendly** responses
- **Multi-line input** support (Ctrl+Enter to send)
- **Token usage** display
- **Clear history** functionality
- **Responsive** design

## Total Implementation Time: ~1 hour