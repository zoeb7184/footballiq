"""Gold-backed fact catalog (rag-design §2, §6).

Every numeric fact the analyst states comes from one of these executed SQL
queries against gold — never from embeddings or the LLM. Each route maps to a
small, fixed query set (the demo questions are deterministic entries). Missing
tables degrade to no facts, so the pipeline answers "cannot answer" rather than
crashing.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, text

from footballiq.application.rag.ports import Fact, Route


def _eur(x: object) -> str:
    return str(round(float(str(x))))


class GoldFactProvider:
    """FactProvider port: route -> catalog SQL -> grounded facts."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._p = f"{schema}." if schema else ""

    def facts(self, route: Route, question: str) -> list[Fact]:  # noqa: ARG002
        dispatch = {
            Route.KPI: self._kpi,
            Route.PREDICTION: self._prediction,
            Route.EXPLANATION: self._explanation,
            Route.GRAPH: self._graph,
        }
        handler = dispatch.get(route)
        if handler is None:
            return []  # DOCS -> retrieval only
        try:
            return handler()
        except Exception:  # missing table / empty warehouse: answer from docs
            return []

    def _one(self, sql: str) -> Any:
        with self._engine.connect() as conn:
            return conn.execute(text(sql)).first()

    def _kpi(self) -> list[Fact]:
        row = self._one(
            f"SELECT count(*) AS n, COALESCE(sum(market_value_eur), 0) AS v "
            f"FROM {self._p}dim_player WHERE player_sk > 0"
        )
        goals = self._one(
            f"SELECT count(*) AS g FROM {self._p}fact_match_event "
            "WHERE event_type = 'Goal'"
        )
        if row is None:
            return []
        facts = [
            Fact("Squad size (players)", str(int(row.n)), "gold.dim_player"),
            Fact("Total squad value (EUR)", _eur(row.v), "gold.dim_player"),
        ]
        if goals is not None:
            facts.append(Fact("Goals scored", str(int(goals.g)),
                              "gold.fact_match_event"))
        return facts

    def _prediction(self) -> list[Fact]:
        r = self._one(
            "SELECT dp.player_name AS name, pr.predicted_value_eur AS pred, "
            "pr.value_gap_eur AS gap, pr.model_version AS mv, pr.scored_at AS ts "
            f"FROM {self._p}prediction_player_valuation pr "
            f"JOIN {self._p}dim_player dp ON dp.player_sk = pr.player_sk "
            "WHERE dp.player_sk > 0 ORDER BY pr.value_gap_eur DESC LIMIT 1"
        )
        if r is None:
            return []
        src = "gold.prediction_player_valuation"
        return [
            Fact("Most undervalued player", str(r.name), src, "prediction"),
            Fact("Predicted value (EUR)", _eur(r.pred), src, "prediction"),
            Fact("Value gap (EUR)", _eur(r.gap), src, "prediction"),
            Fact("model_version", str(r.mv), src, "prediction"),
            Fact("scored_at", str(r.ts), src, "prediction"),
        ]

    def _explanation(self) -> list[Fact]:
        top = self._one(
            "SELECT dp.player_name AS name, pr.player_sk AS sk, "
            "pr.model_version AS mv "
            f"FROM {self._p}prediction_player_valuation pr "
            f"JOIN {self._p}dim_player dp ON dp.player_sk = pr.player_sk "
            "WHERE dp.player_sk > 0 ORDER BY pr.value_gap_eur DESC LIMIT 1"
        )
        if top is None:
            return []
        src = "gold.explanation_player_valuation"
        facts = [
            Fact("Explained player", str(top.name), src, "explanation"),
            Fact("model_version", str(top.mv), src, "explanation"),
        ]
        with self._engine.connect() as conn:
            drivers = conn.execute(
                text(
                    "SELECT feature_name AS f, multiplicative_factor AS m "
                    f"FROM {self._p}explanation_player_valuation "
                    "WHERE player_sk = :sk ORDER BY rank LIMIT 3"
                ),
                {"sk": int(top.sk)},
            ).all()
        for d in drivers:
            facts.append(Fact(
                f"Driver: {d.f}", f"x{round(float(str(d.m)), 2)}", src, "explanation"
            ))
        return facts

    def _graph(self) -> list[Fact]:
        r = self._one(
            "SELECT club, players_supplied AS n, value_exported AS v, "
            "graph_version AS gv "
            f"FROM {self._p}graph_metrics_club "
            "ORDER BY value_exported DESC LIMIT 1"
        )
        if r is None:
            return []
        src = "gold.graph_metrics_club"
        return [
            Fact("Top talent supplier", str(r.club), src, "graph"),
            Fact("Players supplied", str(int(r.n)), src, "graph"),
            Fact("Value exported (EUR)", _eur(r.v), src, "graph"),
            Fact("graph_version", str(r.gv), src, "graph"),
        ]
