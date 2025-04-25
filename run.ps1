# Check if Python is installed
try {
    $pythonVersion = python --version
    if (-not($pythonVersion -match "Python 3\.[9-9][0-9]")) {
        Write-Host "Python 3.11 or higher is required. You have $pythonVersion"
        exit 1
    }
}
catch {
    Write-Host "Python 3 could not be found. Please install Python 3.11 or higher."
    exit 1
}

# Set environment variables to ignore warnings
$env:PYTHONWARNINGS = "ignore::UserWarning:pydantic"
$env:PYTHONWARNINGS = "ignore::DeprecationWarning:pydantic"

# Check if virtual environment exists
if (-not(Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    
    # Check if venv creation was successful
    if (-not(Test-Path -Path "venv")) {
        Write-Host "Failed to create virtual environment. Please check your Python installation."
        exit 1
    }
}

# Activate virtual environment
.\venv\Scripts\Activate

# Check if dependencies are installed
try {
    python -c "import fastapi"
}
catch {
    Write-Host "Installing dependencies..."
    pip install -e .
}

# Run the application
python run.py
