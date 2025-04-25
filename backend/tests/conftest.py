import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to path to import the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.main import app
from backend.app.models import GraphState


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_state():
    """Create a sample GraphState for testing."""
    state = GraphState(session_id="test_session")
    state.extracted_info = {
        "service_type": "roofing",
        "square_footage": 1000,
        "location": "northeast",
        "material_type": "metal",
        "timeline": "standard"
    }
    state.required_info = ["service_type", "square_footage", "location", "material_type", "timeline"]
    return state


@pytest.fixture
def sample_service_config():
    """Create a sample service configuration for testing."""
    return {
        "base_rate_per_sqft": 4.5,
        "materials": {
            "asphalt": 1.0,
            "metal": 1.8,
            "tile": 2.2,
            "slate": 3.0
        },
        "regions": {
            "northeast": 1.2,
            "midwest": 1.0,
            "south": 0.9,
            "west": 1.3
        },
        "timeline_multipliers": {
            "standard": 1.0,
            "expedited": 1.5,
            "emergency": 2.0
        },
        "permit_fee": 500,
        "price_range_percentage": 0.15,
        "required_info": [
            "service_type",
            "square_footage",
            "location",
            "material_type",
            "timeline"
        ]
    }


@pytest.fixture
def sample_estimate():
    """Create a sample estimate result for testing."""
    return {
        "service_type": "roofing",
        "square_footage": 1000,
        "location": "northeast",
        "material_type": "metal",
        "timeline": "standard",
        "base_cost": 4500,
        "material_cost": 3600,
        "region_adjustment": 1620,
        "timeline_adjustment": 0,
        "permit_fee": 500,
        "total_estimate": 10220,
        "price_range_low": 8687,
        "price_range_high": 11753,
        "image_references": ["image_1", "image_2"]
    }
