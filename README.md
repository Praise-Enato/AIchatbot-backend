# Chatbot Backend

A modern serverless API template built with FastAPI and AWS Lambda. This project provides a production-ready starting point for building serverless API applications with Python 3.12.

## Overview

This project implements a simple API for an example AI chatbot. It serves as a template that demonstrates best practices for:

- FastAPI application structure
- AWS Lambda deployment via SAM
- Structured JSON logging
- Modern Python tooling (uv, ruff, mypy)
- Strict type checking and code quality enforcement

Developers can use this as a foundation for building their own serverless API applications.

## Features

- **FastAPI Backend**: Fast, modern Python web framework
- **AWS Lambda Deployment**: Serverless deployment using AWS SAM and Lambda Function URLs
- **Dependency Management**: Modern `uv` package manager for fast, deterministic installs
- **Strict Type Checking**: Comprehensive static type checking with mypy
- **Code Quality Tools**: Pre-commit hooks, ruff formatter/linter, and more
- **Testing Framework**: Ready-to-use pytest configuration
- **Production-Ready Logging**: Structured JSON logging for better observability

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv) - Modern Python package manager
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) - For deployment
- [Java Runtime Environment (JRE)](https://www.oracle.com/java/technologies/downloads/) - Required for DynamoDB Local testing
- [yq](https://github.com/mikefarah/yq) - YAML processor for extracting table schemas
- AWS credentials configured

### Environment Setup

```bash
# Install Python 3.12 and set up virtual environment
make install
```

### Environment Variables

To use the API endpoints, you need to set up the following environment variables in a `.env` file in the project root:

```
# Required for authentication to the API endpoints
API_SECRET=your-secret-key-here

# Required for OpenAI API access
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Specify which LLM provider to use (defaults to 'openai')
PROVIDER_NAME=openai

# Required for DynamoDB Local development
DYNAMODB_URL=http://localhost:8000
```

An `.env.example` file is provided as a template. These environment variables are loaded automatically when you run the application.

### Local Development with DynamoDB

For local development with persistent data:

```bash
# Initial setup: Start DynamoDB Local and create tables
make dynamodb-setup

# Run the FastAPI application (requires DynamoDB to be running)
make run

# In a separate terminal, test the API
curl http://localhost:8080/hello
```

To manage DynamoDB Local:

```bash
# Start DynamoDB with persistent storage
make dynamodb-start

# Start DynamoDB in-memory (no persistence)
make dynamodb-start-inmemory

# Check if DynamoDB is running
make dynamodb-status

# Stop DynamoDB
make dynamodb-stop

# Reset DynamoDB (delete all data and recreate tables)
make dynamodb-reset
```

We use [Bruno](https://www.usebruno.com/) to test and document our API. You can find API collection files in the `/bruno` directory.

### Building and Deploying

```bash
# Build the SAM application
make build

# Deploy to AWS (uses AWS credentials)
make deploy

# Deploy with guided setup (for first-time setup)
make deploy-guided
```

## Development Workflow

1. **Setup**: Run `make install` to create the development environment
2. **Develop**: Make changes to the codebase
3. **Test Locally**: Run `make run` to test locally
4. **Quality Check**: Run `make check` to verify code quality
5. **Test**: Run `make test` to run the test suite
6. **Deploy**: Run `make deploy` to deploy to AWS

## Testing

This project includes both unit tests and integration tests:

### Running Tests

```bash
# Run fast unit tests only (excludes integration tests)
make test

# Run all tests including integration tests with DynamoDB Local
make test-all
```

### Integration Tests with DynamoDB Local

The `make test-all` command automatically:

1. **Downloads and starts DynamoDB Local** on port 8000 (if not already running)
2. **Creates the required database tables** from the SAM template
3. **Runs all tests** including slow integration tests that use real database operations
4. **Stops DynamoDB Local** when tests complete

### Troubleshooting DynamoDB Local

If you encounter issues with DynamoDB Local during testing (such as "port already in use" errors), you can manually manage the DynamoDB Local instance:

```bash
# Stop any running DynamoDB Local instance
make dynamodb-stop

# Check DynamoDB Local status
make dynamodb-status

# Kill any process using port 8000 (if needed)
lsof -ti:8000 | xargs kill -9
```

The integration tests use DynamoDB Local in-memory mode and will automatically connect to it using the `DYNAMODB_URL` environment variable from your `.env` file.

## Working with Dependencies

This project uses `uv` to manage dependencies, which is significantly faster than pip:

```bash
# Add a new package
uv add fastapi

# Add a development-only package
uv add --dev pytest

# Remove a package
uv remove fastapi

# Update dependencies after pyproject.toml changes
make install
```

## Available Make Commands

```bash
# View all available commands
make help
```

| Command              | Description                                                        |
| -------------------- | ------------------------------------------------------------------ |
| `make install`       | Set up Python 3.12 virtual environment and install dependencies    |
| `make check`         | Run all code quality checks (linting, formatting, type checking)   |
| `make test`          | Run the test suite (excludes slow integration tests)               |
| `make test-all`      | Run all tests including slow integration tests with DynamoDB Local |
| `make run`           | Run the FastAPI application locally with auto-reload               |
| `make build`         | Generate requirements.txt and build the SAM application            |
| `make deploy`        | Deploy the application to AWS                                      |
| `make deploy-guided` | Deploy with interactive prompts (for first deployment)             |
| `make delete`        | Delete the AWS CloudFormation stack                                |

## Project Structure

- `src/chatbot_backend/`: Core application code
  - `app.py`: Main FastAPI application with Lambda handler
- `scripts/`: Utility scripts for testing and development
- `tests/`: Test suite
- `template.yaml`: AWS SAM template defining infrastructure

## Adding Your Own Routes

To add a new endpoint, modify `src/chatbot_backend/app.py`:

```python
@app.get("/my-new-endpoint", response_model=YourResponseModel)
async def my_new_endpoint(request: Request) -> YourResponseModel:
    """New endpoint that returns a response."""
    logger.info("My new endpoint called", extra={"path": request.url.path})
    # Your logic here
    return YourResponseModel(...)
```

## AWS Lambda Integration

The application uses [Mangum](https://github.com/jordaneremieff/mangum) to adapt the FastAPI app to AWS Lambda:

```python
# AWS Lambda handler - integrates FastAPI with AWS Lambda
handler = Mangum(app)
```

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.
