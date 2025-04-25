from typing import Dict, Any, Tuple, Optional
from .models import EstimateResult


def calculate_estimate(
    service_type: str,
    service_config: Dict[str, Any],
    extracted_info: Dict[str, Any],
    image_references: Optional[list] = None
) -> Tuple[EstimateResult, bool]:
    """
    Calculate the estimate based on the provided information and service configuration.
    
    Args:
        service_type: Type of service (e.g., "roofing")
        service_config: Configuration for the service
        extracted_info: Information extracted from the conversation
        image_references: Optional list of image references
        
    Returns:
        Tuple containing:
        - EstimateResult: The calculated estimate result
        - bool: Whether the estimate calculation was successful
    """
    # Check if we have all required information
    required_info = service_config.get("required_info", [])
    
    # Check if all required fields are present
    for field in required_info:
        if field not in extracted_info or not extracted_info[field]:
            return None, False
    
    # Extract values
    square_footage = float(extracted_info.get("square_footage", 0))
    location = extracted_info.get("location", "").lower()
    material_type = extracted_info.get("material_type", "").lower()
    timeline = extracted_info.get("timeline", "").lower()
    
    # Get configuration values
    base_rate = service_config.get("base_rate_per_sqft", 0)
    materials = service_config.get("materials", {})
    regions = service_config.get("regions", {})
    timeline_multipliers = service_config.get("timeline_multipliers", {})
    permit_fee = service_config.get("permit_fee", 0)
    price_range_percentage = service_config.get("price_range_percentage", 0.1)
    
    # Default multipliers if specific ones not found
    material_multiplier = materials.get(material_type, 1.0)
    region_multiplier = regions.get(location, 1.0)
    timeline_multiplier = timeline_multipliers.get(timeline, 1.0)
    
    # Calculate costs
    base_cost = base_rate * square_footage
    material_cost = base_cost * material_multiplier
    region_adjustment = material_cost * region_multiplier - material_cost
    timeline_adjustment = (material_cost + region_adjustment) * timeline_multiplier - (material_cost + region_adjustment)
    
    # Calculate total
    subtotal = base_cost + (material_cost - base_cost) + region_adjustment + timeline_adjustment
    total_estimate = subtotal + permit_fee
    
    # Calculate price range
    price_range_low = total_estimate * (1 - price_range_percentage)
    price_range_high = total_estimate * (1 + price_range_percentage)
    
    # Format the estimate result
    result = EstimateResult(
        service_type=service_type,
        square_footage=square_footage,
        location=location,
        material_type=material_type,
        timeline=timeline,
        base_cost=base_cost,
        material_cost=material_cost - base_cost,  # Just the additional cost due to material
        region_adjustment=region_adjustment,
        timeline_adjustment=timeline_adjustment,
        permit_fee=permit_fee,
        total_estimate=total_estimate,
        price_range_low=price_range_low,
        price_range_high=price_range_high,
        image_references=image_references or []
    )
    
    return result, True


def format_currency(amount: float) -> str:
    """Format a number as USD currency."""
    return f"${amount:,.2f}"


def get_missing_info(required_info: list, extracted_info: Dict[str, Any]) -> list:
    """
    Determine which required information is still missing.
    
    Args:
        required_info: List of required information fields
        extracted_info: Dictionary of information that has been extracted
        
    Returns:
        List of missing information fields
    """
    missing = []
    for field in required_info:
        if field not in extracted_info or not extracted_info[field]:
            missing.append(field)
    return missing
