"""Response DTOs — contracts as types (backend design §4).

The match union is the signature contract: a ScheduledMatch structurally
has no score fields (not nullable scores), and an undetermined opponent is
an explicit typed state — never a null the client must interpret.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from footballiq.application.read_models import MatchRecord, TeamRecord


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


class TeamRef(BaseModel):
    """Minimal team reference inside a match."""

    kind: Literal["team"] = "team"
    team_id: int
    name: str
    fifa_code: str


class TbdOpponentRef(BaseModel):
    """Knockout slot not yet decided — a state, not a null (data contract §4)."""

    kind: Literal["to_be_determined"] = "to_be_determined"


class ScoreOut(BaseModel):
    home: int
    away: int


class XgOut(BaseModel):
    home: float
    away: float


class _MatchBase(BaseModel):
    match_id: int
    date: str
    kickoff_utc: str
    stage: str
    is_knockout: bool
    venue: str
    home: TeamRef


class ScheduledMatch(_MatchBase):
    """A fixture. Structurally scoreless: there is nothing to lie with."""

    status: Literal["Scheduled"] = "Scheduled"
    away: Annotated[TeamRef | TbdOpponentRef, Field(discriminator="kind")]


class CompletedMatch(_MatchBase):
    """A result. Score and xG are required, never nullable (contract §5)."""

    status: Literal["Completed"] = "Completed"
    away: TeamRef
    score: ScoreOut
    xg: XgOut


MatchOut = Annotated[ScheduledMatch | CompletedMatch, Field(discriminator="status")]


class MatchListResponse(BaseModel):
    """Paginated match ledger."""

    items: list[MatchOut]
    total: int
    limit: int
    offset: int


def match_out_from_record(rec: MatchRecord) -> ScheduledMatch | CompletedMatch:
    """Map a read-model record onto the discriminated contract."""
    home = TeamRef(team_id=rec.home_team.team_id, name=rec.home_team.name,
                   fifa_code=rec.home_team.fifa_code)
    base = {
        "match_id": rec.match_id,
        "date": rec.match_date,
        "kickoff_utc": rec.kickoff_utc,
        "stage": rec.stage_name,
        "is_knockout": rec.is_knockout,
        "venue": rec.venue_name,
        "home": home,
    }
    if rec.status == "Completed":
        if (
            rec.away_team is None
            or rec.home_score is None or rec.away_score is None
            or rec.home_xg is None or rec.away_xg is None
        ):
            msg = f"contract violation: completed match {rec.match_id} incomplete in gold"
            raise ValueError(msg)  # surfaces as 500 — loud, never silent
        return CompletedMatch(
            **base,
            away=TeamRef(team_id=rec.away_team.team_id, name=rec.away_team.name,
                         fifa_code=rec.away_team.fifa_code),
            score=ScoreOut(home=rec.home_score, away=rec.away_score),
            xg=XgOut(home=rec.home_xg, away=rec.away_xg),
        )
    away: TeamRef | TbdOpponentRef = TbdOpponentRef()
    if rec.away_team is not None:
        away = TeamRef(team_id=rec.away_team.team_id, name=rec.away_team.name,
                       fifa_code=rec.away_team.fifa_code)
    return ScheduledMatch(**base, away=away)
