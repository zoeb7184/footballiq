# FootballIQ Enterprise — developer commands (single entry point, mirrored in CI)
.PHONY: install lint format typecheck test check db-up db-down ingest transform dbt-test pipeline api features train score graph ai-up index bi-up portal demo

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

features:       ## Build ML feature tables in gold
	python -m footballiq.ml features

train:          ## Train valuation model (baselines + gate + registry)
	python -m footballiq.ml train-valuation

score:          ## Batch-score all players + SHAP explanations into gold
	python -m footballiq.ml score-valuation

graph:          ## Build club<->nation talent-flow graph metrics into gold
	python -m footballiq.graph build

ai-up:          ## Apply the ai schema + pgvector + fiq_analyst role (idempotent)
	docker compose exec -T warehouse psql -U fiq -d footballiq \
		-f /docker-entrypoint-initdb.d/02-ai-schema-and-role.sql

index:          ## Embed docs into the ai.document_chunk vector store
	python -m footballiq.infrastructure.ai index

bi-up:          ## Start Metabase (http://localhost:3000)
	docker compose up -d bi
	@echo "Metabase starting — first boot takes ~1-2 min: http://localhost:3000"

portal:         ## Run the Streamlit customer portal (API-only client)
	streamlit run portal/app.py

demo: db-up pipeline features train score graph ai-up index  ## One command: build the whole platform end-to-end + smoke-check
	python scripts/demo_smoke.py
	@echo ""
	@echo "=== FootballIQ is built end-to-end ==="
	@echo "  make api     -> http://localhost:8000/docs   (versioned read API + RAG analyst)"
	@echo "  make portal  -> http://localhost:8501         (Streamlit scouting portal)"
	@echo "  make bi-up   -> http://localhost:3000         (Metabase dashboards)"

install:        ## Install package + dev tooling
	pip install -e ".[dev]"
	pre-commit install

lint:           ## Static analysis
	ruff check src tests portal

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
