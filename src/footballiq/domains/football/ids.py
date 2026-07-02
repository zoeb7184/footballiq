"""Typed identifiers — NewTypes prevent cross-entity ID mix-ups at type-check time."""

from typing import NewType

PlayerId = NewType("PlayerId", int)
TeamId = NewType("TeamId", int)
VenueId = NewType("VenueId", int)
StageId = NewType("StageId", int)
RefereeId = NewType("RefereeId", int)
MatchId = NewType("MatchId", int)
