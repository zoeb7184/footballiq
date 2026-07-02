"""Readiness probe against the gold layer.

Phase M3: warehouse reachable + core gold populated. The scoring-run check
(backend design §5) activates in Module 5 when prediction tables exist.
"""

from __future__ import annotations

from sqlalchemy import Engine, text

from footballiq.application.ports import ReadinessProbe, ReadinessReport


class GoldReadinessProbe(ReadinessProbe):
    """Concrete probe; schema configurable so unit tests can run on SQLite."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._prefix = f"{schema}." if schema else ""

    def check(self) -> ReadinessReport:
        failures: list[str] = []
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                matches = conn.execute(
                    text(f"SELECT count(*) FROM {self._prefix}fact_match")
                ).scalar_one()
                if int(matches) == 0:
                    failures.append("gold.fact_match is empty (run `make pipeline`)")
        except Exception as exc:  # broad by design: readiness must never raise
            failures.append(f"warehouse unreachable: {type(exc).__name__}")
        return ReadinessReport(ready=not failures, failures=tuple(failures))
