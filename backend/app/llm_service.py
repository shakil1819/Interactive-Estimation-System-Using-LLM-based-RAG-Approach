"""
LLM (Language Learning Model) service for the Interactive Estimation System.
This module handles interactions with LLM APIs for generating responses.
"""
import os
import warnings
import re
from typing import Dict, Any, List, Optional

# Suppress PydanticSchemaJson warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def get_llm_response(prompt: str) -> str:
    """
    Get a response from an LLM based on the provided prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response as a string
    """
    try:
        # Check if OPENAI_API_KEY is available
        if OPENAI_API_KEY:
            # Initialize OpenAI client
            try:
                import openai
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                
                # Send prompt to OpenAI
                response = client.chat.completions.create(
                    model="gpt-4o",  # Use an appropriate model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for a construction estimation system."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                # Extract and return the response text
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error with OpenAI API: {e}")
                return _mock_llm_response(prompt)
        else:
            # Use mock implementation when API key is not available
            return _mock_llm_response(prompt)
    except Exception as e:
        print(f"Error calling LLM: {e}")
        # Fall back to mock implementation
        return _mock_llm_response(prompt)


def _extract_info_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extract information from the prompt for mock response generation.
    
    Args:
        prompt: The prompt text
        
    Returns:
        Dictionary of extracted information
    """
    # Convert prompt to lowercase for easier matching
    text = prompt.lower()
    
    # Extract context information
    result = {
        "missing_info": [],
        "has_estimate": False,
        "last_user_message": ""
    }
    
    # Check if we have an estimate
    if "has estimate: true" in text:
        result["has_estimate"] = True
    
    # Extract missing information
    if "missing information:" in text:
        missing_info_text = text.split("missing information:")[1].split("\n")[0].strip()
        if missing_info_text and "[]" not in missing_info_text and "[" in missing_info_text:
            items_text = missing_info_text[missing_info_text.find("[")+1:missing_info_text.find("]")]
            result["missing_info"] = [item.strip().strip("'\"") for item in items_text.split(",") if item.strip()]
    
    # Extract last user message
    if "last user message:" in text:
        message_parts = text.split('last user message: "')
        if len(message_parts) > 1 and '"' in message_parts[1]:
            result["last_user_message"] = message_parts[1].split('"')[0].strip()
    
    print(f"Extracted from prompt: {result}")
    return result


def _mock_llm_response(prompt: str) -> str:
    """
    Generate a mock LLM response for testing/development without API keys.
    
    Args:
        prompt: The prompt sent to the LLM
        
    Returns:
        A mock response based on the prompt content
    """
    # Extract context from the prompt
    context = _extract_info_from_prompt(prompt)
    missing_info = context.get("missing_info", [])
    has_estimate = context.get("has_estimate", False)
    last_user_message = context.get("last_user_message", "")
    
    print(f"Mock LLM responding to: {prompt[:100]}...")
    print(f"Extracted context: {context}")
    
    # Generate appropriate response based on context
    if not missing_info:
        if has_estimate:
            # Handle follow-up questions after estimate is provided
            if any(greeting in last_user_message.lower() for greeting in ["hi", "hello", "hey"]):
                return "Hello! Is there anything specific you'd like to know about your estimate?"
            
            if "thank" in last_user_message.lower():
                return "You're welcome! If you have any other questions about your estimate or our services, feel free to ask."
            
            if any(keyword in last_user_message.lower() for keyword in ["how long", "timeline", "when", "schedule"]):
                return "Based on your selected timeline, we can typically schedule the work within our standard processing times. Would you like me to provide more details on scheduling?"
            
            if any(keyword in last_user_message.lower() for keyword in ["material", "quality", "brand"]):
                return "We use high-quality materials from trusted suppliers. The estimate is based on the material type you've selected. Would you like more information about the specific brands we work with?"
            
            if any(keyword in last_user_message.lower() for keyword in ["warranty", "guarantee"]):
                return "We offer a standard warranty on all our work. The exact terms depend on the service and materials selected. Would you like me to explain our warranty policy in more detail?"
            
            # Default follow-up response
            return "Thank you for your question. Is there anything specific about the estimate you'd like me to clarify or explain further?"
        else:
            # Ready to generate estimate
            return "I have all the information I need. Let me prepare your estimate."
    
    # Ask about missing information
    next_field = missing_info[0] if missing_info else None
    
    # Questions for missing fields
    questions = {
        "service_type": "What type of service are you looking for? (e.g., roofing)",
        "square_footage": "What is the approximate square footage of the area?",
        "location": "In which region are you located? (Northeast, Midwest, South, or West)",
        "material_type": "What type of material would you prefer? For roofing, options include asphalt, metal, tile, or slate.",
        "timeline": "What is your preferred timeline? (standard, expedited, or emergency)"
    }
    
    return questions.get(next_field, f"Please provide information about {next_field.replace('_', ' ')}.")
