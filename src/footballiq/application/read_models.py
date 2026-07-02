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
