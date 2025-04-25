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
