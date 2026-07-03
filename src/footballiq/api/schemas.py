"""Response DTOs — contracts as types (backend design §4).

The match union is the signature contract: a ScheduledMatch structurally
has no score fields (not nullable scores), and an undetermined opponent is
an explicit typed state — never a null the client must interpret.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from footballiq.application.read_models import (
    ExplanationRecord,
    MatchRecord,
    PlayerRecord,
    TeamRecord,
    ValuationRecord,
)


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


class PlayerResponse(BaseModel):
    """One registered player with national-team context.

    market_value_eur is the source snapshot (the valuation label); model
    valuations arrive as separate prediction endpoints in Module 5.
    """

    player_id: int
    name: str
    position: str
    club: str
    market_value_eur: int
    caps: int
    international_goals: int
    date_of_birth: str
    height_cm: int
    team: TeamRef

    @classmethod
    def from_record(cls, rec: PlayerRecord) -> PlayerResponse:
        return cls(
            player_id=rec.player_id,
            name=rec.name,
            position=rec.position,
            club=rec.club,
            market_value_eur=rec.market_value_eur,
            caps=rec.caps,
            international_goals=rec.international_goals,
            date_of_birth=rec.date_of_birth,
            height_cm=rec.height_cm,
            team=TeamRef(
                team_id=rec.team.team_id, name=rec.team.name, fifa_code=rec.team.fifa_code
            ),
        )


class PlayerListResponse(BaseModel):
    """Paginated player registry (default order: market value, descending)."""

    items: list[PlayerResponse]
    total: int
    limit: int
    offset: int


class MatchListResponse(BaseModel):
    """Paginated match ledger."""

    items: list[MatchOut]
    total: int
    limit: int
    offset: int


class ShapContributionOut(BaseModel):
    """One feature's attribution. shap_log is canonical; multiplicative_factor
    (= exp(shap_log)) is the display form. Attributional, never causal."""

    feature_name: str
    feature_value: float
    shap_log: float
    multiplicative_factor: float
    rank: int


class _Provenance(BaseModel):
    """Every valuation response carries what produced it (XAI design §6)."""

    model_version: str
    feature_version: str
    scored_at: str


class ValuationResponse(_Provenance):
    """A player's model valuation with its headline (top-k) attribution.

    accuracy_note is displayed beside every valuation (trust rule): the model's
    honest ±20% band from evaluation. SHAP explains the model, not the market.
    """

    player_id: int
    name: str
    position: str
    market_value_eur: int
    predicted_value_eur: float
    value_gap_eur: float
    top_k: list[ShapContributionOut]
    accuracy_note: str = (
        "Predictions are indicative: ~20% fall within +/-20% of market on "
        "evaluation. SHAP explains the model, not the market."
    )

    @classmethod
    def from_record(cls, rec: ValuationRecord) -> ValuationResponse:
        return cls(
            player_id=rec.player_id,
            name=rec.name,
            position=rec.position,
            market_value_eur=rec.market_value_eur,
            predicted_value_eur=rec.predicted_value_eur,
            value_gap_eur=rec.value_gap_eur,
            model_version=rec.model_version,
            feature_version=rec.feature_version,
            scored_at=rec.scored_at,
            top_k=[
                ShapContributionOut(
                    feature_name=c.feature_name,
                    feature_value=c.feature_value,
                    shap_log=c.shap_log,
                    multiplicative_factor=c.multiplicative_factor,
                    rank=c.rank,
                )
                for c in rec.top_k
            ],
        )


class ValuationListResponse(BaseModel):
    """Paginated valuation shortlist (scout story 1; default sort value_gap)."""

    items: list[ValuationResponse]
    total: int
    limit: int
    offset: int
    sort: str
    order: str


class ExplanationResponse(_Provenance):
    """Full SHAP breakdown for one player.

    baseline_log + sum(contributions.shap_log) reconstructs log1p(predicted)
    — the additivity invariant guaranteed at scoring time (XAI design §4).
    """

    player_id: int
    name: str
    position: str
    market_value_eur: int
    predicted_value_eur: float
    value_gap_eur: float
    baseline_log: float
    contributions: list[ShapContributionOut]

    @classmethod
    def from_record(cls, rec: ExplanationRecord) -> ExplanationResponse:
        return cls(
            player_id=rec.player_id,
            name=rec.name,
            position=rec.position,
            market_value_eur=rec.market_value_eur,
            predicted_value_eur=rec.predicted_value_eur,
            value_gap_eur=rec.value_gap_eur,
            baseline_log=rec.baseline_log,
            model_version=rec.model_version,
            feature_version=rec.feature_version,
            scored_at=rec.scored_at,
            contributions=[
                ShapContributionOut(
                    feature_name=c.feature_name,
                    feature_value=c.feature_value,
                    shap_log=c.shap_log,
                    multiplicative_factor=c.multiplicative_factor,
                    rank=c.rank,
                )
                for c in rec.contributions
            ],
        )


def match_out_from_record(rec: MatchRecord) -> ScheduledMatch | CompletedMatch:
    """Map a read-model record onto the discriminated contract."""
    home = TeamRef(
        team_id=rec.home_team.team_id,
        name=rec.home_team.name,
        fifa_code=rec.home_team.fifa_code,
    )
    if rec.status == "Completed":
        if (
            rec.away_team is None
            or rec.home_score is None or rec.away_score is None
            or rec.home_xg is None or rec.away_xg is None
        ):
            msg = f"contract violation: completed match {rec.match_id} incomplete in gold"
            raise ValueError(msg)  # surfaces as 500 — loud, never silent
        return CompletedMatch(
            match_id=rec.match_id,
            date=rec.match_date,
            kickoff_utc=rec.kickoff_utc,
            stage=rec.stage_name,
            is_knockout=rec.is_knockout,
            venue=rec.venue_name,
            home=home,
            away=TeamRef(
                team_id=rec.away_team.team_id,
                name=rec.away_team.name,
                fifa_code=rec.away_team.fifa_code,
            ),
            score=ScoreOut(home=rec.home_score, away=rec.away_score),
            xg=XgOut(home=rec.home_xg, away=rec.away_xg),
        )
    away: TeamRef | TbdOpponentRef = TbdOpponentRef()
    if rec.away_team is not None:
        away = TeamRef(
            team_id=rec.away_team.team_id,
            name=rec.away_team.name,
            fifa_code=rec.away_team.fifa_code,
        )
    return ScheduledMatch(
        match_id=rec.match_id,
        date=rec.match_date,
        kickoff_utc=rec.kickoff_utc,
        stage=rec.stage_name,
        is_knockout=rec.is_knockout,
        venue=rec.venue_name,
        home=home,
        away=away,
    )
