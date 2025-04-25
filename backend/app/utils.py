import uuid
from typing import Dict, Any, List, Optional
from .models import GraphState


# In-memory store for session states
session_states: Dict[str, GraphState] = {}


def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    session_states[session_id] = GraphState(session_id=session_id)
    return session_id


def get_session_state(session_id: str) -> Optional[GraphState]:
    """Get the state for a given session ID."""
    return session_states.get(session_id)


def update_session_state(session_id: str, state: GraphState) -> None:
    """Update the state for a given session ID."""
    session_states[session_id] = state


def format_estimate_for_display(estimate: Dict[str, Any]) -> str:
    """
    Format the estimate as a readable string for display to the user.
    
    Args:
        estimate: The estimate result as a dictionary
        
    Returns:
        Formatted string representation of the estimate
    """
    if not estimate:
        return "Unable to generate an estimate with the provided information."
    
    formatted = (
        f"# 📋 Estimate for {estimate['service_type'].title()} Service\n\n"
        f"## Project Details:\n"
        f"- **Square Footage**: {estimate['square_footage']} sq ft\n"
        f"- **Location**: {estimate['location'].title()}\n"
        f"- **Material**: {estimate['material_type'].title()}\n"
        f"- **Timeline**: {estimate['timeline'].title()}\n"
    )
    
    if estimate.get('image_references'):
        formatted += f"- **Images Provided**: {len(estimate['image_references'])}\n"
    
    formatted += (
        f"\n## Cost Breakdown:\n"
        f"- **Base Cost**: ${estimate['base_cost']:,.2f}\n"
        f"- **Material Cost**: ${estimate['material_cost']:,.2f}\n"
        f"- **Regional Adjustment**: ${estimate['region_adjustment']:,.2f}\n"
        f"- **Timeline Adjustment**: ${estimate['timeline_adjustment']:,.2f}\n"
        f"- **Permit Fee**: ${estimate['permit_fee']:,.2f}\n"
        f"\n## Total Estimate: ${estimate['total_estimate']:,.2f}\n"
        f"## Price Range: ${estimate['price_range_low']:,.2f} - ${estimate['price_range_high']:,.2f}\n\n"
        f"*Note: This is a preliminary estimate and may change based on final inspection.*"
    )
    
    return formatted


def generate_next_question(missing_info: List[str], extracted_info: Dict[str, Any], has_estimate: bool = False, last_user_message: str = "") -> str:
    """
    Generate the next question to ask based on missing information.
    
    Args:
        missing_info: List of information fields that are still missing
        extracted_info: Dictionary of information that has been extracted
        has_estimate: Boolean indicating if we already have an estimate
        last_user_message: The last message from the user (for contextual responses)
        
    Returns:
        Question string to ask the user
    """
    # If we already have an estimate and get a new message, give a contextual response
    if not missing_info:
        if has_estimate:
            # Provide appropriate responses based on the user's follow-up question
            if last_user_message.lower() in ["hi", "hello", "hey"]:
                return "Hello! Is there anything specific you'd like to know about your estimate?"
            
            if "thank" in last_user_message.lower():
                return "You're welcome! If you have any other questions about your estimate or our services, feel free to ask."

            if any(q in last_user_message.lower() for q in ["how long", "timeline", "when", "schedule"]):
                return "Based on your selected timeline, we can typically schedule the work within our standard processing times. Would you like me to provide more details on scheduling?"
            
            if any(q in last_user_message.lower() for q in ["material", "quality", "brand"]):
                return "We use high-quality materials from trusted suppliers. The estimate is based on the material type you've selected. Would you like more information about the specific brands we work with?"
            
            if any(q in last_user_message.lower() for q in ["warranty", "guarantee"]):
                return "We offer a standard warranty on all our work. The exact terms depend on the service and materials selected. Would you like me to explain our warranty policy in more detail?"
            
            # Default response for other follow-ups
            return "Thank you for your question. Is there anything specific about the estimate you'd like me to clarify or explain further?"
        else:
            return "I have all the information I need. Let me prepare your estimate."
    
    # If there are missing fields, ask about the next one
    next_field = missing_info[0]
    
    questions = {
        "service_type": "What type of service are you looking for? (e.g., roofing)",
        "square_footage": "What is the approximate square footage of the area?",
        "location": "In which region are you located? (Northeast, Midwest, South, or West)",
        "material_type": "What type of material would you prefer? For roofing, options include asphalt, metal, tile, or slate.",
        "timeline": "What is your preferred timeline? (standard, expedited, or emergency)"
    }
    
    return questions.get(next_field, f"Please provide information about {next_field.replace('_', ' ')}.")
