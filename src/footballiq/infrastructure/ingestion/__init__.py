"""Bronze ingestion — CSVs land verbatim with load stamping.

Rules implemented (physical architecture §1):
- append-only, immutable, all columns TEXT (no interpretation at bronze)
- every load stamped: load_id, source file, sha256, ingested_at
- idempotent: re-ingesting an unchanged file is a recorded no-op
"""
