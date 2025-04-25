.PHONY: install test lint format run setup clean

# Default target
all: install test

# Install dependencies
install:
	pip install -e ".[dev,test]"

# Run tests
test:
	pytest

# Run tests with coverage
coverage:
	pytest --cov=backend --cov-report=term --cov-report=html

# Run linting
lint:
	flake8 backend
	isort --check backend
	black --check backend

# Format code
format:
	isort backend
	black backend

# Run the application
run:
	python run.py

# Run backend only
backend:
	cd backend && uvicorn app.main:app --reload --port 8000

# Run frontend only
frontend:
	cd frontend && streamlit run app.py

# Setup initial development environment
setup:
	pip install -e ".[dev,test]"
	pre-commit install

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
