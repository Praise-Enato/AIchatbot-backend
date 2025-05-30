# Load environment variables from .env file
include .env
export

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
	@STARTED_DYNAMODB=false; \
	if ! ./setup/start_dynamodb_local.sh status > /dev/null 2>&1; then \
		echo "🚀 Starting DynamoDB Local in-memory for tests"; \
		./setup/start_dynamodb_local.sh start --mode inmemory; \
		./setup/create_tables.sh; \
		STARTED_DYNAMODB=true; \
	else \
		echo "✅ DynamoDB Local is already running"; \
	fi;
	@uv run python -m pytest tests/ || ($$STARTED_DYNAMODB && ./setup/start_dynamodb_local.sh stop; exit 1); \
	$$STARTED_DYNAMODB && ./setup/start_dynamodb_local.sh stop

.PHONY: run
run: ## Run the FastAPI application with auto-reload
	@echo "🚀 Starting API server with auto-reload"
	@./setup/start_dynamodb_local.sh status || (echo "❌ DynamoDB Local is not running. Please run 'make dynamodb-start' first." && exit 1)
	@uv run uvicorn src.chatbot_backend.app:app --reload --host 0.0.0.0 --port 8080

.PHONY: dev
dev: ## Start DynamoDB in-memory and run the server for frontend testing
	@echo "🚀 Starting development environment for frontend testing"
	@STARTED_DYNAMODB=false; \
	if ! ./setup/start_dynamodb_local.sh status > /dev/null 2>&1; then \
		echo "🚀 Starting DynamoDB Local in-memory for development"; \
		./setup/start_dynamodb_local.sh start --mode inmemory; \
		./setup/create_tables.sh; \
		STARTED_DYNAMODB=true; \
	else \
		echo "✅ DynamoDB Local is already running"; \
	fi;
	@echo "🚀 Starting API server";
	@uv run uvicorn src.chatbot_backend.app:app --reload --host 0.0.0.0 --port 8080 || ($$STARTED_DYNAMODB && ./setup/start_dynamodb_local.sh stop; exit 1); \
	$$STARTED_DYNAMODB && echo "🛑 Stopping DynamoDB Local that was started for dev" && ./setup/start_dynamodb_local.sh stop

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

.PHONY: data-down
data-down: ## Download data from S3
	@if [ -z "$(DATA_S3_BUCKET)" ]; then \
		echo "❌ DATA_S3_BUCKET environment variable not set. Add it to your .env file."; \
		exit 1; \
	fi
	@echo "🚀 Downloading data from $(DATA_S3_BUCKET)"
	@aws s3 sync $(DATA_S3_BUCKET) data --delete
	@echo "✅ Data sync complete: $$(du -sh data | cut -f1)"

.PHONY: data-up
data-up: ## Upload data to S3
	@if [ -z "$(DATA_S3_BUCKET)" ]; then \
		echo "❌ DATA_S3_BUCKET environment variable not set. Add it to your .env file."; \
		exit 1; \
	fi
	@echo "🚀 Uploading data to $(DATA_S3_BUCKET)"
	@aws s3 sync data $(DATA_S3_BUCKET)
	@echo "✅ Upload complete"

.PHONY: data-up-dry
data-up-dry: ## Preview what would be uploaded to S3
	@if [ -z "$(DATA_S3_BUCKET)" ]; then \
		echo "❌ DATA_S3_BUCKET environment variable not set. Add it to your .env file."; \
		exit 1; \
	fi
	@echo "🔍 Preview of files that would be uploaded to $(DATA_S3_BUCKET):"
	@aws s3 sync data $(DATA_S3_BUCKET) --dryrun

.PHONY: data-size
data-size: ## Check data directory size
	@if [ -d "data" ]; then \
		echo "📊 Data directory sizes:"; \
		du -sh data/* | sort -h; \
	else \
		echo "❌ No data directory found"; \
	fi

.PHONY: docker-run
docker-run: ## Run the application in Docker container locally
	@echo "🚀 Running Docker container with DynamoDB Local"
	@STARTED_DYNAMODB=false; \
	if ! ./setup/start_dynamodb_local.sh status > /dev/null 2>&1; then \
		echo "🚀 Starting DynamoDB Local in-memory for Docker testing"; \
		./setup/start_dynamodb_local.sh start --mode inmemory; \
		./setup/create_tables.sh; \
		STARTED_DYNAMODB=true; \
	else \
		echo "✅ DynamoDB Local is already running"; \
	fi;
	@echo "🚀 Building Docker image"
	@docker build -t chatbot-backend:local .
	@echo "🚀 Running Docker container"
	@if [ "$$(uname)" = "Linux" ] && [ ! -f /.dockerenv ]; then \
		echo "🐧 Detected Linux - using host network mode"; \
		docker run --rm --network host --env-file .env chatbot-backend:local || ($$STARTED_DYNAMODB && ./setup/start_dynamodb_local.sh stop; exit 1); \
	else \
		echo "🍎 Detected Mac/Windows/WSL - using host.docker.internal"; \
		docker run --rm -p 8080:8080 --env-file .env -e DYNAMODB_URL=http://host.docker.internal:8000 chatbot-backend:local || ($$STARTED_DYNAMODB && ./setup/start_dynamodb_local.sh stop; exit 1); \
	fi; \
	$$STARTED_DYNAMODB && echo "🛑 Stopping DynamoDB Local that was started for Docker testing" && ./setup/start_dynamodb_local.sh stop

.PHONY: build
build: ## Generate requirements.txt and build the SAM application
	@echo "🚀 Generating requirements.txt from pyproject.toml"
	@uv pip compile pyproject.toml -o requirements.txt
	@echo "🔐 Authenticating with AWS ECR Public Registry"
	@aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
	@echo "🚀 Building SAM application (container mode)"
	@sam build --use-container

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
	@echo "⚠️  WARNING: This will delete the CloudFormation stack 'chatbot-backend' and all its resources"
	@read -p "Are you sure you want to continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Deletion cancelled"; \
		exit 1; \
	fi
	@echo "🧹 Deleting stack"
	@sam delete --stack-name chatbot-backend --no-prompts

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
