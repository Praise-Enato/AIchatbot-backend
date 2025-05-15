.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Installing python and creating virtual environment using uv"
	@uv python install 3.12
	@uv sync
	@uv run pre-commit install

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
test: ## Test the code with pytest (skips slow tests)
	@echo "🚀 Testing code: Running pytest (excluding slow tests)"
	@uv run python -m pytest -m "not slow"

.PHONY: test-all
test-all: ## Run all tests including slow tests
	@echo "🚀 Running all tests including slow tests"
	@uv run python -m pytest

.PHONY: run
run: ## Run the FastAPI application with auto-reload
	@echo "🚀 Starting API server with auto-reload"
	@uv run uvicorn src.chatbot_backend.app:app --reload --host 0.0.0.0 --port 8000

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
