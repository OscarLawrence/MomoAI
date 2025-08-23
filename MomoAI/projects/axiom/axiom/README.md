# Axiom PWA - Complete Implementation

## 🚀 Quick Start

1. **Set up your API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

2. **Start the server:**
   ```bash
   # Unix/Linux/macOS
   ./start.sh
   
   # Windows
   start.bat
   
   # Or use Python directly
   python start.py
   ```

3. **Open your browser:**
   - Navigate to `http://localhost:8000`
   - The PWA will automatically load

## 📁 Project Structure

```
axiom/
├── backend/                 # FastAPI Backend
│   ├── main.py             # Main FastAPI application
│   ├── api/                # REST API endpoints
│   │   ├── sessions.py     # Session management
│   │   └── messages.py     # Message handling
│   ├── core/               # Core business logic
│   │   ├── anthropic_client.py  # Pure HTTP Claude client
│   │   ├── contracts.py         # Formal contract system
│   │   └── session_manager.py   # Session state management
│   └── tools/              # Tool system
│       ├── parser.py       # Natural function call parser
│       └── executor.py     # Tool execution engine
├── frontend/               # PWA Frontend
│   ├── index.html          # Main app shell
│   ├── manifest.json       # PWA manifest
│   ├── sw.js              # Service worker
│   ├── css/
│   │   └── app.css        # Complete responsive styling
│   └── js/
│       ├── api.js         # WebSocket + REST client
│       ├── ui.js          # DOM manipulation
│       ├── stages.js      # Stage management
│       └── app.js         # Main application coordinator
└── README.md              # This file
```

## 🏗️ Architecture

### Backend (FastAPI)
- **Pure HTTP client** to Claude Sonnet 4 (no SDK pollution)
- **WebSocket support** for real-time streaming
- **Formal contract system** for coherence validation
- **Natural tool calls** - AI responds with `read_file("/path")` instead of complex JSON
- **Session management** with collaboration stages
- **RESTful API** as fallback for non-WebSocket clients

### Frontend (PWA)
- **Progressive Web App** - works on any device, installable
- **Real-time chat** with streaming responses
- **Stage-based workflow** - Vision → Architecture → Implementation → Review
- **Task progress visualization**
- **Offline support** with service worker
- **Responsive design** - mobile and desktop optimized

### Tool System
The AI can use simple, natural function calls:
```python
read_file("/path/to/file.txt")
write_file("/path/to/file.txt", "content")
edit_file("/path/to/file.txt", "old_content", "new_content")
list_files("/path/to/directory")
bash_exec("command")
create_directory("/path/to/dir")
delete_file("/path/to/file.txt")
```

## 🎯 Collaboration Stages

### 1. Vision (🎯)
- **Purpose**: Explore problems and define goals
- **Focus**: Understanding requirements, constraints, and objectives
- **Transitions to**: Architecture when problem is well-defined

### 2. Architecture (🏗️)
- **Purpose**: Design solutions and plan implementation
- **Focus**: System design, technology choices, component structure
- **Transitions to**: Implementation when design is clear

### 3. Implementation (⚙️)
- **Purpose**: Build and execute the solution
- **Focus**: Writing code, creating files, executing tasks
- **Transitions to**: Review when implementation is complete

### 4. Review (🔍)
- **Purpose**: Evaluate and refine results
- **Focus**: Testing, quality assessment, improvements
- **Transitions to**: Vision for new iterations or features

## 🔧 API Endpoints

### REST API
```
POST /api/sessions                    # Create new session
GET  /api/sessions/{id}              # Get session state
POST /api/sessions/{id}/stage        # Change collaboration stage
GET  /api/sessions/{id}/tasks        # Get task tree
POST /api/messages/{session_id}      # Send message (REST fallback)
GET  /api/messages/{session_id}      # Get message history
```

### WebSocket
```
/ws/{session_id}                     # Real-time communication

# Client → Server
{ "type": "message", "content": "..." }
{ "type": "interrupt_task", "task_id": "..." }

# Server → Client
{ "type": "message", "content": "...", "tool_calls": [...] }
{ "type": "message_delta", "content": "..." }  # Streaming
{ "type": "task_update", "task": {...} }
{ "type": "stage_change", "stage": "..." }
{ "type": "error", "content": "..." }
```

## 🛠️ Development

### Requirements
- Python 3.11+
- Anthropic API key

### Local Development
```bash
# Install in development mode
pip install -e .

# Run with auto-reload
cd axiom/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
```bash
ANTHROPIC_API_KEY=your_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 🌟 Key Features

### ✅ Implemented
- **Complete PWA** with offline support
- **Real-time WebSocket** communication
- **Streaming AI responses** with live updates
- **Natural tool system** - simple function calls
- **Stage-based collaboration** workflow
- **Responsive design** - works on mobile and desktop
- **Session management** with persistence
- **Error handling** and reconnection logic
- **Formal contract system** for coherence
- **Pure HTTP client** (no SDK dependencies)

### 🎯 Core Philosophy
- **Coherent over complex** - Simple, clean interfaces
- **Democratized creation** - No terminal skills required
- **Future-proof design** - Works local and remote
- **Tool simplicity** - Natural language function calls
- **Real-time collaboration** - Live updates and progress

## 🚀 Deployment

### Local Deployment
```bash
# Quick start
./start.sh  # or start.bat on Windows

# Manual start
python start.py
```

### Production Deployment
```bash
# Install dependencies
pip install -e .

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here

# Run with production server
cd axiom/backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🧪 Testing the Implementation

1. **Start the server** using one of the startup scripts
2. **Open browser** to `http://localhost:8000`
3. **Test basic chat** - send a message and verify AI response
4. **Test tool calls** - ask AI to "read_file('README.md')" or "list_files('.')"
5. **Test stage transitions** - change stages and verify behavior
6. **Test WebSocket** - verify real-time streaming responses
7. **Test PWA features** - try installing as app, test offline mode

## 📱 PWA Features

- **Installable** - Add to home screen on mobile/desktop
- **Offline capable** - Service worker caches static assets
- **Responsive** - Adapts to any screen size
- **Fast loading** - Cached resources load instantly
- **Native feel** - Behaves like a native app

## 🔍 Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY not found"**
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key to `.env`

2. **"WebSocket connection failed"**
   - Check if server is running on port 8000
   - Verify no firewall blocking WebSocket connections

3. **"Module not found" errors**
   - Run `pip install -e .` to install dependencies
   - Ensure you're in the correct directory

4. **PWA not installing**
   - Ensure HTTPS (or localhost) for PWA features
   - Check browser console for manifest errors

## 🎉 Success Criteria Met

✅ **Working local PWA** - Complete Progressive Web App implementation  
✅ **Chats with Claude Sonnet 4** - Pure HTTP client integration  
✅ **Executes basic tool functions** - Natural function call system  
✅ **FastAPI backend** - Complete REST API + WebSocket server  
✅ **PWA frontend** - Responsive, installable web app  
✅ **All architecture documented** - Complete file structure and APIs  

The implementation is complete and ready for use!