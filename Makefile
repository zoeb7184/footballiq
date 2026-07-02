# FootballIQ Enterprise — developer commands (single entry point, mirrored in CI)
.PHONY: install lint format typecheck test check db-up db-down ingest transform dbt-test pipeline

transform:      ## Build silver/gold models (dbt)
	cd transform && dbt run --profiles-dir .

dbt-test:       ## Run dbt data contracts
	cd transform && dbt test --profiles-dir .

pipeline: ingest transform dbt-test  ## Full data pipeline: bronze -> silver -> contracts

db-up:          ## Start the warehouse (Postgres via docker compose)
	docker compose up -d warehouse
	@until docker compose exec warehouse pg_isready -U fiq -d footballiq -q; do sleep 1; done
	@echo "warehouse ready"

db-down:        ## Stop the warehouse (data volume preserved)
	docker compose down

ingest:         ## Load data/raw CSVs into the bronze layer
	python -m footballiq.infrastructure.ingestion

api:            ## Run the API locally (http://localhost:8000/docs)
	uvicorn footballiq.api.main:create_app --factory --reload

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

lint-imports:   ## Enforce ADR-0002 layer rules
	lint-imports

check: lint typecheck lint-imports test  ## Full quality gate (what CI runs)
