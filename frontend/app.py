import streamlit as st
import requests
import json
import os
import warnings
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Filter out PydanticSchemaJson warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/object/apply:.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/.*", category=UserWarning)

# Load environment variables
load_dotenv()

# API Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "http://localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
API_URL = f"{BACKEND_HOST}:{BACKEND_PORT}"

# Page configuration
st.set_page_config(
    page_title="Interactive Estimation System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #f0f2f6;
    }
    .chat-message.assistant {
        background-color: #e6f3ff;
    }
    .chat-message .content {
        padding: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    div.block-container {
        padding-top: 2rem;
    }
    div.stButton {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "estimate" not in st.session_state:
    st.session_state.estimate = None
if "conversation_complete" not in st.session_state:
    st.session_state.conversation_complete = False


def initialize_session():
    """Initialize a new session with the backend."""
    try:
        response = requests.post(f"{API_URL}/api/session")
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data.get("session_id")
            
            # Get initial conversation state
            get_conversation()
            
            return True
        else:
            st.error(f"Failed to initialize session: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error initializing session: {e}")
        return False


def send_message(message: str):
    """Send a message to the backend API."""
    if not st.session_state.session_id:
        st.error("No active session. Please refresh the page.")
        return
    
    try:
        response = requests.post(
            f"{API_URL}/api/chat", 
            json={
                "session_id": st.session_state.session_id,
                "message": message
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Update state with response data
            if "message" in data and data["message"]:
                st.session_state.messages.append({"role": "assistant", "content": data["message"]})
            
            if "estimate" in data and data["estimate"]:
                st.session_state.estimate = data["estimate"]
            
            if "conversation_complete" in data:
                st.session_state.conversation_complete = data["conversation_complete"]
            
            return True
        else:
            st.error(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error sending message: {e}")
        return False


def upload_file(file_description: str):
    """Send a file upload notification to the backend API."""
    if not st.session_state.session_id:
        st.error("No active session. Please refresh the page.")
        return
    
    try:
        response = requests.post(
            f"{API_URL}/api/upload", 
            json={
                "session_id": st.session_state.session_id,
                "file_description": file_description
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Update state with response data
            if "message" in data and data["message"]:
                st.session_state.messages.append({"role": "assistant", "content": data["message"]})
            
            return True
        else:
            st.error(f"Failed to process upload: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error processing upload: {e}")
        return False


def get_conversation():
    """Get the current conversation state from the backend."""
    if not st.session_state.session_id:
        return
    
    try:
        response = requests.get(f"{API_URL}/api/conversation/{st.session_state.session_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Update messages from conversation history
            st.session_state.messages = data.get("conversation_history", [])
            
            # Update estimate if available
            if "final_estimate" in data and data["final_estimate"]:
                st.session_state.estimate = data["final_estimate"]
                st.session_state.conversation_complete = True
            
            return True
        else:
            st.error(f"Failed to get conversation: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error getting conversation: {e}")
        return False


def handle_input():
    """Handle user input from the chat input."""
    message = st.session_state.user_input
    if message:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": message})
        
        # Send to backend
        send_message(message)
        
        # Clear input
        st.session_state.user_input = ""


def handle_file_upload():
    """Handle file upload from the user."""
    uploaded_file = st.session_state.uploaded_file
    if uploaded_file:
        # Add user message about upload
        file_message = f"I've uploaded an image: {uploaded_file.name}"
        st.session_state.messages.append({"role": "user", "content": file_message})
        
        # In a real system, you would upload the file to the server here
        # For the prototype, we just send a notification about the upload
        upload_file(uploaded_file.name)


def reset_conversation():
    """Reset the conversation and start a new session."""
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.estimate = None
    st.session_state.conversation_complete = False
    
    # Initialize a new session
    initialize_session()


# Main layout
st.title("📋 Interactive Estimation System")

# Sidebar
with st.sidebar:
    st.header("Service Estimation")
    st.markdown("""
    This interactive system helps you get an estimate for services such as roofing.
    
    **How it works:**
    1. Answer the questions about your project
    2. Upload images if needed (optional)
    3. Get a detailed estimate
    
    **Features:**
    - Conversational interface
    - Image upload capability (demo)
    - Detailed cost breakdown
    - Price range estimation
    """)
    
    # Reset button
    if st.button("Start New Estimate"):
        reset_conversation()


# Initialize session if needed
if not st.session_state.session_id:
    initialize_session()
    
# Main chat interface
chat_container = st.container()

# Input area
input_container = st.container()

with input_container:
    cols = st.columns([3, 1])
    
    with cols[0]:
        st.text_input("Type your message", key="user_input", on_change=handle_input)
    
    with cols[1]:
        st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="uploaded_file", on_change=handle_file_upload)

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Display estimate if available
if st.session_state.estimate:
    with st.expander("📋 Estimate Details", expanded=True):
        # Format estimate for display
        estimate = st.session_state.estimate
        formatted_estimate = f"""
# 📋 Estimate for {estimate['service_type'].title()} Service

## Project Details:
- **Square Footage**: {estimate['square_footage']} sq ft
- **Location**: {estimate['location'].title()}
- **Material**: {estimate['material_type'].title()}
- **Timeline**: {estimate['timeline'].title()}
"""
        
        if estimate.get('image_references'):
            formatted_estimate += f"- **Images Provided**: {len(estimate['image_references'])}\n"
        
        formatted_estimate += f"""
## Cost Breakdown:
- **Base Cost**: ${estimate['base_cost']:,.2f}
- **Material Cost**: ${estimate['material_cost']:,.2f}
- **Regional Adjustment**: ${estimate['region_adjustment']:,.2f}
- **Timeline Adjustment**: ${estimate['timeline_adjustment']:,.2f}
- **Permit Fee**: ${estimate['permit_fee']:,.2f}

## Total Estimate: ${estimate['total_estimate']:,.2f}
## Price Range: ${estimate['price_range_low']:,.2f} - ${estimate['price_range_high']:,.2f}

*Note: This is a preliminary estimate and may change based on final inspection.*
"""
        st.markdown(formatted_estimate)
