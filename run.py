import subprocess
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
import time

# Filter out PydanticSchemaJson warnings at the system level
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/object/apply:.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/.*", category=UserWarning)

def run_backend():
    """Run the backend server using uvicorn."""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"]
    return subprocess.Popen(cmd, cwd=backend_dir)

def run_frontend():
    """Run the Streamlit frontend."""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    return subprocess.Popen(cmd, cwd=frontend_dir)

def main():
    """Run both the backend and frontend servers."""
    print("Starting Interactive Estimation System...")
    
    # Give the backend a moment to start before launching the frontend
    backend_process = run_backend()
    print("Backend server starting...")
    
    # Wait a moment to ensure backend is up
    time.sleep(2)
    
    # Start frontend
    frontend_process = run_frontend()
    print("Frontend server starting...")
    
    try:
        # Keep the main process running while the subprocesses are active
        while backend_process.poll() is None and frontend_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        # Clean up processes
        if backend_process.poll() is None:
            backend_process.terminate()
        if frontend_process.poll() is None:
            frontend_process.terminate()
        
        print("Servers stopped.")

if __name__ == "__main__":
    main()
