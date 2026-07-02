"""Value objects for the football domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from footballiq.kernel.errors import InvariantViolation
from footballiq.kernel.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Score(ValueObject):
    """Final score of a completed match. Non-negative by invariant."""

    home: int
    away: int

    def __post_init__(self) -> None:
        if self.home < 0 or self.away < 0:
            msg = f"scores must be non-negative, got {self.home}-{self.away}"
            raise InvariantViolation(msg)

    @property
    def is_draw(self) -> bool:
        return self.home == self.away

    @property
    def winner(self) -> Literal["home", "away"] | None:
        if self.home > self.away:
            return "home"
        if self.away > self.home:
            return "away"
        return None


@dataclass(frozen=True, slots=True)
class XgPair(ValueObject):
    """Expected goals for both sides. POST-tagged data (leakage governance)."""

    home: float
    away: float

    def __post_init__(self) -> None:
        if self.home < 0 or self.away < 0:
            msg = f"xG must be non-negative, got {self.home}/{self.away}"
            raise InvariantViolation(msg)


@dataclass(frozen=True, slots=True)
class TbdOpponent(ValueObject):
    """Opponent not yet determined — a legal knockout bracket state.

    A typed state, not a null: consumers are forced by the type checker to
    handle it (logical model: reserved member TBD).
    """


TBD = TbdOpponent()
