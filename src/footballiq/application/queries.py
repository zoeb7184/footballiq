"""Query use cases — thin orchestration over read-model ports (CQRS Q-side)."""

from __future__ import annotations

from dataclasses import dataclass

from footballiq.application.read_models import (
    MatchReadModel,
    MatchRecord,
    Page,
    TeamReadModel,
    TeamRecord,
)


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
