import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
import os.path


# Load environment variables
load_dotenv()

# Get API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Get server configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "http://localhost")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Get configuration path - check multiple locations
CONFIG_LOCATIONS = [
    os.getenv("CONFIG_PATH", ""),  # From environment variable
    "config.json",                 # Current directory
    "/app/config.json",            # Docker container root
    os.path.join(os.path.dirname(__file__), "../..", "config.json"),  # Project root
    os.path.join(os.path.dirname(__file__), "..", "config.json"),     # Backend directory
]

# Default estimation configuration
DEFAULT_CONFIG = {
    "services": {
        "roofing": {
            "required_info": [
                "service_type",
                "square_footage",
                "location",
                "material_type",
                "timeline"
            ],
            "base_rate_per_sqft": 5.0,
            "materials": {
                "asphalt": 1.0,
                "metal": 1.5,
                "tile": 1.8,
                "slate": 2.2
            },
            "regions": {
                "northeast": 1.2,
                "midwest": 1.0,
                "south": 0.9,
                "west": 1.3
            },
            "timeline_multipliers": {
                "standard": 1.0,
                "expedited": 1.25,
                "emergency": 1.5
            },
            "permit_fee": 250.0,
            "price_range_percentage": 0.1
        }
    }
}


def load_estimation_config() -> Dict[str, Any]:
    """
    Load the estimation configuration from the config file.
    
    Returns:
        Dict[str, Any]: The estimation configuration
    """
    # Try loading from various locations
    for config_path in CONFIG_LOCATIONS:
        if not config_path:
            continue
            
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                print(f"Loaded config from {config_path}")
                return config
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
    
    # If no config file found, use default
    print("Using default configuration as no config file was found")
    return DEFAULT_CONFIG


# Load the estimation configuration
ESTIMATION_CONFIG = load_estimation_config()
