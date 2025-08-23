import os
import re
import logging
import traceback
from typing import List
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
try:
    from .models import ChatMessage, ChatRequest, ChatResponse
except ImportError:
    from models import ChatMessage, ChatRequest, ChatResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get the project root directory (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent

app = FastAPI(title="Axiom Minimal Chat")

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed messages."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation error",
            "errors": error_details
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}\nTraceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

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

# Load system message from file
def load_system_message():
    """Load the system message from file."""
    system_message_path = PROJECT_ROOT / "backend" / "system_message.txt"
    try:
        if not system_message_path.exists():
            logger.warning(f"System message file not found at {system_message_path}")
            raise FileNotFoundError(f"System message file not found at {system_message_path}")
        
        content = system_message_path.read_text(encoding="utf-8").strip()
        if not content:
            logger.warning("System message file is empty")
            raise ValueError("System message file is empty")
        
        logger.info("System message loaded successfully")
        return content
        
    except FileNotFoundError as e:
        logger.error(f"System message file not found: {e}")
        # Fallback system message if file not found
        fallback_msg = "You are Axiom, a helpful AI assistant focused on providing clear, accurate, and useful responses."
        logger.info("Using fallback system message")
        return fallback_msg
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode system message file: {e}")
        raise HTTPException(status_code=500, detail="System message file has encoding issues")
    except PermissionError as e:
        logger.error(f"Permission denied reading system message file: {e}")
        raise HTTPException(status_code=500, detail="Cannot read system message file due to permissions")
    except Exception as e:
        logger.error(f"Unexpected error loading system message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load system message: {str(e)}")

def execute_read_file(path: str) -> str:
    """Execute the read_file function with comprehensive error handling."""
    try:
        # Validate path input
        if not path or not isinstance(path, str):
            raise ValueError("File path must be a non-empty string")
        
        # Convert to Path object for better validation
        file_path = Path(path)
        
        # Security check - prevent directory traversal
        try:
            file_path.resolve().relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            raise PermissionError(f"Access denied: path '{path}' is outside project directory")
        
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Check if it's actually a file (not a directory)
        if not file_path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        # Read the file
        logger.info(f"Reading file: {path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Successfully read file: {path} ({len(content)} characters)")
        return content
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError as e:
        error_msg = f"Permission denied: {path} - {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except UnicodeDecodeError as e:
        error_msg = f"Cannot decode file '{path}' as UTF-8: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except IsADirectoryError as e:
        error_msg = f"Path is a directory: {path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except ValueError as e:
        error_msg = f"Invalid file path: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error reading file '{path}': {str(e)}"
        logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")
        return f"Error: {error_msg}"

def detect_and_execute_function_calls(content: str) -> str:
    """Detect read_file function calls in content and execute them."""
    try:
        # Validate input
        if not isinstance(content, str):
            logger.error("Function call detection received non-string content")
            return content
        
        # Regex pattern to match read_file('path') or read_file("path")
        pattern = r"read_file\(['\"]([^'\"]+)['\"]\)"
        
        def replace_function_call(match):
            file_path = match.group(1)
            logger.info(f"Executing function call: read_file('{file_path}')")
            
            try:
                result = execute_read_file(file_path)
                return f"read_file('{file_path}') returned:\n```\n{result}\n```"
            except Exception as e:
                error_msg = f"read_file('{file_path}') failed: {str(e)}"
                logger.error(error_msg)
                return error_msg
        
        # Count function calls for logging
        matches = re.findall(pattern, content)
        if matches:
            logger.info(f"Found {len(matches)} function call(s): {matches}")
        
        return re.sub(pattern, replace_function_call, content)
        
    except Exception as e:
        logger.error(f"Error in function call detection: {str(e)}\nTraceback: {traceback.format_exc()}")
        return content  # Return original content if processing fails

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send message to Claude and return response with comprehensive error handling."""
    
    try:
        logger.info(f"Received chat request from user")
        
        # Step 4: Input Validation
        if not request.message or not request.message.strip():
            logger.warning("Empty message received")
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(request.message) > 100000:  # Reasonable limit
            logger.warning(f"Message too long: {len(request.message)} characters")
            raise HTTPException(status_code=400, detail="Message too long (max 100,000 characters)")
        
        # Validate API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not found")
            raise HTTPException(status_code=500, detail="API key not configured")
        
        if not api_key.startswith("sk-"):
            logger.error("Invalid API key format")
            raise HTTPException(status_code=500, detail="Invalid API key format")
        
        # Load and validate system message
        try:
            system_message = load_system_message()
        except HTTPException:
            raise  # Re-raise HTTPExceptions from load_system_message
        except Exception as e:
            logger.error(f"Failed to load system message: {e}")
            raise HTTPException(status_code=500, detail="Failed to load system configuration")
        
        # Add user message to history
        user_message = ChatMessage(role="user", content=request.message.strip())
        messages.append(user_message)
        logger.info(f"Added user message to history (total messages: {len(messages)})")
        
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
            "system": system_message,
            "messages": api_messages
        }
        
        logger.info("Making API call to Anthropic")
        
        # Step 3: API Call Error Handling
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
            except httpx.TimeoutException as e:
                logger.error(f"API request timeout: {e}")
                raise HTTPException(status_code=504, detail="Request timeout - please try again")
            except httpx.ConnectError as e:
                logger.error(f"API connection error: {e}")
                raise HTTPException(status_code=503, detail="Unable to connect to AI service")
            except httpx.HTTPStatusError as e:
                logger.error(f"API HTTP error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 401:
                    raise HTTPException(status_code=500, detail="Invalid API key")
                elif e.response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded - please try again later")
                elif e.response.status_code == 400:
                    raise HTTPException(status_code=400, detail="Invalid request format")
                else:
                    raise HTTPException(status_code=500, detail=f"AI service error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Unexpected API error: {e}\nTraceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail="Unexpected error calling AI service")
        
        # Step 5: Response Validation
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse API response as JSON: {e}")
            raise HTTPException(status_code=500, detail="Invalid response format from AI service")
        
        # Validate response structure
        if not isinstance(data, dict):
            logger.error("API response is not a dictionary")
            raise HTTPException(status_code=500, detail="Invalid response structure from AI service")
        
        if "content" not in data:
            logger.error("API response missing 'content' field")
            raise HTTPException(status_code=500, detail="Invalid response: missing content")
        
        if not isinstance(data["content"], list) or len(data["content"]) == 0:
            logger.error("API response content is not a non-empty list")
            raise HTTPException(status_code=500, detail="Invalid response: empty content")
        
        if "text" not in data["content"][0]:
            logger.error("API response content missing 'text' field")
            raise HTTPException(status_code=500, detail="Invalid response: missing text content")
        
        if "usage" not in data:
            logger.warning("API response missing 'usage' field")
            token_usage = {"input_tokens": 0, "output_tokens": 0}
        else:
            token_usage = data["usage"]
        
        assistant_content = data["content"][0]["text"]
        logger.info(f"Received response from API ({len(assistant_content)} characters)")
        
        # Check for function calls and execute them
        if "read_file(" in assistant_content:
            logger.info("Function calls detected in response")
            processed_content = detect_and_execute_function_calls(assistant_content)
            
            # If function calls were executed, send the result back to Claude
            if processed_content != assistant_content:
                logger.info("Function calls executed, making follow-up API call")
                
                # Add the original assistant message to history
                assistant_message = ChatMessage(role="assistant", content=assistant_content)
                messages.append(assistant_message)
                
                # Add function execution results as a user message
                function_result_message = ChatMessage(role="user", content=f"Function execution results:\n{processed_content}")
                messages.append(function_result_message)
                
                # Make another API call to Claude with the function results
                api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
                payload["messages"] = api_messages
                
                try:
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers=headers,
                        json=payload,
                        timeout=60.0
                    )
                    response.raise_for_status()
                    
                    # Parse and validate the final response
                    data = response.json()
                    if "content" not in data or not data["content"] or "text" not in data["content"][0]:
                        logger.error("Invalid follow-up response structure")
                        raise HTTPException(status_code=500, detail="Invalid follow-up response from AI service")
                    
                    final_content = data["content"][0]["text"]
                    token_usage = data.get("usage", {"input_tokens": 0, "output_tokens": 0})
                    
                    # Add final assistant message to history
                    final_assistant_message = ChatMessage(role="assistant", content=final_content)
                    messages.append(final_assistant_message)
                    
                    logger.info("Follow-up API call completed successfully")
                    return ChatResponse(
                        response=final_content,
                        token_usage=token_usage
                    )
                    
                except Exception as e:
                    logger.error(f"Follow-up API call failed: {e}")
                    # Return the original response if follow-up fails
                    assistant_message = ChatMessage(role="assistant", content=assistant_content)
                    messages.append(assistant_message)
                    return ChatResponse(
                        response=assistant_content + "\n\n[Note: Function execution completed but follow-up failed]",
                        token_usage=token_usage
                    )
        
        # No function calls - add assistant message to history and return
        assistant_message = ChatMessage(role="assistant", content=assistant_content)
        messages.append(assistant_message)
        
        logger.info("Chat request completed successfully")
        return ChatResponse(
            response=assistant_content,
            token_usage=token_usage
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions (these have proper status codes and messages)
        raise
    except Exception as e:
        # Step 1: Detailed Exception Logging
        logger.error(f"Unexpected error in chat endpoint: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/history")
async def get_history():
    """Get chat history with error handling."""
    try:
        logger.info(f"Retrieving chat history ({len(messages)} messages)")
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@app.delete("/api/history")
async def clear_history():
    """Clear chat history with error handling."""
    try:
        message_count = len(messages)
        messages.clear()
        logger.info(f"Cleared chat history ({message_count} messages removed)")
        return {"status": "cleared", "messages_removed": message_count}
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")

FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html with error handling."""
    try:
        index_path = FRONTEND_DIR / "index.html"
        if not index_path.exists():
            logger.error(f"Frontend index.html not found at {index_path}")
            raise HTTPException(status_code=404, detail="Frontend not found")
        
        logger.info("Serving frontend index.html")
        return FileResponse(index_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to serve frontend")

# Mount static files with error handling
try:
    if not FRONTEND_DIR.exists():
        logger.error(f"Frontend directory not found at {FRONTEND_DIR}")
        raise FileNotFoundError(f"Frontend directory not found at {FRONTEND_DIR}")
    
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
    logger.info(f"Static files mounted from {FRONTEND_DIR}")
except Exception as e:
    logger.error(f"Failed to mount static files: {str(e)}")
    # Continue without static files - the app can still function for API calls

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)