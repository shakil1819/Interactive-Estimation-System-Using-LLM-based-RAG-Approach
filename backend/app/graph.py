from typing import Dict, Any, List, Annotated, TypedDict, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import (
    JsonOutputParser,
)
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.fake import FakeListLLM

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


# Initialize LLM for development - using a fake LLM response for predictable behavior
# In production, use OpenAI: llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0)
def extract_info_from_text(text):
    """Extract information from text using more robust pattern matching"""
    import re
    
    # Create default responses for each type of extraction
    result = {"service_type": None, "square_footage": None, "location": None, 
              "material_type": None, "timeline": None}
    
    text = text.lower()
    
    # Extract service type with more specific patterns
    if re.search(r'\b(roof|roofing|shingles?)\b', text):
        result["service_type"] = "roofing"
    elif re.search(r'\b(siding|exterior|cladding)\b', text):
        result["service_type"] = "siding"
    
    # Check if user mentioned square footage or area with better pattern matching
    # Look for various formats like 1500 sq ft, 1,500 square feet, etc.
    sq_ft_match = re.search(r'(\d[\d,]*)\s*(?:sq\.?\s*ft\.?|square\s*feet|square\s*foot|sq(?:\s*\.)?(?:\s*footage)?)', text)
    if sq_ft_match:
        # Remove commas and convert to float
        square_footage = sq_ft_match.group(1).replace(',', '')
        result["square_footage"] = float(square_footage)
    
    # Also check for just numbers that might be square footage
    # Only match if it's likely to be square footage (between 500-10000 for typical roof sizes)
    if result["square_footage"] is None:
        size_matches = re.findall(r'\b(\d{3,5})\b', text)  # Look for 3-5 digit numbers
        for match in size_matches:
            num = int(match)
            # Fix the parenthesis issue in the condition
            if 500 <= num <= 10000 and (('feet' in text) or ('foot' in text) or ('footage' in text) or ('area' in text) or ('size' in text)):
                result["square_footage"] = float(num)
                print(f"Extracted square footage from number: {num}")
                break
    
    # Extract location with better region detection
    region_patterns = {
        "northeast": [r'\b(north\s*east|northeastern|new\s*england|ny|ma|ct|ri|vt|nh|me|new\s*york|massachusetts|connecticut|rhode\s*island|vermont|new\s*hampshire|maine)\b'],
        "midwest": [r'\b(mid\s*west|midwest|oh|mi|in|il|wi|mn|ia|mo|nd|sd|ne|ks|ohio|michigan|indiana|illinois|wisconsin|minnesota|iowa|missouri|north\s*dakota|south\s*dakota|nebraska|kansas)\b'],
        "south": [r'\b(south|southeastern|tx|ok|ar|la|ms|al|tn|ky|fl|ga|sc|nc|va|wv|md|de|dc|texas|oklahoma|arkansas|louisiana|mississippi|alabama|tennessee|kentucky|florida|georgia|south\s*carolina|north\s*carolina|virginia|west\s*virginia|maryland|delaware)\b'],
        "west": [r'\b(west|western|ca|or|wa|nv|id|mt|wy|ut|co|az|nm|hi|ak|california|oregon|washington|nevada|idaho|montana|wyoming|utah|colorado|arizona|new\s*mexico|hawaii|alaska)\b']
    }
    
    for region, patterns in region_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                result["location"] = region
                break
        if result["location"]:
            break
    
    # Extract material type with better pattern matching
    material_patterns = {
        "asphalt": [r'\b(asphalt|composite|shingles?|architectural)\b'],
        "metal": [r'\b(metal|steel|aluminum|tin|copper)\b'],
        "tile": [r'\b(tile|clay|ceramic|terracotta|concrete\s*tile)\b'],
        "slate": [r'\b(slate|stone|natural\s*slate)\b']
    }
    
    for material, patterns in material_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                result["material_type"] = material
                break
        if result["material_type"]:
            break
    
    # Extract timeline with better pattern matching
    timeline_patterns = {
        "standard": [r'\b(standard|normal|regular|usual|typical|60\s*days|2\s*months)\b'],
        "expedited": [r'\b(expedited|rush|urgent|quick|soon|30\s*days|1\s*month)\b'],
        "emergency": [r'\b(emergency|immediate|right\s*away|asap|as\s*soon\s*as\s*possible|immediately|7\s*days|week)\b']
    }
    
    for timeline, patterns in timeline_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                result["timeline"] = timeline
                break
        if result["timeline"]:
            break
    
    # Look for numerical values in responses
    # This helps with extracting values when users just respond with a number
    numerical_response_match = re.match(r'^\s*(\d[\d,]*)\s*$', text.strip())
    if numerical_response_match and not result["square_footage"]:
        result["square_footage"] = float(numerical_response_match.group(1).replace(',', ''))
    
    return result

# Create a function to format extraction responses that considers both user input and context
def format_extraction_response(inputs):
    # Get the current input and the history
    current_input = inputs.get("input", "")
    history = inputs.get("history", [])
    
    # Combine the current message with context from recent history for better extraction
    context = ""
    if history:
        # Get up to the last 3 exchanges for context
        recent_history = history[-6:] if len(history) > 6 else history
        for msg in recent_history:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            context += f"{role}: {msg.content}\n"
    
    # Combine context with current input for better extraction
    full_text = f"{context}\nCurrent User Input: {current_input}"
    
    # Extract information from the combined text
    extraction = extract_info_from_text(full_text)
    result = ExtractedInfo(**extraction)
    print(f"Extracted information from user input: {result}")
    return result

# Define extraction prompt - using a more detailed system prompt
extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant that extracts specific information for a construction estimation system. "
              "Extract ONLY the information explicitly provided by the user in their latest message. "
              "Pay special attention to numbers, measurements, regions, and material types. "
              "For square footage, extract any numerical values followed by sq ft, square feet, etc. "
              "For location, identify regions like northeast, midwest, south, west, or specific states/cities. "
              "For materials, look for specific mentions of asphalt, metal, tile, slate, etc. "
              "For timeline, identify standard, expedited, emergency, or similar terms. "
              "If any information is not clearly provided in the current message, leave that field as null."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Create a more robust extraction chain that processes both history and input
extraction_chain = RunnablePassthrough.assign(
    history=lambda x: x.get("history", []),
    input=lambda x: x.get("input", "")
) | format_extraction_response


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
    from .llm_service import analyze_image, extract_info_from_image_analysis
    
    # Get the latest image reference - this would be set in the handle_image_upload function
    latest_image_ref = state.image_references[-1] if state.image_references else None
    latest_image_data = None
    
    # In a real system, we would retrieve the base64 data for the image here
    # For now, we'll assume it's passed in the state's image_analysis with the key being the image reference
    if latest_image_ref and latest_image_ref in state.image_analysis and "base64_data" in state.image_analysis[latest_image_ref]:
        latest_image_data = state.image_analysis[latest_image_ref]["base64_data"]
        
        # Only analyze if we have image data
        if latest_image_data:
            # Analyze the image using GPT-4o
            analysis = analyze_image(latest_image_data, latest_image_ref)
            
            # Store the analysis
            if latest_image_ref not in state.image_analysis:
                state.image_analysis[latest_image_ref] = {}
            state.image_analysis[latest_image_ref]["analysis"] = analysis
            
            # Extract structured information from the analysis
            extracted_info = extract_info_from_image_analysis(analysis)
            
            # Update the state's extracted info with information from the image
            for key, value in extracted_info.items():
                if value is not None and (key not in state.extracted_info or state.extracted_info[key] is None):
                    state.extracted_info[key] = value
                    print(f"Extracted {key}: {value} from image analysis")
            
            # Add the analysis to the conversation history
            summary = f"I've analyzed your image and found the following: {analysis}"
            state.add_to_history("assistant", summary)
        else:
            # Add a generic confirmation if no image data
            confirmation = "I've received your image, but couldn't analyze it. Please make sure it's a valid image format."
            state.add_to_history("assistant", confirmation)
    else:
        # Add a generic confirmation if no image reference or data
        confirmation = "I've received your image. This will help with the estimation process."
        state.add_to_history("assistant", confirmation)
        
        # Add a reference to the image (this will be used as a placeholder)
        if not latest_image_ref:
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
    # Skip extraction if user input is empty
    if not state.user_input.strip():
        return state
    
    # Create conversation history
    history = []
    for message in state.conversation_history:
        if message["role"] == "assistant":
            history.append(AIMessage(content=message["content"]))
        else:
            history.append(HumanMessage(content=message["content"]))
    
    # Store the most recent question asked to provide context
    last_question = ""
    for i in range(len(state.conversation_history) - 1, -1, -1):
        if state.conversation_history[i]["role"] == "assistant":
            last_question = state.conversation_history[i]["content"]
            break
    
    # Determine if this is answering a specific question
    field_to_update = None
    if "square footage" in last_question.lower() or "area" in last_question.lower() or "how large" in last_question.lower():
        field_to_update = "square_footage"
    elif "location" in last_question.lower() or "region" in last_question.lower() or "where" in last_question.lower():
        field_to_update = "location"
    elif "material" in last_question.lower() or "type of" in last_question.lower():
        field_to_update = "material_type"
    elif "timeline" in last_question.lower() or "how soon" in last_question.lower() or "when" in last_question.lower():
        field_to_update = "timeline"
    
    # For very simple responses that might just contain a value, try direct extraction
    if field_to_update and len(state.user_input.strip().split()) <= 3:
        # Try to directly extract the value if it's a simple response
        value = None
        simple_input = state.user_input.strip().lower()
        
        # Direct mapping for common inputs
        if field_to_update == "location":
            for region in ["northeast", "midwest", "south", "west", "north east", "mid west"]:
                if region in simple_input:
                    value = region.replace(" ", "")
                    break
            # Regional shorthand
            if not value:
                if any(x in simple_input for x in ["ne", "east coast", "ma", "ny"]):
                    value = "northeast"
                elif any(x in simple_input for x in ["mw", "middle", "central", "oh", "il"]):
                    value = "midwest"
                elif any(x in simple_input for x in ["s", "southeast", "fl", "tx", "ga"]):
                    value = "south"
                elif any(x in simple_input for x in ["w", "ca", "west coast", "pacific", "az"]):
                    value = "west"
        
        elif field_to_update == "material_type":
            for material in ["asphalt", "metal", "tile", "slate"]:
                if material in simple_input:
                    value = material
                    break
            if not value and "shingle" in simple_input:
                value = "asphalt"
        
        elif field_to_update == "timeline":
            timeline_map = {
                "standard": ["standard", "normal", "regular", "typical", "60 days", "2 months"],
                "expedited": ["expedited", "rush", "urgent", "quick", "30 days", "1 month"],
                "emergency": ["emergency", "immediate", "asap", "right away", "7 days", "week"]
            }
            for timeline, terms in timeline_map.items():
                if any(term in simple_input for term in terms):
                    value = timeline
                    break
        
        elif field_to_update == "square_footage":
            # Try to extract a number
            import re
            try:
                # First try to find a number with sq ft mention
                sq_ft_match = re.search(r'(\d[\d,]*)\s*(?:sq\.?\s*ft\.?|square\s*feet|square\s*foot)', simple_input)
                if sq_ft_match:
                    value = float(sq_ft_match.group(1).replace(',', ''))
                else:
                    # If no explicit mention, see if it's just a number
                    num_match = re.search(r'(\d[\d,]*)', simple_input)
                    if num_match:
                        value = float(num_match.group(1).replace(',', ''))
            except (ValueError, AttributeError):
                pass
        
        # If we found a value through direct extraction, update it
        if value is not None:
            state.extracted_info[field_to_update] = value
            print(f"Directly extracted {field_to_update}: {value} from simple response")
    
    # Also run the full extraction for comprehensive analysis
    extracted_data = extraction_chain.invoke({
        "history": history,
        "input": state.user_input
    })
    
    # Update extracted info in state, only for fields that have values
    for field, value in extracted_data.dict(exclude_none=True).items():
        if value:  # Only update if value is not None or empty
            state.extracted_info[field] = value
            print(f"Updated {field} to {value} from extraction chain")
    
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
    if state.user_input.strip():  # Only add if non-empty
        print(f"Adding user input to history: '{state.user_input}'")
        state.add_to_history("user", state.user_input)
    
    # Store the user input temporarily for debugging
    user_input_snapshot = state.user_input
    
    # Clear user input for next round
    state.user_input = ""
    
    # Check if we have all required information
    missing_info = get_missing_info(state.required_info, state.extracted_info)
    
    # Debug log
    print(f"Processing user input: '{user_input_snapshot}'")
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


def question_generator(state: GraphState) -> Dict[str, str]:
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
    
    # End the graph execution after generating the question
    # The user will start a new graph execution with their answer
    print("Generated question, ending graph execution")
    return {"next": END}


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
    # End after question_generator rather than cycling back to input_processor
    graph.add_edge("question_generator", END)
    graph.add_edge("estimator", "response_generator")
    graph.add_edge("response_generator", END)
    
    # Compile the graph
    return graph.compile()


# Initialize the graph - this must be done at module level before the functions that use it
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
    """
    # Print message for debugging
    print(f"Processing user message: '{message}'")
    
    # Either use previous state or create a new one
    if prev_state:
        # Use previous state but update the user input
        input_state = prev_state.copy()
        input_state.user_input = message
        print(f"Using existing state, updated user_input to: '{message}'")
    else:
        # Create a brand new state if none exists
        input_state = GraphState(
            session_id=session_id,
            user_input=message
        )
        print(f"Created new state with user_input: '{message}'")
    
    # Check if this is likely a direct answer to a question about a specific field
    if prev_state and len(message.strip().split()) <= 3 and prev_state.current_question:
        question = prev_state.current_question.lower()
        simple_input = message.strip().lower()
        print(f"Detected simple response '{simple_input}' to question: '{question}'")
        
        # Try to perform direct extraction based on the question context
        import re
        if ('square footage' in question or 'area' in question) and re.search(r'\b\d+\b', simple_input):
            # Extract number from simple response
            match = re.search(r'(\d[\d,]*)', simple_input)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    input_state.extracted_info['square_footage'] = value
                    print(f"Pre-extracted square_footage value from direct response: {value}")
                except ValueError:
                    pass
                    
        elif 'location' in question or 'region' in question:
            # Check for location keywords
            for region in ["northeast", "midwest", "south", "west"]:
                if region in simple_input:
                    input_state.extracted_info['location'] = region
                    print(f"Pre-extracted location value from direct response: {region}")
                    break
                    
        elif 'material' in question:
            # Check for material keywords
            for material in ["asphalt", "metal", "tile", "slate"]:
                if material in simple_input:
                    input_state.extracted_info['material_type'] = material
                    print(f"Pre-extracted material_type value from direct response: {material}")
                    break
            if "shingle" in simple_input and 'material_type' not in input_state.extracted_info:
                input_state.extracted_info['material_type'] = "asphalt"
                print(f"Pre-extracted material_type (shingles) as asphalt")
                
        elif 'timeline' in question or 'when' in question or 'how soon' in question:
            # Check for timeline keywords
            timeline_mapping = {
                "standard": ["standard", "normal", "regular"],
                "expedited": ["expedited", "rush", "urgent", "soon"],
                "emergency": ["emergency", "immediate", "asap"]
            }
            for timeline, keywords in timeline_mapping.items():
                if any(keyword in simple_input for keyword in keywords):
                    input_state.extracted_info['timeline'] = timeline
                    print(f"Pre-extracted timeline value from direct response: {timeline}")
                    break
    
    # Run the graph with increased recursion limit to prevent Graph Recursion Error
    try:
        raw_result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 250})
        # Convert raw graph output to GraphState for attribute access
        new_state = GraphState.parse_obj(raw_result)
        print(f"After processing, extracted info: {new_state.extracted_info}")
        return new_state
    except Exception as e:
        # Log error but continue with input_state to prevent losing conversation
        print(f"Error during graph execution: {e}")
        # Add error message to conversation history
        input_state.add_to_history("assistant", "I'm sorry, I encountered an error processing your request. Please try again.")
        return input_state


# Function to handle image upload
async def handle_image_upload(session_id: str, file_description: str, image_data: Optional[str] = None, prev_state: Optional[GraphState] = None) -> GraphState:
    """
    Handle an image upload event.
    
    Args:
        session_id: The session ID
        file_description: Description of the uploaded file
        image_data: Base64 encoded image data
        prev_state: Optional previous graph state to preserve context
        
    Returns:
        Updated graph state after processing the image upload
        
    Note:
        The graph execution terminates after generating a response.
        Each user interaction starts a new graph execution with persisted state.
    """
    # Either use previous state or create a new one
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
    
    # Create a new image reference
    image_ref = f"image_{len(input_state.image_references) + 1}"
    input_state.image_references.append(image_ref)
    
    # Store the base64 image data in the state if provided
    if image_data:
        print(f"Storing base64 image data for {image_ref}")
        # Initialize the image analysis dict for this reference if it doesn't exist
        if image_ref not in input_state.image_analysis:
            input_state.image_analysis[image_ref] = {}
            
        # Store the image data
        input_state.image_analysis[image_ref]["base64_data"] = image_data
    
    # Run the graph with increased recursion limit to prevent Graph Recursion Error
    try:
        raw_result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 250})
        return GraphState.parse_obj(raw_result)
    except Exception as e:
        # Log error but continue with input_state to prevent losing conversation
        print(f"Error during graph execution: {e}")
        # Add error message to conversation history
        input_state.add_to_history("assistant", "I'm sorry, I encountered an error processing your image. Please try again.")
        return input_state
