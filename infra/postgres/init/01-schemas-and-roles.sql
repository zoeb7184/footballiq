-- Medallion layers as schemas (physical architecture §1) and the
-- grant-enforced access rule (backend design §3): the API role can
-- only ever SELECT from gold. Runs once on first container start.

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- API role: gold-only, read-only — enforced by the engine, not convention.
CREATE ROLE fiq_api LOGIN PASSWORD 'fiq_api_local_dev';
GRANT USAGE ON SCHEMA gold TO fiq_api;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO fiq_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO fiq_api;

-- Explicitly no access to bronze/silver (no USAGE grant = invisible).
