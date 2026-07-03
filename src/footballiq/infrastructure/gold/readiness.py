"""Readiness probe against the gold layer.

The platform reports itself fit only when it can actually serve: warehouse
reachable, core gold populated, AND a scoring run present (backend design §5 /
ML design §9). An empty prediction table means the valuation endpoints would
return nothing but 404s — that is not-ready, not merely running.
"""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

from footballiq.application.ports import ReadinessProbe, ReadinessReport

# Each check: (gold table, human remedy). Missing table counts as empty.
_REQUIRED = (
    ("fact_match", "gold.fact_match is empty (run `make pipeline`)"),
    ("prediction_player_valuation",
     "gold.prediction_player_valuation is empty (run `make score`)"),
)


class GoldReadinessProbe(ReadinessProbe):
    """Concrete probe; schema configurable so unit tests can run on SQLite."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._prefix = f"{schema}." if schema else ""

    def check(self) -> ReadinessReport:
        failures: list[str] = []
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # warehouse reachable
                for table, remedy in _REQUIRED:
                    if self._is_empty(conn, table):
                        failures.append(remedy)
        except Exception as exc:  # broad by design: readiness must never raise
            failures.append(f"warehouse unreachable: {type(exc).__name__}")
        return ReadinessReport(ready=not failures, failures=tuple(failures))

    def _is_empty(self, conn: Connection, table: str) -> bool:
        """True if the table is missing or has no rows (either blocks serving)."""
        try:
            count = conn.execute(
                text(f"SELECT count(*) FROM {self._prefix}{table}")
            ).scalar_one()
        except Exception:  # table absent → treat as empty, not as a crash
            return True
        return int(count) == 0
