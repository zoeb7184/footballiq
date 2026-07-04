"""Gold adapter for talent-flow graph reads (graph-design §4).

Reads the three batch-built graph tables joined to dim_team for public nation
ids/names. Read-only: metrics are computed by `make graph`, never here.
"""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.engine import RowMapping

from footballiq.application.read_models import (
    ClubFilter,
    ClubMetric,
    GraphReadModel,
    NationConcentration,
    SupplierShare,
    TalentFlowEdge,
)

# Whitelist: request sort key -> column (guards ORDER BY against injection).
_CLUB_SORT_COLUMNS = {
    "value_exported": "value_exported",
    "players_supplied": "players_supplied",
    "nations_supplied": "nations_supplied",
}


def _edge(row: RowMapping) -> TalentFlowEdge:
    return TalentFlowEdge(
        club=str(row["club"]),
        nation_id=int(str(row["team_id_nat"])),
        nation_name=str(row["team_name"]),
        player_count=int(str(row["player_count"])),
        total_value=float(str(row["total_value"])),
    )


def _club(row: RowMapping) -> ClubMetric:
    return ClubMetric(
        club=str(row["club"]),
        nations_supplied=int(str(row["nations_supplied"])),
        players_supplied=int(str(row["players_supplied"])),
        value_exported=float(str(row["value_exported"])),
    )


class GoldGraphReadModel(GraphReadModel):
    """Reads gold.graph_edge_talent_flow + graph_metrics_club/nation."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._p = f"{schema}." if schema else ""

    def list_edges(self, *, limit: int, offset: int) -> list[TalentFlowEdge]:
        query = text(
            "SELECT e.club, t.team_id_nat, t.team_name, e.player_count, e.total_value "
            f"FROM {self._p}graph_edge_talent_flow e "
            f"JOIN {self._p}dim_team t ON t.team_sk = e.team_sk "
            "ORDER BY e.total_value DESC, e.club LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(
                query, {"limit": limit, "offset": offset}
            ).mappings().all()
        return [_edge(r) for r in rows]

    def count_edges(self) -> int:
        with self._engine.connect() as conn:
            return int(conn.execute(
                text(f"SELECT count(*) FROM {self._p}graph_edge_talent_flow")
            ).scalar_one())

    def list_clubs(
        self, *, limit: int, offset: int, filters: ClubFilter
    ) -> list[ClubMetric]:
        column = _CLUB_SORT_COLUMNS[filters.sort]  # KeyError caught upstream
        direction = "DESC" if filters.descending else "ASC"
        query = text(
            "SELECT club, nations_supplied, players_supplied, value_exported "
            f"FROM {self._p}graph_metrics_club "
            f"ORDER BY {column} {direction}, club LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(
                query, {"limit": limit, "offset": offset}
            ).mappings().all()
        return [_club(r) for r in rows]

    def count_clubs(self) -> int:
        with self._engine.connect() as conn:
            return int(conn.execute(
                text(f"SELECT count(*) FROM {self._p}graph_metrics_club")
            ).scalar_one())

    def get_nation_concentration(
        self, nation_id: int, *, top: int
    ) -> NationConcentration | None:
        head = text(
            "SELECT n.team_sk, t.team_id_nat, t.team_name, n.supplier_count, "
            "n.players_total, n.total_value, n.hhi_players "
            f"FROM {self._p}graph_metrics_nation n "
            f"JOIN {self._p}dim_team t ON t.team_sk = n.team_sk "
            "WHERE t.team_id_nat = :nid"
        )
        with self._engine.connect() as conn:
            row = conn.execute(head, {"nid": nation_id}).mappings().first()
            if row is None:
                return None
            suppliers = conn.execute(
                text(
                    "SELECT club, player_count, total_value "
                    f"FROM {self._p}graph_edge_talent_flow "
                    "WHERE team_sk = :sk ORDER BY player_count DESC, total_value DESC "
                    "LIMIT :top"
                ),
                {"sk": int(str(row["team_sk"])), "top": top},
            ).mappings().all()
        players_total = int(str(row["players_total"]))
        return NationConcentration(
            nation_id=int(str(row["team_id_nat"])),
            nation_name=str(row["team_name"]),
            supplier_count=int(str(row["supplier_count"])),
            players_total=players_total,
            total_value=float(str(row["total_value"])),
            hhi_players=float(str(row["hhi_players"])),
            top_suppliers=[
                SupplierShare(
                    club=str(s["club"]),
                    player_count=int(str(s["player_count"])),
                    total_value=float(str(s["total_value"])),
                    share=int(str(s["player_count"])) / players_total
                    if players_total else 0.0,
                )
                for s in suppliers
            ],
        )
