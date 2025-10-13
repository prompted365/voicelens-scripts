.PHONY: install dev lint format test test-coverage clean build demo export init
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install the package in development mode
	pip install -e ".[dev,parquet,async]"

dev: install  ## Set up development environment
	pre-commit install
	@echo "✅ Development environment ready"

lint:  ## Run all linting tools
	@echo "Running black..."
	black --check src tests
	@echo "Running isort..."
	isort --check-only src tests
	@echo "Running ruff..."
	ruff check src tests
	@echo "Running mypy..."
	mypy src

format:  ## Auto-format code
	@echo "Formatting with black..."
	black src tests
	@echo "Sorting imports with isort..."
	isort src tests
	@echo "Auto-fixing with ruff..."
	ruff check --fix src tests
	@echo "✅ Code formatted"

test:  ## Run tests
	pytest

test-coverage:  ## Run tests with coverage report
	pytest --cov=voicelens_seeder --cov-report=term-missing --cov-report=html

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean  ## Build distribution packages
	python -m build

init:  ## Initialize project database
	voicelens init-db --db data/voicelens.db

demo:  ## Run happy path demo
	voicelens demo happy-path --profile happy_path_hvac

export:  ## Export sample data  
	voicelens export csv --tables conversations,perception_gaps --out exports/demo_data

# Development shortcuts
quick-test:  ## Run fast tests only
	pytest -m "not slow"

typecheck:  ## Run only type checking
	mypy src

serve-docs:  ## Serve documentation locally
	@echo "Open http://localhost:8000"
	python -m http.server 8000 --directory docs/

# CI targets
ci-lint: lint  ## CI linting (stricter)

ci-test:  ## CI testing with coverage
	pytest --cov=voicelens_seeder --cov-report=xml --cov-report=term