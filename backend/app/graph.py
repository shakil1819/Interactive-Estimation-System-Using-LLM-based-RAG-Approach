from typing import Dict, Any, List, Annotated, TypedDict, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import (
    JsonOutputParser,
)
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

from .config import OPENAI_API_KEY, ESTIMATION_CONFIG
from .models import GraphState
from .estimator import calculate_estimate, get_missing_info
from .utils import generate_next_question, format_estimate_for_display

# Define extraction schema for function calling
class ExtractedInfo(BaseModel):
    """Information extracted from user messages."""
    service_type: Optional[str] = Field(
        None, description="Type of service requested (e.g., roofing, plumbing, etc.)"
    )
    square_footage: Optional[float] = Field(
        None, description="Square footage of the area"
    )
    location: Optional[str] = Field(
        None, description="Region (northeast, midwest, south, west)"
    )
    material_type: Optional[str] = Field(
        None, description="Type of material (e.g., asphalt, metal, tile, slate for roofing)"
    )
    timeline: Optional[str] = Field(
        None, description="Timeline preference (standard, expedited, emergency)"
    )


# Initialize LLM
llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4", temperature=0)

# Define extraction prompt
extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant that extracts information for a service estimation system. "
              "Extract only the information provided by the user. "
              "If the information is not provided, leave the field as null."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Create extraction chain
extraction_chain = (
    extraction_prompt
    | llm.with_structured_output(ExtractedInfo)
)


# Define graph nodes
def start_node(state: GraphState) -> GraphState:
    """
    Initialize conversation and provide welcome message.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated graph state
    """
    # Get service config (defaulting to roofing for the prototype)
    service_type = "roofing"
    if service_type in ESTIMATION_CONFIG.get("services", {}):
        service_config = ESTIMATION_CONFIG["services"][service_type]
        state.service_config = service_config
        state.required_info = service_config.get("required_info", [])
    
    # Add initial greeting to history
    welcome_message = (
        "Welcome to the Interactive Estimation System! I'm here to help you get an estimate "
        "for your project. I'll ask you a series of questions, and you can also upload images "
        "if needed. Let's get started!"
    )
    
    state.add_to_history("assistant", welcome_message)
    
    # Generate the first question
    next_question = generate_next_question(state.required_info, state.extracted_info)
    state.current_question = next_question
    state.add_to_history("assistant", next_question)
    
    return state


def input_processor(state: GraphState) -> Dict[str, str]:
    """
    Process user input and determine next action.
    
    Args:
        state: The current graph state
        
    Returns:
        Dictionary indicating the next node to transition to
    """
    # Check if input mentions image upload
    if any(keyword in state.user_input.lower() for keyword in ["image", "photo", "picture", "uploaded", "upload"]):
        state.next = "image_handler"
        return {"next": "image_handler"}
    
    # Otherwise, continue to information extraction
    state.next = "information_extractor"
    return {"next": "information_extractor"}


def image_handler_node(state: GraphState) -> GraphState:
    """
    Handle image upload references.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated graph state
    """
    # Add confirmation message
    confirmation = "I've received your image. This will help with the estimation process."
    state.add_to_history("assistant", confirmation)
    
    # Add a reference to the image (in a real system, this would store actual image data or references)
    state.image_references.append(f"image_{len(state.image_references) + 1}")
    
    return state


def information_extractor(state: GraphState) -> GraphState:
    """
    Extract information from user input.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated graph state with extracted information
    """
    # Create conversation history
    history = []
    for message in state.conversation_history:
        if message["role"] == "assistant":
            history.append(AIMessage(content=message["content"]))
        else:
            history.append(HumanMessage(content=message["content"]))
    
    # Extract information using LLM
    extracted_data = extraction_chain.invoke({
        "history": history,
        "input": state.user_input
    })
    
    # Update extracted info in state
    for field, value in extracted_data.dict(exclude_none=True).items():
        if value:  # Only update if value is not None or empty
            state.extracted_info[field] = value
    
    return state


def state_updater(state: GraphState) -> Dict[str, str]:
    """
    Update state and determine next action based on completeness.
    
    Args:
        state: The current graph state
        
    Returns:
        Dictionary indicating the next node to transition to
    """
    # Add user input to conversation history
    state.add_to_history("user", state.user_input)
    
    # Clear user input for next round
    state.user_input = ""
    
    # Check if we have all required information
    missing_info = get_missing_info(state.required_info, state.extracted_info)
    
    if not missing_info:
        state.next = "estimator"
        return {"next": "estimator"}
    else:
        state.next = "question_generator"
        return {"next": "question_generator"}


def question_generator(state: GraphState) -> GraphState:
    """
    Generate the next question based on missing information.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated graph state with the next question
    """
    # Get missing information
    missing_info = get_missing_info(state.required_info, state.extracted_info)
    
    # Generate next question
    next_question = generate_next_question(missing_info, state.extracted_info)
    state.current_question = next_question
    
    # Add question to conversation history
    state.add_to_history("assistant", next_question)
    
    return state


def estimator_node(state: GraphState) -> GraphState:
    """
    Calculate the estimate based on extracted information.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated graph state with the estimate
    """
    # Get service type (defaulting to "roofing" for the prototype)
    service_type = state.extracted_info.get("service_type", "roofing")
    
    # Calculate estimate
    estimate_result, success = calculate_estimate(
        service_type=service_type,
        service_config=state.service_config,
        extracted_info=state.extracted_info,
        image_references=state.image_references
    )
    
    if success and estimate_result:
        # Store the estimate in the state
        state.final_estimate = estimate_result.dict()
    
    return state


def response_generator(state: GraphState) -> Dict[str, str]:
    """
    Generate the final response and end the conversation flow.
    
    Args:
        state: The current graph state
        
    Returns:
        Dictionary indicating to end the conversation
    """
    if state.final_estimate:
        # Format the estimate for display
        estimate_message = format_estimate_for_display(state.final_estimate)
        
        # Add the estimate to the conversation history
        state.add_to_history("assistant", estimate_message)
        
        # Add a closing message
        closing_message = (
            "Thank you for using our estimation service! "
            "Is there anything else you'd like to know about this estimate?"
        )
        state.add_to_history("assistant", closing_message)
    
    # End the graph execution after response is generated
    # New user inputs will start fresh graph executions
    return {"next": END}


# Create the graph
def create_graph() -> StateGraph:
    """
    Create and configure the conversation flow graph.
    
    Returns:
        Configured StateGraph
    """
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("start", start_node)
    graph.add_node("input_processor", input_processor)
    graph.add_node("image_handler", image_handler_node)
    graph.add_node("information_extractor", information_extractor)
    graph.add_node("state_updater", state_updater)
    graph.add_node("question_generator", question_generator)
    graph.add_node("estimator", estimator_node)
    graph.add_node("response_generator", response_generator)
    
    # Add edges
    graph.set_entry_point("start")
    graph.add_edge("start", "input_processor")
    graph.add_conditional_edges(
        "input_processor",
        lambda state: state.next,
        {
            "image_handler": "image_handler",
            "information_extractor": "information_extractor"
        }
    )
    graph.add_edge("image_handler", "information_extractor")
    graph.add_edge("information_extractor", "state_updater")
    graph.add_conditional_edges(
        "state_updater",
        lambda state: state.next,
        {
            "estimator": "estimator",
            "question_generator": "question_generator"
        }
    )
    graph.add_edge("question_generator", "input_processor")
    graph.add_edge("estimator", "response_generator")
    graph.add_edge("response_generator", END)
    
    # Compile the graph
    return graph.compile()


# Initialize the graph
estimation_graph = create_graph()


# Function to process user message and get response
async def process_user_message(session_id: str, message: str) -> GraphState:
    """
    Process a user message through the graph.
    
    Args:
        session_id: The session ID
        message: The user's message
        
    Returns:
        Updated graph state after processing the message
        
    Note:
        The graph execution terminates after generating a response.
        Each user message starts a new graph execution with persisted state.
    """
    # Create initial state or use existing state
    input_state = GraphState(
        session_id=session_id,
        user_input=message
    )
    
    # Run the graph with increased recursion limit to prevent Graph Recursion Error
    result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
    return result


# Function to handle image upload
async def handle_image_upload(session_id: str, file_description: str) -> GraphState:
    """
    Handle an image upload event.
    
    Args:
        session_id: The session ID
        file_description: Description of the uploaded file
        
    Returns:
        Updated graph state after processing the image upload
        
    Note:
        The graph execution terminates after generating a response.
        Each user interaction starts a new graph execution with persisted state.
    """
    # Create input state with image upload message
    input_state = GraphState(
        session_id=session_id,
        user_input=f"I've uploaded an image: {file_description}"
    )
    
    # Run the graph with increased recursion limit to prevent Graph Recursion Error
    result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
    return result
