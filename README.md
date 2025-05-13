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
- AWS credentials configured

### Environment Setup

```bash
# Install Python 3.12 and set up virtual environment
make install
```

### API Key Configuration

To use the `/api/chat` endpoint, you need to create a `.env` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=your-api-key-here
```

This key is loaded automatically when you run the application.

### Local Development

```bash
# Run the FastAPI application locally with hot-reload
make run

# In a separate terminal, test the API
curl http://localhost:8000/hello
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

| Command              | Description                                                      |
| -------------------- | ---------------------------------------------------------------- |
| `make install`       | Set up Python 3.12 virtual environment and install dependencies  |
| `make check`         | Run all code quality checks (linting, formatting, type checking) |
| `make test`          | Run the test suite                                               |
| `make run`           | Run the FastAPI application locally with auto-reload             |
| `make build`         | Generate requirements.txt and build the SAM application          |
| `make deploy`        | Deploy the application to AWS                                    |
| `make deploy-guided` | Deploy with interactive prompts (for first deployment)           |
| `make delete`        | Delete the AWS CloudFormation stack                              |

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
