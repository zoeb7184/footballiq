"""Match aggregate — accumulating-status lifecycle with typed TBD opponent.

Implements the logical data model's rules in the type system:
- Scheduled → Completed is the only permitted transition (forward-only).
- A Scheduled match has no score/xG (structural, not missing).
- A knockout match cannot complete as a draw (stage-conditional outcomes).
- An undetermined opponent is `TbdOpponent`, a typed state — never a null.

References other aggregates by ID only (DDD aggregate boundary).
"""

from __future__ import annotations

from datetime import datetime

from footballiq.domains.football.enums import MatchStatus
from footballiq.domains.football.ids import MatchId, PlayerId, RefereeId, StageId, TeamId, VenueId
from footballiq.domains.football.values import Score, TbdOpponent, XgPair
from footballiq.kernel.entity import Entity
from footballiq.kernel.errors import InvariantViolation


class Match(Entity[MatchId]):
    """A fixture that is born Scheduled and may complete exactly once."""

    __slots__ = (
        "away",
        "home",
        "is_knockout",
        "kickoff_utc",
        "player_of_match",
        "referee_id",
        "score",
        "stage_id",
        "status",
        "venue_id",
        "xg",
    )

    def __init__(  # noqa: PLR0913 - fixture context is irreducible
        self,
        match_id: MatchId,
        *,
        home: TeamId,
        away: TeamId | TbdOpponent,
        stage_id: StageId,
        is_knockout: bool,
        venue_id: VenueId,
        referee_id: RefereeId,
        kickoff_utc: datetime,
    ) -> None:
        super().__init__(match_id)
        if not isinstance(away, TbdOpponent) and home == away:
            raise InvariantViolation("a team cannot play itself")
        if isinstance(away, TbdOpponent) and not is_knockout:
            raise InvariantViolation("TBD opponents exist only in knockout brackets")
        self.home = home
        self.away: TeamId | TbdOpponent = away
        self.stage_id = stage_id
        self.is_knockout = is_knockout
        self.venue_id = venue_id
        self.referee_id = referee_id
        self.kickoff_utc = kickoff_utc
        self.status = MatchStatus.SCHEDULED
        self.score: Score | None = None
        self.xg: XgPair | None = None
        self.player_of_match: PlayerId | None = None

    # -- queries ------------------------------------------------------------

    @property
    def is_completed(self) -> bool:
        return self.status is MatchStatus.COMPLETED

    @property
    def opponent_determined(self) -> bool:
        return not isinstance(self.away, TbdOpponent)

    # -- transitions (the only legal mutations) ------------------------------

    def resolve_opponent(self, team: TeamId) -> None:
        """Replace a TBD slot with the qualified team (idempotent update path)."""
        if self.opponent_determined:
            raise InvariantViolation("opponent already determined")
        if team == self.home:
            raise InvariantViolation("a team cannot play itself")
        self.away = team

    def complete(
        self,
        score: Score,
        xg: XgPair,
        player_of_match: PlayerId | None = None,
    ) -> None:
        """Record the final result. Contract: Completed ⇒ score and xG present."""
        if self.is_completed:
            raise InvariantViolation("match already completed (forward-only lifecycle)")
        if not self.opponent_determined:
            raise InvariantViolation("cannot complete a match against a TBD opponent")
        if self.is_knockout and score.is_draw:
            msg = f"knockout match cannot end in a draw: {score.home}-{score.away}"
            raise InvariantViolation(msg)
        self.score = score
        self.xg = xg
        self.player_of_match = player_of_match
        self.status = MatchStatus.COMPLETED
