"""Gold adapter for the player read model."""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.engine import RowMapping

from footballiq.application.read_models import (
    PlayerFilter,
    PlayerReadModel,
    PlayerRecord,
    TeamSide,
)

_SELECT = """
SELECT
    p.player_id_nat, p.player_name, p.position, p.club_team,
    p.market_value_eur, p.caps, p.international_goals,
    p.date_of_birth, p.height_cm,
    t.team_id_nat, t.team_name, t.fifa_code
FROM {p}dim_player p
JOIN {p}dim_team t ON p.team_sk = t.team_sk
WHERE p.player_sk > 0
"""
# Scout-first ordering: most valuable players open the catalog.
_ORDER = " ORDER BY p.market_value_eur DESC, p.player_name"


def _record(row: RowMapping) -> PlayerRecord:
    return PlayerRecord(
        player_id=int(str(row["player_id_nat"])),
        name=str(row["player_name"]),
        position=str(row["position"]),
        club=str(row["club_team"]),
        market_value_eur=int(str(row["market_value_eur"])),
        caps=int(str(row["caps"])),
        international_goals=int(str(row["international_goals"])),
        date_of_birth=str(row["date_of_birth"]),
        height_cm=int(str(row["height_cm"])),
        team=TeamSide(
            team_id=int(str(row["team_id_nat"])),
            name=str(row["team_name"]),
            fifa_code=str(row["fifa_code"]),
        ),
    )


def _filters_sql(filters: PlayerFilter) -> tuple[str, dict[str, object]]:
    clauses = ""
    params: dict[str, object] = {}
    if filters.team_id is not None:
        clauses += " AND t.team_id_nat = :team_id"
        params["team_id"] = filters.team_id
    if filters.position is not None:
        clauses += " AND p.position = :position"
        params["position"] = filters.position
    return clauses, params


class GoldPlayerReadModel(PlayerReadModel):
    """Reads gold.dim_player (reserved member excluded), team joined."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._p = f"{schema}." if schema else ""

    def list_players(
        self, *, limit: int, offset: int, filters: PlayerFilter
    ) -> list[PlayerRecord]:
        clauses, params = _filters_sql(filters)
        query = text(
            _SELECT.format(p=self._p) + clauses + _ORDER + " LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(
                query, {**params, "limit": limit, "offset": offset}
            ).mappings().all()
        return [_record(r) for r in rows]

    def count_players(self, *, filters: PlayerFilter) -> int:
        clauses, params = _filters_sql(filters)
        query = text(
            f"SELECT count(*) FROM {self._p}dim_player p "
            f"JOIN {self._p}dim_team t ON p.team_sk = t.team_sk "
            "WHERE p.player_sk > 0" + clauses
        )
        with self._engine.connect() as conn:
            return int(conn.execute(query, params).scalar_one())

    def get_player(self, player_id: int) -> PlayerRecord | None:
        query = text(_SELECT.format(p=self._p) + " AND p.player_id_nat = :pid")
        with self._engine.connect() as conn:
            row = conn.execute(query, {"pid": player_id}).mappings().first()
        return None if row is None else _record(row)
