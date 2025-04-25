# Extending the Interactive Estimation System

This guide provides information on how to extend the system with additional features or functionality.

## Adding New Service Types

The easiest way to extend the system is by adding new service types to the configuration. Use the provided `config_tool.py` script:

```bash
python config_tool.py add <service_name>
```

Follow the prompts to configure:
- Base rate per square foot
- Materials and their multipliers
- Regions and their multipliers
- Timeline options and their multipliers
- Permit fees
- Price range percentages

## Enhancing LLM Information Extraction

To improve information extraction capabilities:

1. Update the `ExtractedInfo` model in `backend/app/graph.py`:

```python
class ExtractedInfo(BaseModel):
    """Information extracted from user messages."""
    service_type: Optional[str] = Field(...)
    square_footage: Optional[float] = Field(...)
    # Add your new fields here
    new_field: Optional[str] = Field(
        None, description="Description of the new field"
    )
```

2. Update the required information list in your service configuration:

```json
"required_info": [
    "service_type",
    "square_footage",
    "location",
    "material_type", 
    "timeline",
    "new_field"
]
```

3. Update the question generation logic in `backend/app/utils.py` to handle the new field:

```python
questions = {
    # Existing questions...
    "new_field": "What is the value for the new field?",
}
```

## Adding Real Image Analysis

To implement actual image analysis:

1. Add a new function in a new file `backend/app/image_analysis.py`:

```python
from PIL import Image
import io

def analyze_image(image_data: bytes) -> dict:
    """
    Analyze an uploaded image and extract relevant information.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dictionary with extracted information
    """
    # Convert bytes to image
    image = Image.open(io.BytesIO(image_data))
    
    # Implement your image analysis logic here
    # This could use a computer vision API, ML model, etc.
    
    # Return extracted information
    return {
        "image_type": "roof",
        "estimated_area": 2000,  # Square feet
        "condition": "good",
        # Other extracted information
    }
```

2. Update the file upload endpoint in `backend/app/main.py` to handle the image data:

```python
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """Handle file upload and analysis."""
    # Read file content
    content = await file.read()
    
    # Analyze the image
    from .image_analysis import analyze_image
    analysis_result = analyze_image(content)
    
    # Process through the graph
    # ... rest of your code
```

3. Update the Streamlit frontend to handle the analysis results.

## Adding Persistent Storage

To implement persistent storage:

1. Create a new file `backend/app/database.py`:

```python
import json
import os
from typing import Dict, Any, Optional

# For a simple JSON-based storage
class JsonStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)
    
    def save_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save session data to storage."""
        all_sessions = self._load_all()
        all_sessions[session_id] = data
        self._save_all(all_sessions)
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from storage."""
        all_sessions = self._load_all()
        return all_sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session from storage."""
        all_sessions = self._load_all()
        if session_id in all_sessions:
            del all_sessions[session_id]
            self._save_all(all_sessions)
    
    def _load_all(self) -> Dict[str, Any]:
        """Load all sessions from storage."""
        with open(self.file_path, "r") as f:
            return json.load(f)
    
    def _save_all(self, data: Dict[str, Any]) -> None:
        """Save all sessions to storage."""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)
```

2. Update the session management in `backend/app/utils.py`:

```python
from .database import JsonStorage

# Initialize storage
storage = JsonStorage("sessions.json")

def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    state = GraphState(session_id=session_id)
    storage.save_session(session_id, state.dict())
    return session_id

def get_session_state(session_id: str) -> Optional[GraphState]:
    """Get the state for a given session ID."""
    data = storage.load_session(session_id)
    if data:
        return GraphState(**data)
    return None

def update_session_state(session_id: str, state: GraphState) -> None:
    """Update the state for a given session ID."""
    storage.save_session(session_id, state.dict())
```

## Adding Authentication

To add a simple authentication system:

1. Install additional dependencies:
   ```bash
   pip install python-jose python-multipart passlib bcrypt
   ```

2. Create `backend/app/auth.py`:
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
   from jose import JWTError, jwt
   from passlib.context import CryptContext
   from datetime import datetime, timedelta
   from typing import Optional, Dict
   
   # Security configuration
   SECRET_KEY = "your-secret-key"  # Change this!
   ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   
   # Password hashing
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   
   # OAuth2 scheme
   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   
   # Mock user database (replace with real database in production)
   users_db = {
       "testuser": {
           "username": "testuser",
           "hashed_password": pwd_context.hash("password123"),
           "disabled": False,
       }
   }
   
   def verify_password(plain_password, hashed_password):
       return pwd_context.verify(plain_password, hashed_password)
   
   def get_user(username: str):
       if username in users_db:
           return users_db[username]
       return None
   
   def authenticate_user(username: str, password: str):
       user = get_user(username)
       if not user:
           return False
       if not verify_password(password, user["hashed_password"]):
           return False
       return user
   
   def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None):
       to_encode = data.copy()
       expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
       to_encode.update({"exp": expire})
       return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
   
   async def get_current_user(token: str = Depends(oauth2_scheme)):
       credentials_exception = HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Could not validate credentials",
           headers={"WWW-Authenticate": "Bearer"},
       )
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           username: str = payload.get("sub")
           if username is None:
               raise credentials_exception
       except JWTError:
           raise credentials_exception
       user = get_user(username)
       if user is None:
           raise credentials_exception
       return user
   ```

3. Update your FastAPI endpoints to require authentication:
   ```python
   @app.post("/api/chat")
   async def chat(
       input_data: ChatInput,
       current_user: dict = Depends(get_current_user)
   ):
       # ... existing code
   ```

## Other Extension Ideas

1. **Multiple Concurrent Services**: Allow users to get estimates for multiple services in one session
2. **User History**: Store past estimates for returning users
3. **PDF Export**: Add functionality to export estimates as PDF documents
4. **Email Integration**: Send estimates to users via email
5. **Payment Integration**: Add ability to take deposits or payments through payment gateways
6. **Scheduling**: Allow users to schedule appointments based on their estimates
7. **Competitor Comparison**: Add features to compare estimates with market rates
8. **Multi-language Support**: Add internationalization for different languages
