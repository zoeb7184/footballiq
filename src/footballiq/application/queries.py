"""Query use cases — thin orchestration over read-model ports (CQRS Q-side)."""

from __future__ import annotations

from dataclasses import dataclass

from footballiq.application.read_models import (
    ExplanationRecord,
    MatchReadModel,
    MatchRecord,
    Page,
    PlayerFilter,
    PlayerReadModel,
    PlayerRecord,
    TeamReadModel,
    TeamRecord,
    ValuationFilter,
    ValuationReadModel,
    ValuationRecord,
)

_VALUATION_SORTS = frozenset({"value_gap", "predicted_value", "market_value"})


@dataclass(frozen=True, slots=True)
class TeamPage:
    """A page of teams with its envelope."""

    items: list[TeamRecord]
    page: Page


class TeamQueries:
    """User intents over the team catalog."""

    def __init__(self, read_model: TeamReadModel) -> None:
        self._teams = read_model

    def list_teams(self, *, limit: int, offset: int) -> TeamPage:
        items = self._teams.list_teams(limit=limit, offset=offset)
        return TeamPage(
            items=items,
            page=Page(total=self._teams.count_teams(), limit=limit, offset=offset),
        )

    def get_team(self, team_id: int) -> TeamRecord | None:
        return self._teams.get_team(team_id)


@dataclass(frozen=True, slots=True)
class MatchPage:
    """A page of matches with its envelope."""

    items: list[MatchRecord]
    page: Page


class MatchQueries:
    """User intents over the match ledger."""

    def __init__(self, read_model: MatchReadModel) -> None:
        self._matches = read_model

    def list_matches(
        self, *, limit: int, offset: int, status: str | None = None
    ) -> MatchPage:
        items = self._matches.list_matches(limit=limit, offset=offset, status=status)
        total = self._matches.count_matches(status=status)
        return MatchPage(items=items, page=Page(total=total, limit=limit, offset=offset))

    def get_match(self, match_id: int) -> MatchRecord | None:
        return self._matches.get_match(match_id)


@dataclass(frozen=True, slots=True)
class PlayerPage:
    """A page of players with its envelope."""

    items: list[PlayerRecord]
    page: Page


class PlayerQueries:
    """User intents over the player registry."""

    def __init__(self, read_model: PlayerReadModel) -> None:
        self._players = read_model

    def list_players(
        self, *, limit: int, offset: int, filters: PlayerFilter
    ) -> PlayerPage:
        items = self._players.list_players(limit=limit, offset=offset, filters=filters)
        total = self._players.count_players(filters=filters)
        return PlayerPage(items=items, page=Page(total=total, limit=limit, offset=offset))

    def get_player(self, player_id: int) -> PlayerRecord | None:
        return self._players.get_player(player_id)


class UnknownSortError(ValueError):
    """Requested a sort column the valuation shortlist doesn't support."""


@dataclass(frozen=True, slots=True)
class ValuationPage:
    """A page of valuations with its envelope."""

    items: list[ValuationRecord]
    page: Page


class ValuationQueries:
    """User intents over model valuations and their SHAP explanations."""

    def __init__(self, read_model: ValuationReadModel) -> None:
        self._valuations = read_model

    def list_valuations(
        self, *, limit: int, offset: int, sort: str, descending: bool
    ) -> ValuationPage:
        if sort not in _VALUATION_SORTS:
            msg = f"unknown sort {sort!r}; allowed: {sorted(_VALUATION_SORTS)}"
            raise UnknownSortError(msg)
        filters = ValuationFilter(sort=sort, descending=descending)
        items = self._valuations.list_valuations(
            limit=limit, offset=offset, filters=filters
        )
        total = self._valuations.count_valuations()
        return ValuationPage(
            items=items, page=Page(total=total, limit=limit, offset=offset)
        )

    def get_valuation(self, player_id: int) -> ValuationRecord | None:
        return self._valuations.get_valuation(player_id)

    def get_explanation(self, player_id: int) -> ExplanationRecord | None:
        return self._valuations.get_explanation(player_id)
