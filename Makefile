# Makefile for Discord Guild Manager

# Variables
PYTHON := python3
PIP := pip
VENV := venv
REQUIREMENTS := requirements.txt

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help install venv clean run test lint format

help: ## Show this help message
	@echo "Discord Guild Manager - Development Commands"
	@echo "============================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install -r $(REQUIREMENTS)

venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Activate with:"
	@echo "  source $(VENV)/bin/activate  (Linux/macOS)"
	@echo "  $(VENV)\Scripts\activate.bat (Windows)"

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf $(VENV)
	rm -rf *.egg-info
	rm -rf dist build
	rm -rf .pytest_cache
	rm -rf output/*
	@echo "Cleaned up generated files"

run: ## Run the main script
	$(PYTHON) main.py

test: ## Run tests (if available)
	@echo "No tests configured yet"

lint: ## Check code style
	@if command -v flake8 &> /dev/null; then \
		flake8 . --ignore=E501,W503; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

format: ## Format code with black
	@if command -v black &> /dev/null; then \
		black .; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi

freeze: ## Update requirements.txt with current packages
	$(PIP) freeze > $(REQUIREMENTS)

setup: venv install ## Complete setup (create venv and install deps)
	@echo "Setup complete! Activate virtual environment and run 'make run'"