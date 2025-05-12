# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an example chatbot. It's built as a FastAPI server that interfaces with OpenAI for generating responses. The project serves as an educational example for students, so code quality is of the highest importance.

## Architecture

- FastAPI backend that calls OpenAI to generate chatbot responses
- Deployment via AWS Lambda using Mangum, Lambda Function URLs, and AWS SAM
- Python scripts in the `scripts/` directory function similar to notebooks for testing and evaluating chatbot responses

## Development Commands

### Environment Setup

```bash
# Install Python 3.12 and set up virtual environment
make install
```

### Dependency Management

```bash
# Add a dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Sync dependencies after changes to pyproject.toml
make install
```

### Code Quality

```bash
# Run all code quality checks (linting, formatting, dependency check)
make check

# Run individual checks
uv run pre-commit run -a  # Run all pre-commit hooks
uv run deptry .           # Check for obsolete dependencies
```

### Testing

```bash
# Run all tests
make test

# Run a specific test file
uv run python -m pytest tests/path/to/test_file.py

# Run a specific test function
uv run python -m pytest tests/path/to/test_file.py::test_function_name
```

### Running Scripts

```bash
# Run a script using uv
uv run scripts/<script_name>.py

# Alternative: activate the virtual environment and run scripts
source .venv/bin/activate
python scripts/<script_name>.py
```

### Help

```bash
# Display available make commands with descriptions
make help
```

## Project Structure

- `src/chatbot_backend/`: Core library code
  - Main FastAPI application will be located here
  - API endpoints for the chatbot interface
  - OpenAI integration components
  - AWS Lambda/Mangum integration
- `scripts/`: Notebook-like Python scripts for testing and evaluating chatbot responses
- `tests/`: Test suite for ensuring code quality

## Code Standards

- **Python Version**: 3.12+
- **Type Checking**: Strict typing with mypy
- **Code Style**: Enforced by ruff (linting and formatting)
- **Pre-commit Hooks**: Various checks including:
  - Code formatting (ruff)
  - Import sorting
  - Type checking (mypy)
  - Security checks (detect-private-key)
  - Code quality (pyupgrade, etc.)

## Development Workflow

1. Set up the environment with `make install`
2. Make code changes
3. Run `make check` to ensure code quality
4. Run `make test` to verify functionality
5. Create a commit (pre-commit hooks will run automatically)

## AWS Deployment

The application is designed to be deployed as an AWS Lambda function:

- Uses Mangum as an ASGI adapter for FastAPI
- Configured with Lambda Function URLs for direct access
- AWS SAM for infrastructure as code and deployment management
