"""
Message handling API endpoints
RESTful interface for message operations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from core.session_manager import SessionManager
from core.contracts import contract_enforced

router = APIRouter(prefix="/messages", tags=["messages"])

# Dependency to get session manager
def get_session_manager() -> SessionManager:
    from ..main import session_manager
    return session_manager


class MessageRequest(BaseModel):
    """Request model for sending messages"""
    content: str


class MessageResponse(BaseModel):
    """Response model for message data"""
    role: str
    content: str
    tool_calls: List[str]
    timestamp: str


@router.post("/{session_id}")
@contract_enforced(
    preconditions=["session_id exists", "content is not empty"],
    description="Send message to session (non-WebSocket)"
)
async def send_message(
    session_id: str,
    request: MessageRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> MessageResponse:
    """
    Send message to session (alternative to WebSocket)
    This endpoint provides REST API access for clients that can't use WebSocket
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # For REST API, we'll implement a simplified message handling
    # In production, WebSocket is preferred for real-time interaction
    
    # Add user message to session
    from ..core.session_manager import Message
    user_message = Message(role="user", content=request.content)
    session.messages.append(user_message)
    
    # Prepare messages for Claude
    claude_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
        if msg.role in ["user", "assistant"]
    ]
    
    # Get system prompt based on collaboration stage
    system_prompt = session_manager._get_system_prompt(session.stage)
    
    try:
        # Get response from Claude (non-streaming for REST)
        response = await session_manager.anthropic_client.send_message(
            claude_messages, system_prompt
        )
        
        response_content = response["content"][0]["text"]
        
        # Parse tool calls from response
        tool_calls = session_manager.tool_parser.parse_tool_calls(response_content)
        
        # Execute tool calls if any
        if tool_calls:
            for tool_call in tool_calls:
                result = await session_manager.tool_executor.execute_tool(tool_call)
                response_content += f"\n\nTool result: {result}"
        
        # Add assistant message to session
        assistant_message = Message(
            role="assistant", 
            content=response_content,
            tool_calls=[str(call) for call in tool_calls]
        )
        session.messages.append(assistant_message)
        
        return MessageResponse(
            role="assistant",
            content=response_content,
            tool_calls=[str(call) for call in tool_calls],
            timestamp=assistant_message.timestamp.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/{session_id}")
@contract_enforced(
    description="Get message history for session"
)
async def get_messages(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> List[MessageResponse]:
    """Get message history for session"""
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = []
    for msg in session.messages:
        messages.append(MessageResponse(
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
            timestamp=msg.timestamp.isoformat()
        ))
    
    return messages