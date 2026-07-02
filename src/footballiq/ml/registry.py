"""Feature registry — every model input is declared here or it doesn't exist.

CI enforces (testing strategy / ML design §3): every column the feature
builder produces must be registered with its group and description, and
no feature may derive from the valuation label.
"""

from dataclasses import dataclass
from enum import StrEnum


class FeatureGroup(StrEnum):
    """ML design §2A groups. Cross-sectional model: no as-of cutoffs needed."""

    ATTRIBUTE = "attribute"      # registry facts, known independent of play
    PERFORMANCE = "performance"  # observed tournament output (per-90, shrunk)
    CONTEXT = "context"          # team / club environment


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """One declared feature."""

    name: str
    group: FeatureGroup
    description: str


VALUATION_FEATURE_VERSION = "1.0.0"

VALUATION_FEATURES: tuple[FeatureSpec, ...] = (
    FeatureSpec("age_years", FeatureGroup.ATTRIBUTE,
                "Age at tournament start (2026-06-11), fixed reference date"),
    FeatureSpec("height_cm", FeatureGroup.ATTRIBUTE, "Registered height"),
    FeatureSpec("caps", FeatureGroup.ATTRIBUTE, "Career international caps"),
    FeatureSpec("international_goals", FeatureGroup.ATTRIBUTE,
                "Career international goals"),
    FeatureSpec("position", FeatureGroup.ATTRIBUTE,
                "GK/DEF/MID/FWD (encoded at training time)"),
    FeatureSpec("minutes_played", FeatureGroup.PERFORMANCE,
                "Total tournament minutes (from lineups)"),
    FeatureSpec("appearances", FeatureGroup.PERFORMANCE,
                "Matches with minutes > 0"),
    FeatureSpec("starts", FeatureGroup.PERFORMANCE, "Starting XI selections"),
    FeatureSpec("goals_p90", FeatureGroup.PERFORMANCE,
                "Goals per 90 from events; <90 min shrunk to position mean"),
    FeatureSpec("assists_p90", FeatureGroup.PERFORMANCE,
                "Assists per 90 from events; <90 min shrunk to position mean"),
    FeatureSpec("cards_p90", FeatureGroup.PERFORMANCE,
                "Yellow+red per 90; <90 min shrunk to position mean"),
    FeatureSpec("low_minutes_flag", FeatureGroup.PERFORMANCE,
                "1 when minutes < 90 (per-90 rates are shrunk estimates)"),
    FeatureSpec("team_elo", FeatureGroup.CONTEXT, "National team Elo (pre-tournament)"),
    FeatureSpec("team_fifa_ranking", FeatureGroup.CONTEXT,
                "National team FIFA rank (pre-tournament)"),
    FeatureSpec("club_count", FeatureGroup.CONTEXT,
                "Frequency encoding of club: squad members from same club "
                "(ML design §2A fallback — leak-proof by construction)"),
)

# Hard rule (ML design §2A rule 1): no feature may touch the label.
FORBIDDEN_LABEL_TOKENS: tuple[str, ...] = ("market_value",)
