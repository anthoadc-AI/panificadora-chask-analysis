.PHONY: help install install-dev test lint format clean notebook dashboard docs all

# Colors for help output
BLUE := \033[36m
RESET := \033[0m

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(RESET) %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pip install -e .

test:  ## Run all tests with coverage
	pytest --cov=src/panificadora --cov-report=term-missing --cov-report=html

lint:  ## Run linters (ruff + mypy)
	ruff check src tests
	mypy src

format:  ## Auto-format code with ruff
	ruff format src tests
	ruff check --fix src tests

clean:  ## Remove cache and build artifacts
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +

notebook:  ## Launch Jupyter notebook server
	jupyter notebook notebooks/

dashboard:  ## Launch Streamlit dashboard
	streamlit run dashboard/app.py

docs:  ## Build documentation locally
	mkdocs serve

figures:  ## Regenerate all report figures from notebooks
	jupyter nbconvert --to notebook --execute notebooks/*.ipynb --output-dir notebooks/

all: clean install-dev lint test  ## Full quality check pipeline
