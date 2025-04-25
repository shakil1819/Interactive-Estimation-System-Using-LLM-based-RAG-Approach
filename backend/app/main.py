from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import warnings
from typing import Dict, Any, Optional

# Filter out PydanticSchemaJson warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/object/apply:.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/.*", category=UserWarning)

from .models import ChatInput, ChatResponse, FileUpload, GraphState
from .graph import process_user_message, handle_image_upload
from .utils import (
    create_session, 
    get_session_state, 
    update_session_state, 
    format_estimate_for_display
)
from .estimator import get_missing_info
from .config import BACKEND_PORT

# Create FastAPI app
app = FastAPI(title="Interactive Estimation System API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active sessions
sessions: Dict[str, GraphState] = {}


@app.get("/")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "message": "Interactive Estimation System API is running"}


@app.post("/api/session")
async def create_new_session() -> Dict[str, str]:
    """Create a new session."""
    session_id = create_session()
    
    # Initialize the conversation by running the start node
    result = await process_user_message(session_id, "")
    
    # Convert the result back to a GraphState object
    # Langgraph returns an AddableValuesDict, not a GraphState
    state = GraphState(**result)
    
    # Store the state
    sessions[session_id] = state
    
    return {"session_id": session_id}


@app.post("/api/chat")
async def chat(input_data: ChatInput) -> ChatResponse:
    """
    Process a chat message from the user.
    
    Args:
        input_data: The chat input from the user
        
    Returns:
        Chat response with assistant message
    """
    session_id = input_data.session_id
    message = input_data.message
    
    # Check if session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
      # Get session state
    state = sessions[session_id]
    
    # Update user input in state
    state.user_input = message
    
    # Process message through graph with previous state
    result = await process_user_message(session_id, message, state)
    
    # Convert the result back to a GraphState object
    # Langgraph returns an AddableValuesDict, not a GraphState
    updated_state = GraphState(**result)
    
    # Update session state
    sessions[session_id] = updated_state
    
    # Get the latest assistant message
    latest_messages = [
        m for m in updated_state.conversation_history 
        if m["role"] == "assistant"
    ]
    latest_message = latest_messages[-1]["content"] if latest_messages else ""
    
    # Get missing information
    from .estimator import get_missing_info
    missing_info = get_missing_info(
        updated_state.required_info, 
        updated_state.extracted_info
    )
    
    # Create response
    response = ChatResponse(
        session_id=session_id,
        message=latest_message,
        estimate=updated_state.final_estimate,
        missing_info=missing_info,
        conversation_complete=bool(updated_state.final_estimate)
    )
    
    return response


@app.post("/api/upload")
async def upload_file(upload_data: FileUpload) -> ChatResponse:
    """
    Handle file upload from the user.
    
    Args:
        upload_data: Information about the uploaded file
        
    Returns:
        Chat response with assistant message
    """
    session_id = upload_data.session_id
    file_description = upload_data.file_description
      # Check if session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the existing state
    state = sessions[session_id]
      
    # Process file upload through graph with previous state
    result = await handle_image_upload(session_id, file_description, state)
    
    # Convert the result back to a GraphState object
    # Langgraph returns an AddableValuesDict, not a GraphState
    updated_state = GraphState(**result)
    
    # Update session state
    sessions[session_id] = updated_state
    
    # Get the latest assistant message
    latest_messages = [
        m for m in updated_state.conversation_history 
        if m["role"] == "assistant"
    ]
    latest_message = latest_messages[-1]["content"] if latest_messages else ""
    
    # Get missing information
    from .estimator import get_missing_info
    missing_info = get_missing_info(
        updated_state.required_info, 
        updated_state.extracted_info
    )
    
    # Create response
    response = ChatResponse(
        session_id=session_id,
        message=latest_message,
        estimate=updated_state.final_estimate,
        missing_info=missing_info,
        conversation_complete=bool(updated_state.final_estimate)
    )
    
    return response


@app.get("/api/conversation/{session_id}")
async def get_conversation(session_id: str) -> Dict[str, Any]:
    """
    Get the current conversation state.
    
    Args:
        session_id: The session ID
        
    Returns:
        The current conversation state
    """
    # Check if session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get session state
    state = sessions[session_id]
    
    return {
        "session_id": session_id,
        "conversation_history": state.conversation_history,
        "extracted_info": state.extracted_info,
        "missing_info": get_missing_info(state.required_info, state.extracted_info),
        "final_estimate": state.final_estimate
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
