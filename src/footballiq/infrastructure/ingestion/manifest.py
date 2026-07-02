"""Source manifest — the declared universe of ingestible files.

A file not in this manifest is not ingested (governance: sources are
declared, never discovered). matches_detailed is bronze-only by design
(reconciliation fixture, physical architecture §1).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    """One declared CSV source."""

    filename: str
    bronze_table: str
    bronze_only: bool = False


SOURCES: tuple[Source, ...] = (
    Source("teams.csv", "raw_teams"),
    Source("venues.csv", "raw_venues"),
    Source("tournament_stages.csv", "raw_tournament_stages"),
    Source("referees.csv", "raw_referees"),
    Source("matches.csv", "raw_matches"),
    Source("matches_detailed.csv", "raw_matches_detailed", bronze_only=True),
    Source("squads_and_players.csv", "raw_squads_and_players"),
    Source("player_stats.csv", "raw_player_stats"),
    Source("match_team_stats.csv", "raw_match_team_stats"),
    Source("match_lineups.csv", "raw_match_lineups"),
    Source("match_events.csv", "raw_match_events"),
)
