-- Module 7 (RAG) store: an `ai` schema with pgvector, plus the analyst DB role.
-- Idempotent: runs on first container start (init dir) AND can be re-applied to
-- an existing volume via `make ai-up`. The assistant is the platform's first
-- internal customer; fiq_analyst can SELECT gold + ai only (rag-design §8).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS ai;

-- Analyst role: read-only over gold (facts) and ai (retrieval), nothing below.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fiq_analyst') THEN
        CREATE ROLE fiq_analyst LOGIN PASSWORD 'fiq_analyst_local_dev';
    END IF;
END
$$;

-- Audit log (rag-design §8): every analyst answer is reconstructible. Written
-- by the app (owner) role; created here so it exists before grants apply.
CREATE TABLE IF NOT EXISTS ai.query_log (
    log_id         BIGSERIAL PRIMARY KEY,
    question       TEXT NOT NULL,
    route          TEXT NOT NULL,
    grounded       BOOLEAN NOT NULL,
    fact_count     INTEGER NOT NULL,
    citation_count INTEGER NOT NULL,
    response_hash  TEXT NOT NULL,
    versions       JSONB NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT USAGE ON SCHEMA gold TO fiq_analyst;
GRANT USAGE ON SCHEMA ai   TO fiq_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO fiq_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA ai   TO fiq_analyst;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO fiq_analyst;
ALTER DEFAULT PRIVILEGES IN SCHEMA ai   GRANT SELECT ON TABLES TO fiq_analyst;

-- No USAGE on bronze/silver: everything below gold stays invisible.
