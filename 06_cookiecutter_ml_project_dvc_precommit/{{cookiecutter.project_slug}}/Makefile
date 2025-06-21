.PHONY: help setup install clean test quality pipeline train evaluate api-dev docker-build docker-run

# Default target
.DEFAULT_GOAL := help

# Project variables
PROJECT_NAME := {{cookiecutter.project_slug}}
PYTHON_VERSION := {{cookiecutter.python_version}}
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Set up development environment
	python$(PYTHON_VERSION) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev,notebook]"
	$(PIP) install dvc[{{cookiecutter.dvc_remote_type}}]
	{% if cookiecutter.use_mlflow == 'yes' -%}
	$(PIP) install mlflow
	{% endif -%}
	{% if cookiecutter.use_wandb == 'yes' -%}
	$(PIP) install wandb
	{% endif -%}
	pre-commit install
	dvc install
	@echo "✅ Development environment ready!"

install: ## Install production dependencies
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

clean: ## Clean up generated files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .coverage htmlcov .pytest_cache
	rm -rf reports/*
	@echo "✅ Cleaned up!"

test: ## Run tests with coverage
	pytest -v --cov={{cookiecutter.project_slug}} --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest -v -m unit

test-integration: ## Run integration tests only
	pytest -v -m integration

quality: ## Run code quality checks
	black src/ tests/
	isort src/ tests/
	flake8 src/ tests/
	mypy src/
	bandit -r src/
	safety check
	@echo "✅ Code quality checks passed!"

precommit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# DVC commands
dvc-pull: ## Pull data and models from DVC remote
	dvc pull -v

dvc-push: ## Push data and models to DVC remote
	dvc push -v

dvc-status: ## Check DVC status
	dvc status

pipeline: ## Run the full ML pipeline
	dvc repro
	dvc metrics show
	@echo "✅ Pipeline completed!"

train: ## Train the model
	$(PYTHON) -m src.models.train

evaluate: ## Evaluate the model
	$(PYTHON) -m src.models.evaluate

{% if cookiecutter.include_api_service == 'yes' -%}
# API commands
api-dev: ## Run API in development mode
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

api-test: ## Test API endpoints
	pytest tests/api/ -v
{% endif -%}

# Docker commands
docker-build: ## Build Docker image
	docker build -t $(PROJECT_NAME):latest .

docker-build-dev: ## Build development Docker image
	docker build --target development -t $(PROJECT_NAME):dev .

docker-run: ## Run Docker container
	docker run -it --rm \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/models:/app/models \
		-p 8000:8000 \
		$(PROJECT_NAME):latest

docker-run-dev: ## Run development Docker container
	docker run -it --rm \
		-v $(PWD):/app \
		-p 8888:8888 \
		-p 8000:8000 \
		$(PROJECT_NAME):dev

# Documentation
docs-serve: ## Serve documentation locally
	mkdocs serve

docs-build: ## Build documentation
	mkdocs build

# Deployment commands
{% if cookiecutter.cloud_provider == 'aws' -%}
ecr-login: ## Login to AWS ECR
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

ecr-push: ecr-login docker-build ## Push image to ECR
	docker tag $(PROJECT_NAME):latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(PROJECT_NAME):latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(PROJECT_NAME):latest

deploy-aws: ## Deploy to AWS
	@echo "Deploying to AWS..."
	# Add AWS deployment commands here
{% elif cookiecutter.cloud_provider == 'gcp' -%}
gcr-push: docker-build ## Push image to GCR
	docker tag $(PROJECT_NAME):latest gcr.io/$(GCP_PROJECT_ID)/$(PROJECT_NAME):latest
	docker push gcr.io/$(GCP_PROJECT_ID)/$(PROJECT_NAME):latest

deploy-gcp: ## Deploy to GCP
	@echo "Deploying to GCP..."
	# Add GCP deployment commands here
{% elif cookiecutter.cloud_provider == 'azure' -%}
acr-push: docker-build ## Push image to ACR
	docker tag $(PROJECT_NAME):latest $(AZURE_REGISTRY_NAME).azurecr.io/$(PROJECT_NAME):latest
	docker push $(AZURE_REGISTRY_NAME).azurecr.io/$(PROJECT_NAME):latest

deploy-azure: ## Deploy to Azure
	@echo "Deploying to Azure..."
	# Add Azure deployment commands here
{% endif -%}

# Monitoring commands
{% if cookiecutter.include_model_monitoring == 'yes' -%}
monitor-drift: ## Check for data drift
	$(PYTHON) -m src.monitoring.drift_detector

monitor-performance: ## Check model performance
	$(PYTHON) -m src.monitoring.performance_monitor
{% endif -%}

# Utility commands
format: ## Format code
	black src/ tests/
	isort src/ tests/

lint: ## Lint code
	pylint src/

profile: ## Profile code performance
	$(PYTHON) -m cProfile -o profile.stats src/models/train.py
	$(PYTHON) -m pstats profile.stats

notebook: ## Start Jupyter notebook
	jupyter lab --ip=0.0.0.0 --port=8888

# Environment variables check
check-env: ## Check required environment variables
	@echo "Checking environment variables..."
	{% if cookiecutter.dvc_remote_type == 's3' -%}
	@test -n "$$AWS_ACCESS_KEY_ID" || (echo "❌ AWS_ACCESS_KEY_ID not set" && exit 1)
	@test -n "$$AWS_SECRET_ACCESS_KEY" || (echo "❌ AWS_SECRET_ACCESS_KEY not set" && exit 1)
	{% elif cookiecutter.dvc_remote_type == 'gs' -%}
	@test -n "$$GOOGLE_APPLICATION_CREDENTIALS" || (echo "❌ GOOGLE_APPLICATION_CREDENTIALS not set" && exit 1)
	{% elif cookiecutter.dvc_remote_type == 'azure' -%}
	@test -n "$$AZURE_STORAGE_CONNECTION_STRING" || (echo "❌ AZURE_STORAGE_CONNECTION_STRING not set" && exit 1)
	{% endif -%}
	@echo "✅ All required environment variables are set!"