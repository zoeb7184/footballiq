"""Read-model records and ports (backend design §2).

Records are plain application-level results; the api layer maps them to
response DTOs. Reserved dimension members (sk < 0) never appear here —
they are join semantics, not catalog entries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TeamRecord:
    """One national team from gold.dim_team (real members only)."""

    team_id: int
    name: str
    fifa_code: str
    group_letter: str | None
    confederation: str | None
    fifa_ranking: int | None
    elo_rating: int | None


@dataclass(frozen=True, slots=True)
class Page:
    """Pagination envelope for list queries."""

    total: int
    limit: int
    offset: int


class TeamReadModel(Protocol):
    """Gold-backed access to the team catalog."""

    def list_teams(self, *, limit: int, offset: int) -> list[TeamRecord]: ...

    def count_teams(self) -> int: ...

    def get_team(self, team_id: int) -> TeamRecord | None: ...


@dataclass(frozen=True, slots=True)
class MatchRecord:
    """One match from the star (fact_match + conformed dims).

    away_team is None when the away slot is a reserved member — the DTO
    layer renders that as an explicit TBD state, never a null.
    """

    match_id: int
    match_date: str  # ISO date
    kickoff_utc: str  # HH:MM
    stage_name: str
    is_knockout: bool
    venue_name: str
    home_team: TeamSide
    away_team: TeamSide | None
    status: str
    home_score: int | None
    away_score: int | None
    home_xg: float | None
    away_xg: float | None


@dataclass(frozen=True, slots=True)
class TeamSide:
    """Minimal team reference embedded in a match."""

    team_id: int
    name: str
    fifa_code: str


class MatchReadModel(Protocol):
    """Gold-backed access to the match ledger."""

    def list_matches(
        self, *, limit: int, offset: int, status: str | None
    ) -> list[MatchRecord]: ...

    def count_matches(self, *, status: str | None) -> int: ...

    def get_match(self, match_id: int) -> MatchRecord | None: ...


@dataclass(frozen=True, slots=True)
class PlayerRecord:
    """One player from gold.dim_player with national-team context."""

    player_id: int
    name: str
    position: str
    club: str
    market_value_eur: int
    caps: int
    international_goals: int
    date_of_birth: str  # ISO date; age derived by consumers at query time
    height_cm: int
    team: TeamSide


@dataclass(frozen=True, slots=True)
class PlayerFilter:
    """Optional catalog filters."""

    team_id: int | None = None
    position: str | None = None


class PlayerReadModel(Protocol):
    """Gold-backed access to the player registry."""

    def list_players(
        self, *, limit: int, offset: int, filters: PlayerFilter
    ) -> list[PlayerRecord]: ...

    def count_players(self, *, filters: PlayerFilter) -> int: ...

    def get_player(self, player_id: int) -> PlayerRecord | None: ...
