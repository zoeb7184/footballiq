"""Gold adapter for the match read model — the star schema used as designed."""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.engine import RowMapping

from footballiq.application.read_models import MatchReadModel, MatchRecord, TeamSide

_SELECT = """
SELECT
    f.match_id,
    d.calendar_date          AS match_date,
    f.kickoff_utc,
    s.stage_name,
    s.is_knockout,
    v.stadium_name           AS venue_name,
    ht.team_id_nat           AS home_id,
    ht.team_name             AS home_name,
    ht.fifa_code             AS home_code,
    f.away_team_sk,
    aw.team_id_nat           AS away_id,
    aw.team_name             AS away_name,
    aw.fifa_code             AS away_code,
    f.status,
    f.home_score, f.away_score, f.home_xg, f.away_xg
FROM {p}fact_match f
JOIN {p}dim_stage s ON f.stage_sk = s.stage_sk
JOIN {p}dim_venue v ON f.venue_sk = v.venue_sk
JOIN {p}dim_team ht ON f.home_team_sk = ht.team_sk
JOIN {p}dim_team aw ON f.away_team_sk = aw.team_sk
JOIN {p}dim_date d ON f.date_key = d.date_key
"""
_ORDER = " ORDER BY d.calendar_date, f.kickoff_utc, f.match_id"


def _opt_float(value: object) -> float | None:
    return None if value is None else float(str(value))


def _opt_int(value: object) -> int | None:
    return None if value is None else int(str(value))


def _record(row: RowMapping) -> MatchRecord:
    away_sk = int(str(row["away_team_sk"]))
    away: TeamSide | None = None
    if away_sk > 0:
        away = TeamSide(
            team_id=int(str(row["away_id"])),
            name=str(row["away_name"]),
            fifa_code=str(row["away_code"]),
        )
    return MatchRecord(
        match_id=int(str(row["match_id"])),
        match_date=str(row["match_date"]),
        kickoff_utc=str(row["kickoff_utc"])[:5],
        stage_name=str(row["stage_name"]),
        is_knockout=bool(row["is_knockout"]),
        venue_name=str(row["venue_name"]),
        home_team=TeamSide(
            team_id=int(str(row["home_id"])),
            name=str(row["home_name"]),
            fifa_code=str(row["home_code"]),
        ),
        away_team=away,
        status=str(row["status"]),
        home_score=_opt_int(row["home_score"]),
        away_score=_opt_int(row["away_score"]),
        home_xg=_opt_float(row["home_xg"]),
        away_xg=_opt_float(row["away_xg"]),
    )


class GoldMatchReadModel(MatchReadModel):
    """Reads the match star; reserved away members surface as away_team=None."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._p = f"{schema}." if schema else ""

    def list_matches(
        self, *, limit: int, offset: int, status: str | None
    ) -> list[MatchRecord]:
        where = " WHERE f.status = :status" if status else ""
        query = text(
            _SELECT.format(p=self._p) + where + _ORDER + " LIMIT :limit OFFSET :offset"
        )
        params: dict[str, object] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        with self._engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
        return [_record(r) for r in rows]

    def count_matches(self, *, status: str | None) -> int:
        where = " WHERE status = :status" if status else ""
        query = text(f"SELECT count(*) FROM {self._p}fact_match{where}")
        with self._engine.connect() as conn:
            result = conn.execute(query, {"status": status} if status else {})
            return int(result.scalar_one())

    def get_match(self, match_id: int) -> MatchRecord | None:
        query = text(_SELECT.format(p=self._p) + " WHERE f.match_id = :mid")
        with self._engine.connect() as conn:
            row = conn.execute(query, {"mid": match_id}).mappings().first()
        return None if row is None else _record(row)
