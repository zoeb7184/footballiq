"""Gold adapter for the observed scoring rate (simulation design §2)."""

from __future__ import annotations

from sqlalchemy import Engine, text

from footballiq.application.read_models import ScoringRate, ScoringRateReadModel


class GoldScoringRateReadModel(ScoringRateReadModel):
    """Reads gold.fact_match: mean total goals over completed matches only."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._table = f"{schema}.fact_match" if schema else "fact_match"

    def observed_scoring_rate(self) -> ScoringRate | None:
        query = text(
            "SELECT avg(home_score + away_score) AS avg_goals, count(*) AS n "
            f"FROM {self._table} "
            "WHERE home_score IS NOT NULL AND away_score IS NOT NULL"
        )
        with self._engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        if row is None or row["n"] is None or int(str(row["n"])) == 0:
            return None
        return ScoringRate(
            avg_total_goals=float(str(row["avg_goals"])),
            matches_observed=int(str(row["n"])),
        )
