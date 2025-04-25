# Contributing to Interactive Estimation System

Thank you for considering contributing to the Interactive Estimation System! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. Harassment or abusive behavior will not be tolerated.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with the following information:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any additional context (e.g., screenshots, environment details)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please open an issue with:

- A clear, descriptive title
- A detailed description of the enhancement
- Any relevant mockups or examples
- Rationale for why this enhancement would be valuable

### Contributing Code

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git

### Installation

1. Clone your fork of the repository
   ```bash
   git clone https://github.com/your-username/interactive-estimation-system.git
   cd interactive-estimation-system
   ```

2. Set up a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies
   ```bash
   pip install -e ".[dev,test]"
   ```

4. Install pre-commit hooks
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run a specific test file
pytest backend/tests/test_app.py
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting

You can run these tools with:
```bash
# Format code
black backend
isort backend

# Check style
flake8 backend
```

Pre-commit hooks will automatically check these when you commit changes.

## Adding a New Service Type

To add a new service type to the system:

1. Use the config_tool.py script to add the service configuration:
   ```bash
   python config_tool.py add your_service_name
   ```

2. Update the appropriate test files to include your new service type

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if necessary
3. Include a description of the changes
4. Link any related issues
5. Wait for review from maintainers

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
