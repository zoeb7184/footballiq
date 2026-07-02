"""Entity invariant tests: Player, Team, Venue."""

from datetime import date

import pytest

from footballiq.domains.football.enums import Position
from footballiq.domains.football.ids import PlayerId, RefereeId, StageId, TeamId, VenueId
from footballiq.domains.football.player import Player
from footballiq.domains.football.team import Referee, Stage, Team, Venue
from footballiq.domains.football.values import Score, XgPair
from footballiq.kernel.errors import InvariantViolation


def _player(**overrides: object) -> Player:
    kwargs: dict[str, object] = {
        "name": "José Raúl Rangel",
        "team_id": TeamId(1),
        "position": Position.GOALKEEPER,
        "club": "CD Guadalajara",
        "market_value_eur": 6_500_000,
        "caps": 15,
        "date_of_birth": date(2000, 2, 25),
        "height_cm": 190,
        "international_goals": 0,
    }
    kwargs.update(overrides)
    return Player(PlayerId(1), **kwargs)  # type: ignore[arg-type]


def test_valid_player() -> None:
    p = _player()
    assert p.market_value_eur == 6_500_000


def test_player_value_must_be_positive() -> None:
    with pytest.raises(InvariantViolation, match="market value"):
        _player(market_value_eur=0)


def test_player_height_plausibility() -> None:
    with pytest.raises(InvariantViolation, match="height"):
        _player(height_cm=250)


def test_age_at_fixed_reference_date() -> None:
    p = _player()
    assert p.age_at(date(2026, 6, 11)) == 26
    assert p.age_at(date(2026, 2, 24)) == 25  # day before birthday
    assert p.age_at(date(2026, 2, 25)) == 26  # on birthday


def test_team_fifa_code_validation() -> None:
    with pytest.raises(InvariantViolation, match="FIFA code"):
        Team(
            TeamId(1),
            name="Mexico",
            fifa_code="MEXI",
            confederation="CONCACAF",
            fifa_ranking=14,
            elo_rating=1810,
        )


def test_venue_geo_and_capacity_invariants() -> None:
    with pytest.raises(InvariantViolation, match="capacity"):
        Venue(
            VenueId(1),
            name="X",
            city="Y",
            country="MEX",
            capacity=0,
            latitude=19.3,
            longitude=-99.15,
            elevation_m=2200,
        )
    with pytest.raises(InvariantViolation, match="latitude"):
        Venue(
            VenueId(1),
            name="X",
            city="Y",
            country="MEX",
            capacity=80_000,
            latitude=95.0,
            longitude=-99.15,
            elevation_m=2200,
        )


def test_master_data_happy_paths() -> None:
    team = Team(
        TeamId(1),
        name="Mexico",
        fifa_code="mex",
        confederation="CONCACAF",
        fifa_ranking=14,
        elo_rating=1810,
    )
    assert team.fifa_code == "MEX"  # normalized to upper
    venue = Venue(
        VenueId(1),
        name="Estadio Azteca",
        city="Mexico City",
        country="MEX",
        capacity=80_824,
        latitude=19.3031,
        longitude=-99.1506,
        elevation_m=2200,
    )
    assert venue.elevation_m == 2200
    stage = Stage(StageId(1), name="Group Stage", is_knockout=False)
    assert not stage.is_knockout
    referee = Referee(
        RefereeId(1), name="Szymon Marciniak", country="Poland", avg_cards_per_game=4.2
    )
    assert referee.avg_cards_per_game == 4.2


def test_stage_and_referee_invariants() -> None:
    with pytest.raises(InvariantViolation, match="stage name"):
        Stage(StageId(1), name="  ", is_knockout=True)
    with pytest.raises(InvariantViolation, match="card rate"):
        Referee(RefereeId(1), name="X", country="Y", avg_cards_per_game=-0.1)


def test_score_away_winner_and_xg_invariant() -> None:
    assert Score(0, 2).winner == "away"
    with pytest.raises(InvariantViolation, match="xG"):
        XgPair(-0.1, 1.0)


def test_player_reference_before_birth_rejected() -> None:
    with pytest.raises(InvariantViolation, match="before date of birth"):
        _player().age_at(date(1999, 1, 1))
