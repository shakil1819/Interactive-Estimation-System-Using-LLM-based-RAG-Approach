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


# Initialize LLM with a mock implementation for testing
class MockLLM:
    """Mock LLM for testing purposes"""
    def __init__(self):
        pass
        
    async def ainvoke(self, prompt, **kwargs):
        """Mock invoke method that extracts information from the input"""
        # If this is for structured output extraction, handle differently
        if 'history' in prompt and 'input' in prompt:
            return self._extract_info_from_input(prompt['input'])
        elif isinstance(prompt, str):
            return "I apologize, I don't have enough information to generate a comprehensive response."
        else:
            return ExtractedInfo()
            
    def with_structured_output(self, output_cls):
        """Return self since we're mocking"""
        return self
        
    def _extract_info_from_input(self, input_text):
        """Extract information from user input"""
        import re
        
        # Convert input to lowercase for easier matching
        text = input_text.lower()
        
        # Initialize result with all fields as None
        result = ExtractedInfo()
        
        # Extract service type
        if "roof" in text or "shingle" in text:
            result.service_type = "roofing"
            print("Extracted service_type: roofing")
            
        # Extract square footage
        sq_ft_match = re.search(r'(\d+)\s*(?:sq\s*ft|square\s*feet|square\s*foot)', text)
        if sq_ft_match:
            result.square_footage = float(sq_ft_match.group(1))
            print(f"Extracted square_footage: {result.square_footage}")
            
        # Extract location
        for location in ["northeast", "midwest", "south", "west", "north east", "mid west"]:
            if location in text:
                result.location = location.replace(" ", "")
                print(f"Extracted location: {result.location}")
                break
                
        # Try to extract location from city/state mentions
        if "arizona" in text or "phoenix" in text:
            result.location = "west"
            print("Extracted location from city/state: west")
            
        # Extract material type
        for material in ["asphalt", "metal", "tile", "slate", "shingles", "architectural"]:
            if material in text:
                if material == "architectural" or material == "shingles":
                    result.material_type = "asphalt"
                else:
                    result.material_type = material
                print(f"Extracted material_type: {result.material_type}")
                break
                
        # Extract timeline
        for timeline in ["standard", "expedited", "emergency", "rush", "urgent", "normal"]:
            if timeline in text:
                if timeline == "rush" or timeline == "urgent":
                    result.timeline = "expedited"
                elif timeline == "normal":
                    result.timeline = "standard"
                else:
                    result.timeline = timeline
                print(f"Extracted timeline: {result.timeline}")
                break
                
        # If standard timeline can be inferred
        if result.timeline is None and "regular" in text:
            result.timeline = "standard"
            print("Inferred timeline: standard")
            
        print(f"Extracted information: {result}")
        return result

# Use mock LLM for testing
llm = MockLLM()

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
    # Ensure we have the required info configured
    if not state.required_info and state.service_config:
        service_type = state.extracted_info.get("service_type", "roofing")
        if service_type in state.service_config.get("services", {}):
            state.required_info = state.service_config["services"][service_type].get("required_info", [])
            print(f"Setting required info: {state.required_info}")
    
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
    
    # Debug log
    print(f"Missing information: {missing_info}")
    print(f"Extracted so far: {state.extracted_info}")
    
    # If we already have an estimate and the user sends a general inquiry without
    # providing new information, route to question generator instead of re-calculating estimate
    if not missing_info and state.final_estimate:
        # Only regenerate estimate if explicitly requested
        estimate_keywords = ["new estimate", "recalculate", "update estimate", "different materials", "change"]
        if any(keyword in state.conversation_history[-1]["content"].lower() for keyword in estimate_keywords):
            # Clear the existing estimate to regenerate it
            print("Regenerating estimate based on user request")
            state.final_estimate = None
            state.next = "estimator"
            return {"next": "estimator"}
        else:
            # Otherwise, just provide a response to the follow-up question
            print("Routing to question generator for follow-up")
            state.next = "question_generator"
            return {"next": "question_generator"}
    elif not missing_info:
        # If we don't have an estimate yet but have all required info, generate one
        print("Routing to estimator - all information available")
        state.next = "estimator"
        return {"next": "estimator"}
    else:
        # Missing info, ask questions
        print(f"Routing to question generator - missing: {missing_info}")
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
    
    # Get the last user message for context in responses
    last_user_message = ""
    for message in reversed(state.conversation_history):
        if message["role"] == "user":
            last_user_message = message["content"]
            break
    
    # Generate next question - pass flag indicating if we already have an estimate
    has_estimate = state.final_estimate is not None
    next_question = generate_next_question(
        missing_info, 
        state.extracted_info, 
        has_estimate,
        last_user_message
    )
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
        
        # Log the estimate information for debugging
        print(f"Estimate generated: {service_type} service, total: ${state.final_estimate['total_estimate']:,.2f}")
    else:
        # Log failure for debugging
        print(f"Failed to generate estimate. Missing information: {get_missing_info(state.required_info, state.extracted_info)}")
    
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
        
        # Log that we're returning an estimate
        print(f"Returning estimate for {state.final_estimate['service_type']} service")
    else:
        # If we don't have an estimate but should, calculate it again
        missing_info = get_missing_info(state.required_info, state.extracted_info)
        if not missing_info and not state.final_estimate:
            print("All information available but no estimate - generating now")
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
                
                # Format and add to history
                estimate_message = format_estimate_for_display(state.final_estimate)
                state.add_to_history("assistant", estimate_message)
                
                # Add a closing message
                closing_message = (
                    "Thank you for using our estimation service! "
                    "Is there anything else you'd like to know about this estimate?"
                )
                state.add_to_history("assistant", closing_message)
            else:
                # Something went wrong, add error message
                error_message = "I'm sorry, I couldn't generate an estimate with the provided information. Please check your inputs."
                state.add_to_history("assistant", error_message)
    
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
async def process_user_message(session_id: str, message: str, prev_state: Optional[GraphState] = None) -> GraphState:
    """
    Process a user message through the graph.
    
    Args:
        session_id: The session ID
        message: The user's message
        prev_state: Optional previous graph state to preserve context
        
    Returns:
        Updated graph state after processing the message
        
    Note:
        The graph execution terminates after generating a response.
        Each user message starts a new graph execution with persisted state.
    """    # Either use previous state or create a new one
    if prev_state:
        # Use the previous state but update the user input
        input_state = prev_state.copy()
        input_state.user_input = message
        
        # Only reset final_estimate for certain conditions:
        # 1. If the user explicitly asks for a new estimate
        # 2. If we're still collecting information and don't have an estimate yet
        if prev_state.final_estimate:
            # Keep the existing estimate for follow-up questions
            regenerate_keywords = ["new estimate", "recalculate", "different", "change"]
            if any(keyword in message.lower() for keyword in regenerate_keywords):
                print("Resetting estimate based on user request for change")
                input_state.final_estimate = None
        # If we don't have a final estimate and the system said it's ready to prepare one, 
        # don't reset it (it will be generated in this run)
    else:
        # Create a brand new state if none exists
        input_state = GraphState(
            session_id=session_id,
            user_input=message
        )
    
    # Run the graph with increased recursion limit to prevent Graph Recursion Error
    result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
    return result


# Function to handle image upload
async def handle_image_upload(session_id: str, file_description: str, prev_state: Optional[GraphState] = None) -> GraphState:
    """
    Handle an image upload event.
    
    Args:
        session_id: The session ID
        file_description: Description of the uploaded file
        prev_state: Optional previous graph state to preserve context
        
    Returns:
        Updated graph state after processing the image upload
        
    Note:
        The graph execution terminates after generating a response.
        Each user interaction starts a new graph execution with persisted state.
    """    # Either use previous state or create a new one
    if prev_state:
        # Use the previous state but update the user input
        input_state = prev_state.copy()
        input_state.user_input = f"I've uploaded an image: {file_description}"
        
        # Only reset the estimate if we don't already have one or the image is explicitly for a new estimate
        if "new estimate" in file_description.lower() or "different" in file_description.lower():
            print("Resetting estimate based on new image for different project")
            input_state.final_estimate = None
        else:
            # Images might be for an existing estimate - don't reset unless necessary
            print("Keeping existing estimate while adding new image")
    else:
        # Create a brand new state if none exists
        input_state = GraphState(
            session_id=session_id,
            user_input=f"I've uploaded an image: {file_description}"
        )
    
    # Run the graph with increased recursion limit to prevent Graph Recursion Error
    result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
    return result
