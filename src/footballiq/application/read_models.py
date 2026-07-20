"""Read-model records and ports (backend design §2).

Records are plain application-level results; the api layer maps them to
response DTOs. Reserved dimension members (sk < 0) never appear here —
they are join semantics, not catalog entries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TeamRecord:
    """One national team from gold.dim_team (real members only)."""

    team_id: int
    name: str
    fifa_code: str
    group_letter: str | None
    confederation: str | None
    fifa_ranking: int | None
    elo_rating: int | None


@dataclass(frozen=True, slots=True)
class Page:
    """Pagination envelope for list queries."""

    total: int
    limit: int
    offset: int


class TeamReadModel(Protocol):
    """Gold-backed access to the team catalog."""

    def list_teams(self, *, limit: int, offset: int) -> list[TeamRecord]: ...

    def count_teams(self) -> int: ...

    def get_team(self, team_id: int) -> TeamRecord | None: ...


@dataclass(frozen=True, slots=True)
class MatchRecord:
    """One match from the star (fact_match + conformed dims).

    away_team is None when the away slot is a reserved member — the DTO
    layer renders that as an explicit TBD state, never a null.
    """

    match_id: int
    match_date: str  # ISO date
    kickoff_utc: str  # HH:MM
    stage_name: str
    is_knockout: bool
    venue_name: str
    home_team: TeamSide
    away_team: TeamSide | None
    status: str
    home_score: int | None
    away_score: int | None
    home_xg: float | None
    away_xg: float | None


@dataclass(frozen=True, slots=True)
class TeamSide:
    """Minimal team reference embedded in a match."""

    team_id: int
    name: str
    fifa_code: str


class MatchReadModel(Protocol):
    """Gold-backed access to the match ledger."""

    def list_matches(
        self, *, limit: int, offset: int, status: str | None
    ) -> list[MatchRecord]: ...

    def count_matches(self, *, status: str | None) -> int: ...

    def get_match(self, match_id: int) -> MatchRecord | None: ...


@dataclass(frozen=True, slots=True)
class PlayerRecord:
    """One player from gold.dim_player with national-team context."""

    player_id: int
    name: str
    position: str
    club: str
    market_value_eur: int
    caps: int
    international_goals: int
    date_of_birth: str  # ISO date; age derived by consumers at query time
    height_cm: int
    team: TeamSide


@dataclass(frozen=True, slots=True)
class PlayerFilter:
    """Optional catalog filters."""

    team_id: int | None = None
    position: str | None = None


class PlayerReadModel(Protocol):
    """Gold-backed access to the player registry."""

    def list_players(
        self, *, limit: int, offset: int, filters: PlayerFilter
    ) -> list[PlayerRecord]: ...

    def count_players(self, *, filters: PlayerFilter) -> int: ...

    def get_player(self, player_id: int) -> PlayerRecord | None: ...


@dataclass(frozen=True, slots=True)
class ShapContribution:
    """One feature's SHAP attribution for a player (XAI design §3).

    shap_log is canonical (additive in log1p space); multiplicative_factor =
    exp(shap_log) is the display form ("caps: x1.6"). rank is by |shap_log|.
    """

    feature_name: str
    feature_value: float
    shap_log: float
    multiplicative_factor: float
    rank: int


@dataclass(frozen=True, slots=True)
class ValuationRecord:
    """A player's model valuation from gold.prediction_player_valuation.

    Carries its full provenance (model_version, feature_version, scored_at):
    every rendered valuation must show what produced it (XAI design §6).
    top_k is the denormalized headline attribution for one-call reads.
    """

    player_id: int
    name: str
    position: str
    market_value_eur: int
    predicted_value_eur: float
    value_gap_eur: float
    model_version: str
    feature_version: str
    scored_at: str
    top_k: list[ShapContribution]


@dataclass(frozen=True, slots=True)
class ExplanationRecord:
    """The full SHAP breakdown for one player (all features, long format).

    baseline_log is the model's expected log1p value; baseline_log + sum of
    contributions' shap_log reconstructs log1p(predicted_value_eur) — the
    additivity invariant enforced at scoring time (XAI design §4).
    """

    player_id: int
    name: str
    position: str
    market_value_eur: int
    predicted_value_eur: float
    value_gap_eur: float
    baseline_log: float
    model_version: str
    feature_version: str
    scored_at: str
    contributions: list[ShapContribution]


@dataclass(frozen=True, slots=True)
class ValuationFilter:
    """Sort controls for the valuation shortlist (scout story 1)."""

    sort: str = "value_gap"      # value_gap | predicted_value | market_value
    descending: bool = True


class ValuationReadModel(Protocol):
    """Gold-backed access to model valuations and their explanations."""

    def list_valuations(
        self, *, limit: int, offset: int, filters: ValuationFilter
    ) -> list[ValuationRecord]: ...

    def count_valuations(self) -> int: ...

    def get_valuation(self, player_id: int) -> ValuationRecord | None: ...

    def get_explanation(self, player_id: int) -> ExplanationRecord | None: ...


@dataclass(frozen=True, slots=True)
class TalentFlowEdge:
    """One club -> nation supply edge (graph-design §1). Doubles as viz data."""

    club: str
    nation_id: int
    nation_name: str
    player_count: int
    total_value: float


@dataclass(frozen=True, slots=True)
class ClubMetric:
    """A club's supplier metrics (graph-design §2)."""

    club: str
    nations_supplied: int
    players_supplied: int
    value_exported: float


@dataclass(frozen=True, slots=True)
class SupplierShare:
    """One club's share of a nation's squad (concentration breakdown)."""

    club: str
    player_count: int
    total_value: float
    share: float


@dataclass(frozen=True, slots=True)
class NationConcentration:
    """A nation's supplier-concentration profile (graph-design §2).

    hhi_players in (0, 1]: higher = squad drawn from fewer clubs = more
    concentrated supply risk. top_suppliers is the ranked breakdown.
    """

    nation_id: int
    nation_name: str
    supplier_count: int
    players_total: int
    total_value: float
    hhi_players: float
    top_suppliers: list[SupplierShare]


@dataclass(frozen=True, slots=True)
class ClubFilter:
    """Sort control for the club supplier ranking."""

    sort: str = "value_exported"  # value_exported | players_supplied | nations_supplied
    descending: bool = True


class GraphReadModel(Protocol):
    """Gold-backed access to talent-flow edges and graph metrics."""

    def list_edges(
        self, *, limit: int, offset: int
    ) -> list[TalentFlowEdge]: ...

    def count_edges(self) -> int: ...

    def list_clubs(
        self, *, limit: int, offset: int, filters: ClubFilter
    ) -> list[ClubMetric]: ...

    def count_clubs(self) -> int: ...

    def get_nation_concentration(
        self, nation_id: int, *, top: int
    ) -> NationConcentration | None: ...


@dataclass(frozen=True, slots=True)
class ScoringRate:
    """Observed tournament scoring rate (simulation design §2).

    avg_total_goals is the mean of home+away goals over completed matches;
    matches_observed carries the sample size so consumers can judge it.
    """

    avg_total_goals: float
    matches_observed: int


class ScoringRateReadModel(Protocol):
    """Gold-backed access to the observed scoring rate of completed matches."""

    def observed_scoring_rate(self) -> ScoringRate | None: ...


@dataclass(frozen=True, slots=True)
class ModelRegistryEntry:
    """One registered model with its full lineage (ML design §10)."""

    model_id: str
    task: str
    version: str
    feature_version: str
    git_commit: str
    params: dict[str, float | int | str]
    metrics: dict[str, dict[str, float]]
    seed: int
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class FeatureImportanceRow:
    """Global importance of one feature: mean |SHAP| over all scored players."""

    feature_name: str
    mean_abs_shap_log: float
    mean_feature_value: float
    players: int


class ModelPerformanceReadModel(Protocol):
    """Gold-backed access to the model registry and aggregated SHAP."""

    def list_registry_entries(self, *, task: str) -> list[ModelRegistryEntry]: ...

    def feature_importance(self) -> list[FeatureImportanceRow]: ...
