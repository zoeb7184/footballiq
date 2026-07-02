"""Gold adapter for the team read model."""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.engine import RowMapping

from footballiq.application.read_models import TeamReadModel, TeamRecord

_COLUMNS = (
    "team_id_nat, team_name, fifa_code, group_letter, "
    "confederation, fifa_ranking, elo_rating"
)


def _record(row: RowMapping) -> TeamRecord:
    return TeamRecord(
        team_id=int(str(row["team_id_nat"])),
        name=str(row["team_name"]),
        fifa_code=str(row["fifa_code"]),
        group_letter=None if row["group_letter"] is None else str(row["group_letter"]),
        confederation=None if row["confederation"] is None else str(row["confederation"]),
        fifa_ranking=None if row["fifa_ranking"] is None else int(str(row["fifa_ranking"])),
        elo_rating=None if row["elo_rating"] is None else int(str(row["elo_rating"])),
    )


class GoldTeamReadModel(TeamReadModel):
    """Reads gold.dim_team; reserved members (sk < 0) are never returned."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._table = f"{schema}.dim_team" if schema else "dim_team"

    def list_teams(self, *, limit: int, offset: int) -> list[TeamRecord]:
        query = text(
            f"SELECT {_COLUMNS} FROM {self._table} WHERE team_sk > 0 "
            "ORDER BY team_name LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(query, {"limit": limit, "offset": offset}).mappings().all()
        return [_record(r) for r in rows]

    def count_teams(self) -> int:
        query = text(f"SELECT count(*) FROM {self._table} WHERE team_sk > 0")
        with self._engine.connect() as conn:
            return int(conn.execute(query).scalar_one())

    def get_team(self, team_id: int) -> TeamRecord | None:
        query = text(
            f"SELECT {_COLUMNS} FROM {self._table} "
            "WHERE team_sk > 0 AND team_id_nat = :tid"
        )
        with self._engine.connect() as conn:
            row = conn.execute(query, {"tid": team_id}).mappings().first()
        return None if row is None else _record(row)
