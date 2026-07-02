"""Team, Venue, Stage, Referee — master-data entities."""

from __future__ import annotations

from footballiq.domains.football.ids import RefereeId, StageId, TeamId, VenueId
from footballiq.kernel.entity import Entity
from footballiq.kernel.errors import InvariantViolation

_FIFA_CODE_LEN = 3
_LAT_RANGE = (-90.0, 90.0)
_LON_RANGE = (-180.0, 180.0)


class Team(Entity[TeamId]):
    """National team — a portfolio of player assets."""

    __slots__ = ("confederation", "elo_rating", "fifa_code", "fifa_ranking", "name")

    def __init__(
        self,
        team_id: TeamId,
        *,
        name: str,
        fifa_code: str,
        confederation: str,
        fifa_ranking: int,
        elo_rating: int,
    ) -> None:
        super().__init__(team_id)
        if len(fifa_code) != _FIFA_CODE_LEN or not fifa_code.isalpha():
            msg = f"FIFA code must be 3 letters, got {fifa_code!r}"
            raise InvariantViolation(msg)
        if fifa_ranking < 1 or elo_rating <= 0:
            raise InvariantViolation("rankings must be positive")
        self.name = name
        self.fifa_code = fifa_code.upper()
        self.confederation = confederation
        self.fifa_ranking = fifa_ranking
        self.elo_rating = elo_rating


class Venue(Entity[VenueId]):
    """Facility with operational covariates (capacity, elevation, geo)."""

    __slots__ = ("capacity", "city", "country", "elevation_m", "latitude", "longitude", "name")

    def __init__(  # noqa: PLR0913 - facility attributes are irreducible
        self,
        venue_id: VenueId,
        *,
        name: str,
        city: str,
        country: str,
        capacity: int,
        latitude: float,
        longitude: float,
        elevation_m: int,
    ) -> None:
        super().__init__(venue_id)
        if capacity <= 0:
            raise InvariantViolation("capacity must be positive")
        if not (_LAT_RANGE[0] <= latitude <= _LAT_RANGE[1]):
            raise InvariantViolation(f"latitude out of range: {latitude}")
        if not (_LON_RANGE[0] <= longitude <= _LON_RANGE[1]):
            raise InvariantViolation(f"longitude out of range: {longitude}")
        self.name = name
        self.city = city
        self.country = country
        self.capacity = capacity
        self.latitude = latitude
        self.longitude = longitude
        self.elevation_m = elevation_m


class Stage(Entity[StageId]):
    """Tournament phase; `is_knockout` drives the no-draw business rule."""

    __slots__ = ("is_knockout", "name")

    def __init__(self, stage_id: StageId, *, name: str, is_knockout: bool) -> None:
        super().__init__(stage_id)
        if not name.strip():
            raise InvariantViolation("stage name must be non-empty")
        self.name = name
        self.is_knockout = is_knockout


class Referee(Entity[RefereeId]):
    """Match official with externally computed historical card rate."""

    __slots__ = ("avg_cards_per_game", "country", "name")

    def __init__(
        self,
        referee_id: RefereeId,
        *,
        name: str,
        country: str,
        avg_cards_per_game: float,
    ) -> None:
        super().__init__(referee_id)
        if avg_cards_per_game < 0:
            raise InvariantViolation("card rate must be >= 0")
        self.name = name
        self.country = country
        self.avg_cards_per_game = avg_cards_per_game
