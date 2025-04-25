import os
import json
from typing import Dict, Any
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Get API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Get server configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "http://localhost")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Get configuration path
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")


def load_estimation_config() -> Dict[str, Any]:
    """
    Load the estimation configuration from the config file.
    
    Returns:
        Dict[str, Any]: The estimation configuration
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {"services": {}}


# Load the estimation configuration
ESTIMATION_CONFIG = load_estimation_config()
