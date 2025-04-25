# Architecture Diagram

## System Components

```
┌───────────────────────────────┐
│       Streamlit Frontend      │
│                               │
│ ┌───────────┐   ┌───────────┐ │
│ │   Chat    │   │   File    │ │
│ │ Interface │   │ Uploader  │ │
│ └───────────┘   └───────────┘ │
└───────────┬───────────────────┘
            │ HTTP
            ▼
┌───────────────────────────────┐
│         FastAPI Backend       │
│                               │
│ ┌───────────┐   ┌───────────┐ │
│ │  Session  │   │   API     │ │
│ │ Management│   │ Endpoints │ │
│ └───────────┘   └───────────┘ │
│                               │
│ ┌───────────────────────────┐ │
│ │    Langgraph Engine       │ │
│ │                           │ │
│ │ ┌───────┐      ┌────────┐ │ │
│ │ │ Start │◄────►│ Input  │ │ │
│ │ │ Node  │      │Processor│ │ │
│ │ └───────┘      └────────┘ │ │
│ │      │             │      │ │
│ │      ▼             ▼      │ │
│ │ ┌─────────┐   ┌─────────┐ │ │
│ │ │ Image   │   │  Info   │ │ │
│ │ │ Handler │   │Extractor│ │ │
│ │ └─────────┘   └─────────┘ │ │
│ │                   │       │ │
│ │                   ▼       │ │
│ │ ┌─────────┐   ┌─────────┐ │ │
│ │ │ Question│◄──│  State  │ │ │
│ │ │Generator│   │ Updater │ │ │
│ │ └─────────┘   └─────────┘ │ │
│ │      │             │      │ │
│ │      │             ▼      │ │
│ │      │        ┌─────────┐ │ │
│ │      └───────►│Estimator│ │ │
│ │               └─────────┘ │ │
│ │                    │      │ │
│ │                    ▼      │ │
│ │               ┌─────────┐ │ │
│ │               │Response │ │ │
│ │               │Generator│ │ │
│ │               └─────────┘ │ │
│ └───────────────────────────┘ │
│                               │
│ ┌───────────┐   ┌───────────┐ │
│ │Estimation │   │ OpenAI/LLM│ │
│ │   Logic   │   │Integration│ │
│ └───────────┘   └───────────┘ │
└───────────────────────────────┘
            │
            ▼
┌───────────────────────────────┐
│     Configuration & Data      │
│                               │
│ ┌───────────┐   ┌───────────┐ │
│ │ config.   │   │  Session  │ │
│ │   json    │   │   State   │ │
│ └───────────┘   └───────────┘ │
└───────────────────────────────┘
```

## Data Flow

1. User interacts with the Streamlit frontend, sending messages or uploading files
2. Frontend sends requests to the FastAPI backend
3. Backend processes the request through the Langgraph conversation flow:
   - Extracts information from user input using LLM
   - Updates the conversation state
   - Generates appropriate responses or questions
4. If all required information is provided, the estimation logic calculates a quote
5. Response is sent back to the frontend and displayed to the user

## Key Components

### Frontend (Streamlit)
- Chat interface for natural language interaction
- File uploader for image submission
- Session state management for conversation history

### Backend (FastAPI)
- RESTful API endpoints for chat and file upload
- Session management for multiple concurrent users
- Integration with Langgraph for conversation flow

### Conversation Graph (Langgraph)
- Nodes for different processing steps
- Conditional edges for flow control
- State management for conversation context

### Estimation Logic
- Configuration-driven pricing calculation
- Support for different materials, regions, and timelines
- Price range calculation with adjustable parameters

## Implementation Details

### Langgraph Conversation Flow

The conversation flow is implemented using Langgraph, which provides a flexible way to create stateful, multi-step workflows. The graph is defined in `backend/app/graph.py` and consists of the following nodes:

1. **Start Node**: Initializes the conversation and provides a welcome message.
2. **Input Processor**: Routes user input to either image handling or information extraction.
3. **Image Handler**: Processes image uploads (currently simple tracking).
4. **Information Extractor**: Extracts structured data from user messages using LLM.
5. **State Updater**: Determines if all required information is present or more questions are needed.
6. **Question Generator**: Creates appropriate questions for missing information.
7. **Estimator**: Calculates the estimate based on gathered information.
8. **Response Generator**: Formats and returns the final response.

#### Graph Flow Control

The graph uses conditional edges to control the flow:
```
start → input_processor → (image_handler or information_extractor) → state_updater
→ (question_generator or estimator) → (input_processor or response_generator) → END
```

Important technical considerations:
- The graph terminates after generating a response (ends at `response_generator`)
- New user inputs start fresh graph executions with the persisted state
- This prevents infinite recursion loops that could occur if the graph continually cycles back

### State Management

State is managed in two layers:

1. **Graph State**: Within a single execution of the Langgraph, using `GraphState` class.
2. **Session State**: Between user interactions, using an in-memory dictionary in the FastAPI app.

#### State Conversion

When Langgraph finishes execution, it returns an `AddableValuesDict` object, not a `GraphState` object. This needs to be converted back:

```python
# Langgraph returns an AddableValuesDict, not a GraphState
result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
# Convert to GraphState for proper attribute access
updated_state = GraphState(**result)
```

### Technical Considerations

1. **Recursion Control**: Using `ainvoke()` instead of `invoke()` with appropriate recursion limits:
   ```python
   # Use ainvoke with recursion_limit to prevent errors
   result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
   ```

2. **Graph Termination**: Ending the graph properly after response generation:
   ```python
   # End the graph execution after response is generated
   graph.add_edge("response_generator", END)
   ```

3. **State Persistence**: Properly storing and retrieving state between graph executions:
   ```python
   # Store state after graph execution
   sessions[session_id] = updated_state
   ```
