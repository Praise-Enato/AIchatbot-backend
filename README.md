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
- **Streaming Support**: Real-time streaming responses using AWS Lambda Web Adapter
- **Dependency Management**: Modern `uv` package manager for fast, deterministic installs
- **Strict Type Checking**: Comprehensive static type checking with mypy
- **Code Quality Tools**: Pre-commit hooks, ruff formatter/linter, and more
- **Testing Framework**: Ready-to-use pytest configuration
- **Production-Ready Logging**: Structured JSON logging for better observability

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv) - Modern Python package manager
- [Docker](https://www.docker.com/get-started) - For building container images
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

# Optional: S3 bucket for data storage (include s3:// prefix)
DATA_S3_BUCKET=s3://your-bucket-name/path

# Optional: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=DEBUG
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

For frontend testing and quick development:

```bash
# Start DynamoDB in-memory and run the server in one command
make dev

# This automatically:
# - Starts DynamoDB Local in in-memory mode
# - Creates required database tables
# - Starts the FastAPI server on 0.0.0.0:8080
# - Perfect for running frontend tests or local development

# Stop when done
make dynamodb-stop
```

### Docker Development

You can also run the application in a Docker container locally:

```bash
# Run the application in Docker (automatically manages DynamoDB Local)
make docker-run

# This will:
# - Start DynamoDB Local if not already running
# - Build the Docker image
# - Run the container with proper networking for your OS
# - Stop DynamoDB Local when done (if it started it)
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

Before deploying to AWS, you must set up the required secrets in AWS Systems Manager Parameter Store.

#### 1. Set Up AWS Parameters (Required Before First Deployment)

Create the required secure parameters in AWS Systems Manager:

```bash
# Set your API secret for authentication
aws ssm put-parameter \
  --name "/chatbot/api-secret" \
  --value "your-secure-api-secret-here" \
  --type "SecureString" \
  --description "API secret for chatbot authentication"

# Set your OpenAI API key
aws ssm put-parameter \
  --name "/chatbot/openai-api-key" \
  --value "sk-your-openai-api-key-here" \
  --type "SecureString" \
  --description "OpenAI API key for chatbot responses"
```

**Important Notes:**

- Replace `your-secure-api-secret-here` with a strong, unique secret
- Replace `sk-your-openai-api-key-here` with your actual OpenAI API key
- These parameters are encrypted at rest using AWS KMS
- You only need to set these once per AWS account/region

#### 2. Verify Parameters (Optional)

```bash
# List your parameters (values won't be shown)
aws ssm describe-parameters --filters "Key=Name,Values=/chatbot/"

# Test parameter access (will show decrypted value)
aws ssm get-parameter --name "/chatbot/api-secret" --with-decryption
```

#### 3. Deploy the Application

```bash
# Build the SAM application
make build

# Deploy to AWS (uses AWS credentials and SSM parameters)
make deploy

# Deploy with guided setup (for first-time setup)
make deploy-guided
```

#### 4. Update Secrets (When Needed)

To change secrets without redeploying:

```bash
# Update API secret
aws ssm put-parameter \
  --name "/chatbot/api-secret" \
  --value "new-secret-value" \
  --type "SecureString" \
  --overwrite

# Update OpenAI API key
aws ssm put-parameter \
  --name "/chatbot/openai-api-key" \
  --value "sk-new-openai-key" \
  --type "SecureString" \
  --overwrite
```

The Lambda function will automatically use the new values without requiring a redeployment.

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

### DynamoDB Workbench

AWS provides DynamoDB Workbench, a GUI tool for examining and querying DynamoDB databases. This is useful for debugging and inspecting your local DynamoDB data.

To use DynamoDB Workbench with your local DynamoDB:

1. **Start DynamoDB Local first** - The database must be running before you can connect:

   ```bash
   make dynamodb-start  # For persistent storage
   # or
   make dynamodb-start-inmemory  # For temporary in-memory storage
   ```

2. **Download DynamoDB Workbench** from the [AWS documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html)

3. **Connect to Local DynamoDB**:

   - Launch DynamoDB Workbench
   - Click "Operation builder"
   - Click "Add connection"
   - Select "DynamoDB local"
   - Click "Connect"

4. **Use the Workbench** to:
   - Browse table contents
   - Run queries and scans
   - Test access patterns
   - Debug data issues

Note: DynamoDB Workbench connects to the default local port (8000). Make sure no other services are using this port.

## Data Management

This project supports storing large datasets in AWS S3 that are excluded from Git. Data files should use explicit dates in filenames for versioning (e.g., `dataset_2024-01-15.json`).

### Setup

1. Add your S3 bucket to `.env`:

   ```
   DATA_S3_BUCKET=s3://your-bucket-name/path
   ```

2. Ensure you have AWS credentials configured with appropriate S3 permissions.

### Data Commands

```bash
# Download data from S3 to local /data directory
make data-down

# Upload local data to S3
make data-up

# Preview what would be uploaded (dry run)
make data-up-dry

# Check local data directory sizes
make data-size
```

**Important Notes:**

- The `/data` directory is excluded from Git via `.gitignore`
- `make data-down` uses the `--delete` flag to ensure local data matches S3 exactly
- Always use explicit dates in filenames for version control
- Consider S3 lifecycle policies for managing old data versions

## Logging Configuration

The application uses Python's standard logging module with configurable log levels:

### Log Levels

Set the `LOG_LEVEL` environment variable in your `.env` file:

```
LOG_LEVEL=DEBUG    # Show all logs (development)
LOG_LEVEL=INFO     # Show info, warning, error logs (production default)
LOG_LEVEL=WARNING  # Show only warnings and errors
LOG_LEVEL=ERROR    # Show only errors
```

### Development vs Production

- **Development**: Use `LOG_LEVEL=DEBUG` to see detailed debug information
- **Production**: Use `LOG_LEVEL=INFO` or higher to reduce log noise
- **AWS Lambda**: Set log levels via environment variables in your SAM template

### Structured Logging

The logger automatically appends extra context as JSON when provided:

```python
logger.info("Chat created", extra={"chat_id": chat_id, "user_id": user_id})
# Output: 2024-01-15 10:30:00 - INFO - chat_route.Chat created - {"chat_id": "123", "user_id": "user456"}
```

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
| `make dev`           | Start DynamoDB in-memory and run server (ideal for frontend tests) |
| `make docker-run`    | Run the application in Docker container locally                    |
| `make build`         | Generate requirements.txt and build the SAM application            |
| `make deploy`        | Deploy the application to AWS                                      |
| `make deploy-guided` | Deploy with interactive prompts (for first deployment)             |
| `make delete`        | Delete the AWS CloudFormation stack                                |

## Project Structure

- `src/app/`: Core application code
  - `main.py`: Main FastAPI application with Lambda handler
- `dev/lab/`: Development and experimental code (excluded from production)
  - Data processing for RAG systems
  - Usage pattern analysis
  - Prompt testing and experimentation
  - Agentic system development
- `scripts/`: Utility scripts for testing and development
- `tests/`: Test suite (covers both `src/app/` and `dev/lab/`)
- `template.yaml`: AWS SAM template defining infrastructure

## Renaming the Project

To use this codebase as a template for a new project, update the project name in these 4 locations:

1. **`pyproject.toml`** (line 2): Change `name = "chatbot-backend"`
2. **`template.yaml`** (line 13): Change `Default: chatbot-backend`
3. **`Makefile`** (line 2): Change `PROJECT_NAME := chatbot-backend`
4. **`src/app/main.py`** (line 14): Change `PROJECT_NAME = "chatbot"` (for SSM parameter paths)

Note: The project name in `main.py` is used for AWS SSM parameter paths (`/chatbot/api-secret`), so it should typically be a short, lowercase name without hyphens.

## Adding Your Own Routes

To add a new endpoint, modify `src/app/main.py`:

```python
@app.get("/my-new-endpoint", response_model=YourResponseModel)
async def my_new_endpoint(request: Request) -> YourResponseModel:
    """New endpoint that returns a response."""
    logger.info("My new endpoint called", extra={"path": request.url.path})
    # Your logic here
    return YourResponseModel(...)
```

## AWS Lambda Integration

The application uses Docker containers with the [AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter) to enable streaming responses:

- **Container-based deployment**: Uses Docker images for consistent environments
- **Streaming support**: Real-time response streaming via Lambda Function URLs
- **Web framework compatibility**: Works with any web framework (FastAPI, Flask, etc.)
- **Local development**: Same container runs locally and in Lambda

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.
