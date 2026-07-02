"""Response DTOs — contracts as types (backend design §4)."""

from __future__ import annotations

from pydantic import BaseModel

from footballiq.application.read_models import TeamRecord


class TeamResponse(BaseModel):
    """One national team."""

    team_id: int
    name: str
    fifa_code: str
    group_letter: str | None
    confederation: str | None
    fifa_ranking: int | None
    elo_rating: int | None

    @classmethod
    def from_record(cls, record: TeamRecord) -> TeamResponse:
        return cls(
            team_id=record.team_id,
            name=record.name,
            fifa_code=record.fifa_code,
            group_letter=record.group_letter,
            confederation=record.confederation,
            fifa_ranking=record.fifa_ranking,
            elo_rating=record.elo_rating,
        )


class TeamListResponse(BaseModel):
    """Paginated team catalog."""

    items: list[TeamResponse]
    total: int
    limit: int
    offset: int
