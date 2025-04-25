# Installation and Setup Guide

This guide will help you set up and run the Interactive Estimation System.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- An OpenAI API key (or another compatible LLM provider)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd interactive-estimation-system
```

### 2. Set Up a Virtual Environment

**Windows**:
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

You can install all dependencies at once using the setup.py file:

```bash
pip install -e .
```

Or install backend and frontend dependencies separately:

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env  # On Windows: copy .env.example .env
   ```

2. Open the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 5. Run the Application

You can run both the backend and frontend with a single command:

```bash
python run.py
```

Or run them separately:

**Backend**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend
streamlit run app.py
```

### 6. Access the Application

Open your web browser and navigate to:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000/docs

## Troubleshooting

### Common Issues

1. **API Key Issues**:
   - Make sure your OpenAI API key is valid and correctly set in the `.env` file
   - Check if you have sufficient credits in your OpenAI account

2. **Dependency Issues**:
   - Make sure you're using Python 3.11 or higher
   - Try updating pip: `pip install --upgrade pip`
   - If you encounter conflicts, try creating a fresh virtual environment

3. **Port Conflicts**:
   - If ports 8000 or 8501 are already in use, you can modify the port settings in the `.env` file

### Getting Help

If you encounter any issues not covered here, please [open an issue](link-to-issues) in the repository or contact the project maintainers.
