"""Domain enumerations."""

from enum import Enum, unique


@unique
class Position(str, Enum):
    """Player position groups as they appear in the registry."""

    GOALKEEPER = "GK"
    DEFENDER = "DEF"
    MIDFIELDER = "MID"
    FORWARD = "FWD"


@unique
class MatchStatus(str, Enum):
    """Match lifecycle states (accumulating-status fact: forward-only)."""

    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
