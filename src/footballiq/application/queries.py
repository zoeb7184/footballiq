"""Query use cases — thin orchestration over read-model ports (CQRS Q-side)."""

from __future__ import annotations

from dataclasses import dataclass

from footballiq.application.read_models import Page, TeamReadModel, TeamRecord


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
