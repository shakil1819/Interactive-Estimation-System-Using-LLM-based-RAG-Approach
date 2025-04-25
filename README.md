# Interactive Estimation System (Prototype)

A prototype interactive estimation system using FastAPI, Langgraph, and Streamlit. This system guides users through a conversational flow to gather information for a service (e.g., roofing) and provides a structured estimate.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Features

- **Conversational Flow**: Natural language conversation to gather project requirements
- **Image Upload Support**: Users can upload images related to their projects
- **Smart Information Extraction**: Uses AI to extract relevant information from user messages
- **Dynamic Questioning**: Adapts questions based on missing information
- **Configurable Estimation Logic**: Estimation calculations based on a flexible configuration
- **Real-time Feedback**: Updates the estimate as more information is provided

## 🚀 Quick Start

### Using Scripts

**Windows**:
```powershell
# Run the PowerShell script
.\run.ps1
```

**macOS/Linux**:
```bash
# Make the script executable
chmod +x run.sh

# Run the script
./run.sh
```

### Manual Setup

1. Clone the repository and navigate to the project directory
2. Create and activate a virtual environment
3. Install dependencies: `pip install -e .`
4. Set up your environment variables (copy `.env.example` to `.env` and add your OpenAI API key)
5. Run the application: `python run.py`

### Using Docker

```bash
docker-compose up
```

## 📚 Documentation

- [Installation Guide](INSTALL.md) - Detailed setup instructions
- [User Guide](USER_GUIDE.md) - How to use the system
- [Architecture](ARCHITECTURE.md) - System design and components

## 🏗️ Project Architecture

The system is built using a modern stack:

- **Backend**: FastAPI, Pydantic, Langchain, Langgraph, Uvicorn
- **Frontend**: Streamlit
- **State Management**: In-memory dictionary (for prototype simplicity)
- **Language Model**: OpenAI GPT-4 (via Langchain)

### Component Overview

1. **Input Handler** (FastAPI & Streamlit):
   - Accept text input and image uploads from users
   - Manages session state and communication between frontend and backend

2. **Conversation Manager** (FastAPI & Langgraph):
   - Maintains conversation state for each user session
   - Uses Langgraph to define and manage the conversation flow
   - Extracts information from user inputs
   - Generates appropriate responses and questions

3. **Estimation Logic** (Python):
   - Calculates estimates based on the provided configuration
   - Supports various parameters (materials, regions, timelines, etc.)
   - Generates a structured output with cost breakdown

### Directory Structure

```
interactive-estimation-system/
├── backend/                   # FastAPI backend
│   ├── app/                   # Application code
│   │   ├── __init__.py        
│   │   ├── main.py            # FastAPI app, endpoints
│   │   ├── models.py          # Pydantic models
│   │   ├── graph.py           # Langgraph definition
│   │   ├── estimator.py       # Estimation calculation logic
│   │   ├── config.py          # Load estimation config, API keys
│   │   └── utils.py           # Helper functions
│   └── requirements.txt       # Backend dependencies
├── frontend/                  # Streamlit frontend
│   ├── app.py                 # Streamlit application
│   └── requirements.txt       # Frontend dependencies
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker build instructions
├── setup.py                   # Package installation
├── run.py                     # Script to run both servers
├── run.ps1                    # PowerShell script for Windows
├── run.sh                     # Bash script for Unix/Linux
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore file
├── ARCHITECTURE.md            # System architecture details
├── INSTALL.md                 # Installation instructions
├── USER_GUIDE.md              # User documentation
└── README.md                  # Project documentation
```

## 💻 Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

### Adding New Services

To add new service types:

1. Update the `config.json` file with the new service configuration
2. Add appropriate question templates in `utils.py`
3. Update the information extraction schema in `graph.py` if needed

## 🚧 Limitations & Future Enhancements

This prototype has several limitations that could be addressed in future versions:

- **State Management**: Currently uses in-memory storage, which is not persistent
- **Image Analysis**: Only tracks image uploads without actual analysis
- **Error Handling**: Basic error handling implemented
- **Service Types**: Currently focused on roofing; could be expanded

Potential enhancements:

- **Persistent Storage**: Add a database for session storage
- **Real Image Analysis**: Integrate computer vision to extract information from images
- **Multiple Service Types**: Expand to support various service types
- **User Authentication**: Add user accounts and authentication
- **Enhanced UI**: More interactive and responsive frontend

## 📝 License

[MIT License](LICENSE)

## 👥 Contributors

- [Your Name](https://github.com/yourusername)

## 🙏 Acknowledgments

- OpenAI for the GPT models
- Langchain and Langgraph for the conversation flow management
- FastAPI and Streamlit for the application framework
