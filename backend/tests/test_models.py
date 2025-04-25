import os
import sys
import pytest

# Add the parent directory to path to import the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.models import (
    ChatInput,
    ChatResponse,
    FileUpload,
    GraphState,
    EstimateResult,
)


def test_chat_input_model():
    """Test the ChatInput model."""
    # Create a valid ChatInput instance
    chat_input = ChatInput(session_id="test_session", message="Hello")
    
    # Check that the fields are set correctly
    assert chat_input.session_id == "test_session"
    assert chat_input.message == "Hello"
    
    # Check validation
    with pytest.raises(ValueError):
        # Missing required field
        ChatInput(message="Hello")


def test_file_upload_model():
    """Test the FileUpload model."""
    # Create a FileUpload instance with default description
    file_upload = FileUpload(session_id="test_session")
    
    # Check that the fields are set correctly
    assert file_upload.session_id == "test_session"
    assert file_upload.file_description == "Image uploaded"
    
    # Create a FileUpload instance with custom description
    file_upload = FileUpload(session_id="test_session", file_description="Custom description")
    
    # Check that the fields are set correctly
    assert file_upload.session_id == "test_session"
    assert file_upload.file_description == "Custom description"


def test_graph_state_model():
    """Test the GraphState model."""
    # Create a GraphState instance
    state = GraphState(session_id="test_session")
    
    # Check that defaults are set
    assert state.conversation_history == []
    assert state.user_input == ""
    assert state.extracted_info == {}
    assert state.required_info == []
    assert state.current_question == ""
    assert state.image_references == []
    assert state.final_estimate is None
    
    # Test the add_to_history method
    state.add_to_history("user", "Hello")
    assert len(state.conversation_history) == 1
    assert state.conversation_history[0]["role"] == "user"
    assert state.conversation_history[0]["content"] == "Hello"
    
    state.add_to_history("assistant", "Hi there")
    assert len(state.conversation_history) == 2
    assert state.conversation_history[1]["role"] == "assistant"
    assert state.conversation_history[1]["content"] == "Hi there"


def test_estimate_result_model():
    """Test the EstimateResult model."""
    # Create an EstimateResult instance
    estimate = EstimateResult(
        service_type="roofing",
        square_footage=1000,
        location="northeast",
        material_type="metal",
        timeline="standard",
        base_cost=4500,
        material_cost=3600,
        region_adjustment=1620,
        timeline_adjustment=0,
        permit_fee=500,
        total_estimate=10220,
        price_range_low=8687,
        price_range_high=11753,
    )
    
    # Check that the fields are set correctly
    assert estimate.service_type == "roofing"
    assert estimate.square_footage == 1000
    assert estimate.location == "northeast"
    assert estimate.material_type == "metal"
    assert estimate.timeline == "standard"
    assert estimate.base_cost == 4500
    assert estimate.material_cost == 3600
    assert estimate.region_adjustment == 1620
    assert estimate.timeline_adjustment == 0
    assert estimate.permit_fee == 500
    assert estimate.total_estimate == 10220
    assert estimate.price_range_low == 8687
    assert estimate.price_range_high == 11753
    assert estimate.image_references == []
    
    # Test with image references
    estimate = EstimateResult(
        service_type="roofing",
        square_footage=1000,
        location="northeast",
        material_type="metal",
        timeline="standard",
        base_cost=4500,
        material_cost=3600,
        region_adjustment=1620,
        timeline_adjustment=0,
        permit_fee=500,
        total_estimate=10220,
        price_range_low=8687,
        price_range_high=11753,
        image_references=["image_1", "image_2"],
    )
    
    assert estimate.image_references == ["image_1", "image_2"]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
