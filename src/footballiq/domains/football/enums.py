"""Domain enumerations."""

from enum import StrEnum, unique


@unique
class Position(StrEnum):
    """Player position groups as they appear in the registry."""

    GOALKEEPER = "GK"
    DEFENDER = "DEF"
    MIDFIELDER = "MID"
    FORWARD = "FWD"


@unique
class MatchStatus(StrEnum):
    """Match lifecycle states (accumulating-status fact: forward-only)."""

    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
