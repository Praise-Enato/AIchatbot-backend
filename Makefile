.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Installing python and creating virtual environment using uv"
	@uv python install 3.12
	@uv sync
	@uv run pre-commit install
	@echo "📦 Downloading DynamoDB Local for testing"
	@./setup/download_dynamodb_local.sh

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "Running ruff linting..."
	@uv run ruff check src scripts tests --fix
	@echo "Running ruff import sorting..."
	@uv run ruff check src scripts tests --select I --fix
	@echo "Running ruff formatting..."
	@uv run ruff format src scripts tests
	@echo "Running mypy..."
	@uv run mypy
	@echo "Checking for obsolete dependencies: Running deptry"
	@uv run deptry .

.PHONY: test
test: ## Test the code with pytest (fast tests only)
	@echo "🚀 Testing code: Running fast tests"
	@uv run python -m pytest tests/fast/

.PHONY: test-all
test-all: ## Run all tests with DynamoDB Local
	@echo "🚀 Running all tests with DynamoDB Local"
	@./setup/start_dynamodb_local.sh status > /dev/null 2>&1 && (echo "❌ DynamoDB Local is already running. Please run 'make dynamodb-stop' first." && exit 1) || true
	@./setup/start_dynamodb_local.sh start --mode inmemory
	@./setup/create_tables.sh
	@DYNAMODB_URL=http://localhost:8000 uv run python -m pytest tests/ || (./setup/start_dynamodb_local.sh stop && exit 1)
	@./setup/start_dynamodb_local.sh stop

.PHONY: dynamodb-start
dynamodb-start: ## Start DynamoDB Local with persistent storage and create tables if needed
	@echo "🚀 Starting DynamoDB Local with persistent storage"
	@./setup/start_dynamodb_local.sh start --mode persistent
	@echo "🔍 Checking if tables exist..."
	@if ! ./setup/check_tables.sh >/dev/null 2>&1; then \
		echo "📋 Creating tables..."; \
		./setup/create_tables.sh; \
	else \
		echo "✅ Tables already exist"; \
	fi

.PHONY: dynamodb-start-inmemory
dynamodb-start-inmemory: ## Start DynamoDB Local in-memory
	@echo "🚀 Starting DynamoDB Local in-memory"
	@./setup/start_dynamodb_local.sh start --mode inmemory
	@./setup/create_tables.sh

.PHONY: dynamodb-stop
dynamodb-stop: ## Stop DynamoDB Local
	@echo "🛑 Stopping DynamoDB Local"
	@./setup/start_dynamodb_local.sh stop

.PHONY: dynamodb-status
dynamodb-status: ## Check DynamoDB Local status
	@./setup/start_dynamodb_local.sh status


.PHONY: dynamodb-reset
dynamodb-reset: ## Reset DynamoDB Local (delete data, restart, create tables)
	@echo "🔄 Resetting DynamoDB Local"
	@./setup/start_dynamodb_local.sh stop
	@rm -rf dynamodb-local/data/*
	@./setup/start_dynamodb_local.sh start --mode persistent
	@./setup/create_tables.sh
	@echo "✅ DynamoDB Local has been reset"

.PHONY: run
run: ## Run the FastAPI application with auto-reload
	@echo "🚀 Starting API server with auto-reload"
	@./setup/start_dynamodb_local.sh status || (echo "❌ DynamoDB Local is not running. Please run 'make dynamodb-start' first." && exit 1)
	@uv run uvicorn src.chatbot_backend.local:app --reload --host 0.0.0.0 --port 8080

.PHONY: build
build: ## Generate requirements.txt and build the SAM application
	@echo "🚀 Generating requirements.txt from pyproject.toml"
	@uv pip compile pyproject.toml -o src/requirements.txt
	@echo "🚀 Building SAM application"
	@sam build

.PHONY: deploy-guided
deploy-guided: build ## Deploy the SAM application to AWS with guided setup
	@echo "🚀 Deploying to AWS with guided setup (first time only)"
	@sam deploy --guided

.PHONY: deploy
deploy: build ## Deploy the SAM application to AWS
	@echo "🚀 Deploying to AWS"
	@sam deploy

.PHONY: logs
logs: ## Get the logs of the SAM application
	@echo "🚀 Getting logs"
	@sam logs --stack-name chatbot-backend --tail

.PHONY: delete
delete: ## Delete the CloudFormation stack
	@echo "🧹 Deleting stack"
	@sam delete --stack-name chatbot-backend --no-prompts

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
