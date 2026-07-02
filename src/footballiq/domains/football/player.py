"""Player entity — the valued asset at the heart of the platform."""

from __future__ import annotations

from datetime import date

from footballiq.domains.football.enums import Position
from footballiq.domains.football.ids import PlayerId, TeamId
from footballiq.kernel.entity import Entity
from footballiq.kernel.errors import InvariantViolation

_MIN_HEIGHT_CM = 140
_MAX_HEIGHT_CM = 230


class Player(Entity[PlayerId]):
    """Registered squad member with a market book value."""

    __slots__ = (
        "caps",
        "club",
        "date_of_birth",
        "height_cm",
        "international_goals",
        "market_value_eur",
        "name",
        "position",
        "team_id",
    )

    def __init__(  # noqa: PLR0913 - registry attributes are irreducible
        self,
        player_id: PlayerId,
        *,
        name: str,
        team_id: TeamId,
        position: Position,
        club: str,
        market_value_eur: int,
        caps: int,
        date_of_birth: date,
        height_cm: int,
        international_goals: int,
    ) -> None:
        super().__init__(player_id)
        if not name.strip():
            raise InvariantViolation("player name must be non-empty")
        if market_value_eur <= 0:
            msg = f"market value must be positive, got {market_value_eur}"
            raise InvariantViolation(msg)
        if caps < 0 or international_goals < 0:
            raise InvariantViolation("caps and international goals must be >= 0")
        if not _MIN_HEIGHT_CM <= height_cm <= _MAX_HEIGHT_CM:
            msg = f"implausible height: {height_cm} cm"
            raise InvariantViolation(msg)
        self.name = name
        self.team_id = team_id
        self.position = position
        self.club = club
        self.market_value_eur = market_value_eur
        self.caps = caps
        self.date_of_birth = date_of_birth
        self.height_cm = height_cm
        self.international_goals = international_goals

    def age_at(self, reference: date) -> int:
        """Age at a fixed reference date (ML design: age at tournament start)."""
        if reference < self.date_of_birth:
            raise InvariantViolation("reference date before date of birth")
        had_birthday = (reference.month, reference.day) >= (
            self.date_of_birth.month,
            self.date_of_birth.day,
        )
        return reference.year - self.date_of_birth.year - (0 if had_birthday else 1)
