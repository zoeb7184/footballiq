"""Match lifecycle tests — the domain rules from the logical data model."""

from datetime import UTC, datetime

import pytest

from footballiq.domains.football.enums import MatchStatus
from footballiq.domains.football.ids import MatchId, RefereeId, StageId, TeamId, VenueId
from footballiq.domains.football.match import Match
from footballiq.domains.football.values import TBD, Score, XgPair
from footballiq.kernel.errors import InvariantViolation

_KICKOFF = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)
_DEFAULT_AWAY = TeamId(2)


def _fixture(*, away: TeamId | None = _DEFAULT_AWAY, knockout: bool = False) -> Match:
    return Match(
        MatchId(1),
        home=TeamId(1),
        away=TBD if away is None else away,
        stage_id=StageId(2 if knockout else 1),
        is_knockout=knockout,
        venue_id=VenueId(1),
        referee_id=RefereeId(1),
        kickoff_utc=_KICKOFF,
    )


def test_scheduled_match_has_structural_nulls() -> None:
    m = _fixture()
    assert m.status is MatchStatus.SCHEDULED
    assert m.score is None
    assert m.xg is None


def test_complete_happy_path() -> None:
    m = _fixture()
    m.complete(Score(2, 0), XgPair(1.84, 0.52))
    assert m.is_completed
    assert m.score == Score(2, 0)
    assert m.score.winner == "home"


def test_lifecycle_is_forward_only() -> None:
    m = _fixture()
    m.complete(Score(1, 1), XgPair(1.0, 1.0))
    with pytest.raises(InvariantViolation, match="already completed"):
        m.complete(Score(2, 0), XgPair(1.0, 1.0))


def test_knockout_match_cannot_end_in_draw() -> None:
    m = _fixture(knockout=True)
    with pytest.raises(InvariantViolation, match="draw"):
        m.complete(Score(1, 1), XgPair(1.0, 1.0))


def test_group_stage_draw_is_legal() -> None:
    m = _fixture()
    m.complete(Score(1, 1), XgPair(1.0, 1.0))
    assert m.score is not None and m.score.is_draw


def test_tbd_opponent_only_in_knockout() -> None:
    with pytest.raises(InvariantViolation, match="knockout"):
        _fixture(away=None, knockout=False)


def test_cannot_complete_against_tbd_then_resolve_and_complete() -> None:
    m = _fixture(away=None, knockout=True)
    assert not m.opponent_determined
    with pytest.raises(InvariantViolation, match="TBD"):
        m.complete(Score(1, 0), XgPair(1.0, 0.5))
    m.resolve_opponent(TeamId(7))
    m.complete(Score(1, 0), XgPair(1.0, 0.5))
    assert m.is_completed


def test_resolve_rejects_self_play_and_double_resolution() -> None:
    m = _fixture(away=None, knockout=True)
    with pytest.raises(InvariantViolation, match="itself"):
        m.resolve_opponent(TeamId(1))
    m.resolve_opponent(TeamId(9))
    with pytest.raises(InvariantViolation, match="already determined"):
        m.resolve_opponent(TeamId(10))


def test_team_cannot_play_itself() -> None:
    with pytest.raises(InvariantViolation, match="itself"):
        _fixture(away=TeamId(1))


def test_negative_score_rejected() -> None:
    with pytest.raises(InvariantViolation, match="non-negative"):
        Score(-1, 0)
