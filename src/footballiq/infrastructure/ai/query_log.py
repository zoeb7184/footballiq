"""Append-only analyst audit log (rag-design §8): ai.query_log.

Every answer is recorded so it can be reconstructed: question, route,
groundedness, evidence counts, response hash, and pinned versions. Written by
the app (owner) role; the table is provisioned by the init SQL / `make ai-up`.
"""

from __future__ import annotations

import json

from sqlalchemy import Engine, text

from footballiq.application.rag.ports import QueryLogRecord


class PgQueryLog:
    """QueryLog port over ai.query_log (Postgres, JSONB versions)."""

    def __init__(self, engine: Engine, *, schema: str = "ai") -> None:
        self._engine = engine
        self._schema = schema

    def record(self, entry: QueryLogRecord) -> None:
        stmt = text(
            f"INSERT INTO {self._schema}.query_log "
            "(question, route, grounded, fact_count, citation_count, "
            "response_hash, versions) VALUES "
            "(:q, :r, :g, :fc, :cc, :h, CAST(:v AS JSONB))"
        )
        with self._engine.begin() as conn:
            conn.execute(stmt, {
                "q": entry.question,
                "r": entry.route,
                "g": entry.grounded,
                "fc": entry.fact_count,
                "cc": entry.citation_count,
                "h": entry.response_hash,
                "v": json.dumps(entry.versions),
            })
