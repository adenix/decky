.PHONY: help install dev-install test lint format clean build run

help:
	@echo "Decky Development Commands"
	@echo "=========================="
	@echo "install        - Install package in production mode"
	@echo "dev-install    - Install package in development mode with all dev dependencies"
	@echo "test           - Run test suite"
	@echo "test-cov       - Run tests with coverage report"
	@echo "lint           - Run all linters (black, flake8, mypy, isort)"
	@echo "format         - Format code with black and isort"
	@echo "security       - Run security checks (bandit, safety)"
	@echo "pre-commit     - Run all pre-commit hooks"
	@echo "clean          - Remove build artifacts and cache files"
	@echo "build          - Build distribution packages"
	@echo "run            - Run decky with example config"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/decky --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running black check..."
	black --check src/ tests/
	@echo "Running isort check..."
	isort --check-only src/ tests/
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/decky --ignore-missing-imports

format:
	@echo "Formatting with black..."
	black src/ tests/
	@echo "Sorting imports with isort..."
	isort src/ tests/

security:
	@echo "Running bandit security scanner..."
	bandit -r src/ -c pyproject.toml
	@echo "Checking dependencies for vulnerabilities..."
	safety check

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf .pytest_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete

build: clean
	python -m build

run:
	python -m decky.main configs/example.yaml

# Quick development workflow
quick-check: format lint test
	@echo "✅ All checks passed!"

# CI simulation - run all checks that CI will run
ci-local: format lint security test-cov
	@echo "✅ Local CI checks complete!"
