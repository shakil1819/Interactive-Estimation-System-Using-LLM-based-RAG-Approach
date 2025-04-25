import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to path to import the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.estimator import calculate_estimate, get_missing_info


def test_calculate_estimate():
    """Test the estimate calculation logic."""
    # Test case 1: All required information is provided
    service_config = {
        "base_rate_per_sqft": 4.5,
        "materials": {"asphalt": 1.0, "metal": 1.8},
        "regions": {"northeast": 1.2, "midwest": 1.0},
        "timeline_multipliers": {"standard": 1.0, "expedited": 1.5},
        "permit_fee": 500,
        "price_range_percentage": 0.15,
        "required_info": ["square_footage", "location", "material_type", "timeline"]
    }
    
    extracted_info = {
        "square_footage": 1000,
        "location": "northeast",
        "material_type": "metal",
        "timeline": "standard"
    }
    
    result, success = calculate_estimate("roofing", service_config, extracted_info)
    
    assert success is True
    assert result is not None
    assert result.service_type == "roofing"
    assert result.square_footage == 1000
    assert result.location == "northeast"
    assert result.material_type == "metal"
    assert result.timeline == "standard"
    
    # Check calculations
    assert result.base_cost == 1000 * 4.5
    assert result.material_cost == (1000 * 4.5) * 1.8 - (1000 * 4.5)
    assert result.region_adjustment == ((1000 * 4.5) * 1.8) * 1.2 - ((1000 * 4.5) * 1.8)
    
    # Test case 2: Missing required information
    extracted_info = {
        "square_footage": 1000,
        "material_type": "metal"
        # Missing location and timeline
    }
    
    result, success = calculate_estimate("roofing", service_config, extracted_info)
    
    assert success is False
    assert result is None


def test_get_missing_info():
    """Test the function that determines missing information."""
    required_info = ["service_type", "square_footage", "location", "material_type", "timeline"]
    
    # Test case 1: All information is provided
    extracted_info = {
        "service_type": "roofing",
        "square_footage": 1000,
        "location": "northeast",
        "material_type": "metal",
        "timeline": "standard"
    }
    
    missing = get_missing_info(required_info, extracted_info)
    assert missing == []
    
    # Test case 2: Some information is missing
    extracted_info = {
        "service_type": "roofing",
        "square_footage": 1000,
        # Missing location
        "material_type": "metal",
        # Missing timeline
    }
    
    missing = get_missing_info(required_info, extracted_info)
    assert set(missing) == {"location", "timeline"}
    
    # Test case 3: Empty values are considered missing
    extracted_info = {
        "service_type": "roofing",
        "square_footage": 1000,
        "location": "",  # Empty value
        "material_type": "metal",
        "timeline": None  # None value
    }
    
    missing = get_missing_info(required_info, extracted_info)
    assert set(missing) == {"location", "timeline"}


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
