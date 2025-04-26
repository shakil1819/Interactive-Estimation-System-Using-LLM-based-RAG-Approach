"""
LLM (Language Learning Model) service for the Interactive Estimation System.
This module handles interactions with LLM APIs for generating responses.
"""
import os
import warnings
import re
from typing import Dict, Any, List, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress PydanticSchemaJson warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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


def analyze_image(base64_image: str, image_name: str = "uploaded_image.jpg") -> str:
    """
    Analyze an image using GPT-4o.
    
    Args:
        base64_image: Base64-encoded image data
        image_name: Name of the image file
        
    Returns:
        Analysis of the image as a string
    """
    try:
        # Check if OPENAI_API_KEY is available
        if OPENAI_API_KEY:
            # Initialize OpenAI client
            try:
                import openai
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                
                # Send image to OpenAI for analysis
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant for a construction estimation system. Analyze the uploaded image and provide relevant details about roofing, construction materials, property condition, and any visible damage or issues that could affect cost estimation."
                        },
                        {
                            "role": "user",
                            "content": [
                                { 
                                    "type": "text", 
                                    "text": f"Please analyze this image of a construction project (filename: {image_name}). Focus on identifying the type of roof, materials used, approximate square footage if possible, any visible damage, and overall condition." 
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=3000
                )
                
                # Extract and return the response text
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error with OpenAI API for image analysis: {e}")
                return _mock_image_analysis(image_name)
        else:
            # Use mock implementation when API key is not available
            return _mock_image_analysis(image_name)
    except Exception as e:
        print(f"Error analyzing image: {e}")
        # Fall back to mock implementation
        return _mock_image_analysis(image_name)


def analyze_image_stream(base64_image: str, prompt: str) -> Any:
    """
    Analyze an image using GPT-4o and return a streaming response.
    
    Args:
        base64_image: Base64-encoded image data
        prompt: The text prompt to send with the image
        
    Returns:
        A streaming response object from OpenAI
    """
    try:
        # Check if OPENAI_API_KEY is available
        if OPENAI_API_KEY:
            # Initialize OpenAI client
            try:
                import openai
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                
                # Send image to OpenAI for streaming analysis
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant for a construction estimation system. Analyze the uploaded image and provide relevant details that could affect cost estimation."
                        },
                        {
                            "role": "user",
                            "content": [
                                { 
                                    "type": "text", 
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                    },
                                },
                            ],
                        }
                    ],
                    stream=True
                )
                
                return stream
            except Exception as e:
                print(f"Error with OpenAI API for image streaming analysis: {e}")
                return None
        else:
            # Use mock implementation when API key is not available
            return None
    except Exception as e:
        print(f"Error analyzing image with streaming: {e}")
        return None


def _mock_image_analysis(image_name: str) -> str:
    """
    Generate a mock image analysis for testing/development without API keys.
    
    Args:
        image_name: Name of the image file
        
    Returns:
        A mock analysis based on the image name
    """
    # Generate a simulated analysis based on the image name
    if "roof" in image_name.lower():
        return "The image shows an asphalt shingle roof in moderate condition. The roof appears to be approximately 1,500-2,000 square feet. There are some signs of wear in the southern exposure, and a few shingles appear to be damaged or missing. The overall condition suggests the roof may be 10-15 years old. No significant structural issues are visible, though there is some buildup of debris in the gutters that should be addressed."
    elif "damage" in image_name.lower():
        return "The image shows significant damage to a section of the roof. There appears to be water damage extending to the underlying structure. The damaged area is approximately 200-300 square feet. The existing roofing material appears to be architectural asphalt shingles. This damage would require immediate attention and likely partial replacement of both the shingles and possibly some of the underlying deck."
    elif "metal" in image_name.lower():
        return "The image shows a metal roof in good condition. The roof appears to be a standing seam metal roof with a silver/gray finish. The approximate area is 1,800 square feet. The installation looks relatively recent, possibly within the last 5 years. There are no visible signs of damage or rust, and the flashing around the chimney and vents appears to be properly installed."
    else:
        return "The image shows a residential property with what appears to be a typical gabled roof. The roofing material looks like standard asphalt shingles in a dark gray or black color. The total roof area is approximately 1,500-2,000 square feet based on the overall house dimensions. The roof appears to be in moderate condition with no immediately obvious major damage or issues, though a closer inspection would be recommended for a complete assessment."


def extract_info_from_image_analysis(analysis: str) -> Dict[str, Any]:
    """
    Extract structured information from image analysis text.
    
    Args:
        analysis: The text analysis of an image
        
    Returns:
        Dictionary of extracted information
    """
    # Initialize empty result
    result = {
        "service_type": None,
        "square_footage": None,
        "material_type": None,
    }
    
    try:
        # Check if OpenAI API key is available for better extraction
        if OPENAI_API_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                
                # Send prompt to OpenAI
                prompt = f"""
                Based on the following image analysis, extract these specific pieces of information:
                1. Service type (e.g., roofing, siding, etc.)
                2. Square footage (numerical value only)
                3. Material type (e.g., asphalt, metal, tile, etc.)
                
                If a piece of information is not mentioned or cannot be determined, return null for that field.
                
                Image Analysis: {analysis}
                
                Format your response as a JSON object with these keys: service_type, square_footage, material_type
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful extraction assistant that only responds with properly formatted JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                
                # Parse the JSON response
                extracted_data = json.loads(response.choices[0].message.content)
                
                # Update result with extracted data
                for key in result:
                    if key in extracted_data and extracted_data[key]:
                        result[key] = extracted_data[key]
                
                # Convert square footage to float if it's a number
                if result["square_footage"] and isinstance(result["square_footage"], str):
                    try:
                        # Extract numerical value from string
                        matches = re.findall(r'[\d,]+', result["square_footage"])
                        if matches:
                            result["square_footage"] = float(matches[0].replace(',', ''))
                    except:
                        # If conversion fails, leave as is
                        pass
                
                return result
            
            except Exception as e:
                print(f"Error with OpenAI API for info extraction: {e}")
                return _extract_info_manually(analysis)
        else:
            # Use manual extraction when API key is not available
            return _extract_info_manually(analysis)
    except Exception as e:
        print(f"Error extracting info from analysis: {e}")
        return _extract_info_manually(analysis)


def _extract_info_manually(analysis: str) -> Dict[str, Any]:
    """
    Manually extract information from analysis text when API is not available.
    
    Args:
        analysis: The text analysis of an image
        
    Returns:
        Dictionary of extracted information
    """
    # Initialize empty result
    result = {
        "service_type": None,
        "square_footage": None,
        "material_type": None,
    }
    
    # Extract service type
    if any(term in analysis.lower() for term in ["roof", "shingle", "asphalt", "metal", "tile", "slate"]):
        result["service_type"] = "roofing"
    
    # Extract square footage
    sq_ft_match = re.search(r'(\d[\d,]*)(?:\s*-\s*\d[\d,]*)?\s*square\s*feet', analysis.lower())
    if sq_ft_match:
        # Extract just the first number if there's a range
        match_text = sq_ft_match.group(1).replace(',', '')
        result["square_footage"] = float(match_text)
    
    # Extract material type
    for material in ["asphalt", "metal", "tile", "slate"]:
        if material in analysis.lower():
            result["material_type"] = material
            break
    
    # If asphalt isn't explicitly mentioned but shingles are, assume asphalt
    if result["material_type"] is None and "shingle" in analysis.lower():
        result["material_type"] = "asphalt"
    
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
