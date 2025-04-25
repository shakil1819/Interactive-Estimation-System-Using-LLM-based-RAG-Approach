import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to path to import the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.models import GraphState
from backend.app.graph import (
    start_node,
    input_processor,
    information_extractor,
    state_updater,
    question_generator,
    estimator_node,
    response_generator,
    image_handler_node,
)


def test_start_node():
    """Test the start node of the graph."""
    # Create an initial state
    state = GraphState(session_id="test_session")
    
    # Mock the ESTIMATION_CONFIG
    with patch("backend.app.graph.ESTIMATION_CONFIG", {"services": {"roofing": {"required_info": ["test_field"]}}}):
        # Run the start node
        result = start_node(state)
        
        # Check that the conversation history was updated with a greeting
        assert len(result.conversation_history) > 0
        assert any("Welcome" in msg["content"] for msg in result.conversation_history if msg["role"] == "assistant")
        
        # Check that the service config was stored
        assert result.service_config == {"required_info": ["test_field"]}
        
        # Check that the required info was stored
        assert result.required_info == ["test_field"]
        
        # Check that a question was generated
        assert result.current_question != ""


def test_input_processor():
    """Test the input processor node of the graph."""
    # Test case 1: Regular input
    state = GraphState(session_id="test_session", user_input="I need a new roof")
    result = input_processor(state)
    assert result["next"] == "information_extractor"
    
    # Test case 2: Input mentioning an image
    state = GraphState(session_id="test_session", user_input="I've uploaded an image of my roof")
    result = input_processor(state)
    assert result["next"] == "image_handler"


def test_image_handler_node():
    """Test the image handler node of the graph."""
    state = GraphState(session_id="test_session", user_input="I've uploaded an image")
    
    # Run the image handler
    result = image_handler_node(state)
    
    # Check that a confirmation message was added
    assert any("image" in msg["content"] for msg in result.conversation_history if msg["role"] == "assistant")
    
    # Check that an image reference was added
    assert len(result.image_references) == 1


def test_state_updater():
    """Test the state updater node of the graph."""
    # Test case 1: Missing information
    state = GraphState(
        session_id="test_session",
        user_input="I need a new roof",
        required_info=["service_type", "square_footage"],
        extracted_info={"service_type": "roofing"}
    )
    
    result = state_updater(state)
    
    # Check that the user input was added to history
    assert any("I need a new roof" in msg["content"] for msg in state.conversation_history if msg["role"] == "user")
    
    # Check that we're going to the question generator due to missing info
    assert result["next"] == "question_generator"
    
    # Test case 2: All information provided
    state = GraphState(
        session_id="test_session",
        user_input="I need a new roof",
        required_info=["service_type"],
        extracted_info={"service_type": "roofing"}
    )
    
    result = state_updater(state)
    
    # Check that we're going to the estimator node
    assert result["next"] == "estimator"


def test_question_generator():
    """Test the question generator node of the graph."""
    state = GraphState(
        session_id="test_session",
        required_info=["square_footage", "location"],
        extracted_info={"service_type": "roofing"}
    )
    
    result = question_generator(state)
    
    # Check that a question was generated
    assert result.current_question != ""
    
    # Check that the question was added to the conversation history
    assert any(result.current_question in msg["content"] for msg in result.conversation_history if msg["role"] == "assistant")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
