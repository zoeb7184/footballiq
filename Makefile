# FootballIQ Enterprise — developer commands (single entry point, mirrored in CI)
.PHONY: install lint format typecheck test check

install:        ## Install package + dev tooling
	pip install -e ".[dev]"
	pre-commit install

lint:           ## Static analysis
	ruff check src tests

format:         ## Auto-format
	ruff format src tests
	ruff check --fix src tests

typecheck:      ## Strict type checking
	mypy

test:           ## Run test suite with coverage
	pytest

check: lint typecheck test  ## Full quality gate (what CI runs)
