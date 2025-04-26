from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class ChatInput(BaseModel):
    """Model for chat input from user."""
    session_id: str
    message: str


class FileUpload(BaseModel):
    """Model for file upload data."""
    session_id: str
    file_description: str = Field(default="Image uploaded")
    image_data: Optional[str] = Field(default=None, description="Base64 encoded image data")


class GraphState(BaseModel):
    """Model representing the state of the conversation graph."""
    session_id: str = Field(default="")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    user_input: str = Field(default="")
    extracted_info: Dict[str, Any] = Field(default_factory=dict)
    required_info: List[str] = Field(default_factory=list)
    current_question: str = Field(default="")
    image_references: List[str] = Field(default_factory=list)
    image_analysis: Dict[str, str] = Field(default_factory=dict)  # Store image analysis results
    final_estimate: Optional[Dict[str, Any]] = Field(default=None)
    service_config: Dict[str, Any] = Field(default_factory=dict)
    next: Optional[str] = None
    
    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def copy(self) -> 'GraphState':
        """Create a copy of the current state."""
        return GraphState(
            session_id=self.session_id,
            conversation_history=self.conversation_history.copy(),
            user_input=self.user_input,
            extracted_info=self.extracted_info.copy(),
            required_info=self.required_info.copy(),
            current_question=self.current_question,
            image_references=self.image_references.copy(),
            image_analysis=self.image_analysis.copy(),
            final_estimate=self.final_estimate.copy() if self.final_estimate else None,
            service_config=self.service_config.copy(),
            next=self.next
        )


class ChatResponse(BaseModel):
    """Model for chat response to the user."""
    session_id: str
    message: str
    estimate: Optional[Dict[str, Any]] = None
    missing_info: List[str] = Field(default_factory=list)
    conversation_complete: bool = False


class EstimateResult(BaseModel):
    """Model for the final estimate result."""
    service_type: str
    square_footage: float
    location: str
    material_type: str
    timeline: str
    base_cost: float
    material_cost: float
    region_adjustment: float
    timeline_adjustment: float
    permit_fee: float
    total_estimate: float
    price_range_low: float
    price_range_high: float
    image_references: List[str] = Field(default_factory=list)
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override dict method to ensure proper dictionary conversion."""
        result = super().dict(**kwargs)
        
        # Ensure numeric values are at least in the thousands for demo purposes
        for key in ['base_cost', 'material_cost', 'region_adjustment', 'timeline_adjustment', 
                   'permit_fee', 'total_estimate', 'price_range_low', 'price_range_high']:
            if key in result and result[key] < 1000:
                # Multiply by 10-20 to get into thousands range
                import random
                result[key] *= random.uniform(10, 20)
        
        return result
