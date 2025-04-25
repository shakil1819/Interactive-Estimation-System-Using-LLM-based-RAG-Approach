import pytest
from fastapi.testclient import TestClient
import json
import os
import sys

# Add the parent directory to path to import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.main import app
from backend.app.models import GraphState
from backend.app.estimator import calculate_estimate


# Create a test client
client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "Interactive Estimation System API is running"}


def test_create_session():
    """Test creating a new session."""
    response = client.post("/api/session")
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert response.json()["session_id"] != ""


def test_chat_endpoint():
    """Test the chat endpoint."""
    # First create a session
    session_response = client.post("/api/session")
    session_id = session_response.json()["session_id"]
    
    # Send a chat message
    chat_response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "I need a new roof"}
    )
    
    # Check the response
    assert chat_response.status_code == 200
    assert "message" in chat_response.json()
    assert chat_response.json()["message"] != ""


def test_calculation_logic():
    """Test the estimation calculation logic."""
    # Sample service configuration
    service_config = {
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
        "price_range_percentage": 0.15
    }
    
    # Sample extracted information
    extracted_info = {
        "service_type": "roofing",
        "square_footage": 2000,
        "location": "northeast",
        "material_type": "metal",
        "timeline": "standard"
    }
    
    # Calculate the estimate
    estimate, success = calculate_estimate(
        service_type="roofing",
        service_config=service_config,
        extracted_info=extracted_info
    )
    
    # Check if calculation was successful
    assert success is True
    assert estimate is not None
    
    # Check specific calculations
    assert estimate.base_cost == 2000 * 4.5
    assert estimate.material_cost > 0
    assert estimate.total_estimate > estimate.base_cost
    
    # Check if price range is calculated correctly
    assert estimate.price_range_high > estimate.total_estimate
    assert estimate.price_range_low < estimate.total_estimate


def test_invalid_session():
    """Test behavior with an invalid session ID."""
    response = client.post(
        "/api/chat",
        json={"session_id": "invalid_session_id", "message": "Hello"}
    )
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
