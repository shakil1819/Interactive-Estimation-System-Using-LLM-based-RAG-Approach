from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
import warnings
from typing import Dict, Any, Optional, AsyncGenerator

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
from .llm_service import analyze_image_stream

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
    
    # Store the state - process_user_message now directly returns GraphState
    sessions[session_id] = result
    
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
    
    # Update session state - process_user_message now directly returns GraphState
    sessions[session_id] = result
    
    # Get the latest assistant message
    latest_messages = [
        m for m in result.conversation_history 
        if m["role"] == "assistant"
    ]
    latest_message = latest_messages[-1]["content"] if latest_messages else ""
    
    # Get missing information
    from .estimator import get_missing_info
    missing_info = get_missing_info(
        result.required_info, 
        result.extracted_info
    )
    
    # Create response
    response = ChatResponse(
        session_id=session_id,
        message=latest_message,
        estimate=result.final_estimate,
        missing_info=missing_info,
        conversation_complete=bool(result.final_estimate)
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
    image_data = upload_data.image_data  # Get the base64 encoded image data
    
    # Check if session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the existing state
    state = sessions[session_id]
    
    # Process file upload through graph with previous state
    result = await handle_image_upload(session_id, file_description, image_data, state)
    
    # Update session state - handle_image_upload now directly returns GraphState
    sessions[session_id] = result
    
    # Get the latest assistant message
    latest_messages = [
        m for m in result.conversation_history 
        if m["role"] == "assistant"
    ]
    latest_message = latest_messages[-1]["content"] if latest_messages else ""
    
    # Get missing information
    from .estimator import get_missing_info
    missing_info = get_missing_info(
        result.required_info, 
        result.extracted_info
    )
    
    # Create response
    response = ChatResponse(
        session_id=session_id,
        message=latest_message,
        estimate=result.final_estimate,
        missing_info=missing_info,
        conversation_complete=bool(result.final_estimate)
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
        "final_estimate": state.final_estimate,
        "estimate": state.final_estimate  # Include duplicate with 'estimate' key for consistency
    }


@app.post("/api/analyze-image-stream")
async def analyze_image_stream_endpoint(upload_data: FileUpload) -> StreamingResponse:
    """
    Analyze an image with streaming responses from GPT-4o.
    
    Args:
        upload_data: Information about the uploaded file including base64 image data
        
    Returns:
        Streaming response with analysis
    """
    session_id = upload_data.session_id
    image_data = upload_data.image_data
    prompt = upload_data.file_description or "Please analyze this image and provide detailed information."
    
    if not image_data:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    # Check if session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the existing state
    state = sessions[session_id]
    
    # Create image reference
    image_ref = f"image_{len(state.image_references) + 1}"
    state.image_references.append(image_ref)
    
    # Initialize image analysis storage
    if image_ref not in state.image_analysis:
        state.image_analysis[image_ref] = {}
    
    # Store image data
    state.image_analysis[image_ref]["base64_data"] = image_data
    
    # Update session state with the new image reference
    sessions[session_id] = state
    
    async def stream_generator() -> AsyncGenerator[str, None]:
        # Initialize analysis content accumulator
        full_analysis = ""
        
        # Start streaming response from GPT-4o
        stream = analyze_image_stream(image_data, prompt)
        
        if stream:
            try:
                async for chunk in stream:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_analysis += content
                        yield content
            except Exception as e:
                print(f"Error during streaming: {e}")
                yield f"\nError during analysis: {str(e)}"
            
            # Store the complete analysis in the state
            state.image_analysis[image_ref]["analysis"] = full_analysis
            
            # Extract information from analysis and update state (after streaming is complete)
            from .llm_service import extract_info_from_image_analysis
            extracted_info = extract_info_from_image_analysis(full_analysis)
            
            # Update extracted info from image analysis
            for key, value in extracted_info.items():
                if value is not None and (key not in state.extracted_info or state.extracted_info[key] is None):
                    state.extracted_info[key] = value
        else:
            # If streaming failed, provide a fallback response
            yield "I'm unable to analyze the image at this time. Please try again later."
    
    return StreamingResponse(stream_generator(), media_type="text/plain")


if __name__ == "__main__":
    # Avoid event loop conflicts by using a different approach
    import nest_asyncio
    nest_asyncio.apply()
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
