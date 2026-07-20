"""Match simulation use case (simulation design, ADR-0006).

A transparent Monte Carlo model over data the warehouse actually holds.
Every assumption is explicit, every run is seeded, and the response carries
its own methodology so no consumer can mistake it for an oracle:

1. **Elo win expectancy** (standard formula): We = 1 / (1 + 10^(-dr/400))
   where dr = home Elo - away Elo. Venue-neutral: World Cup 2026 matches
   are not home fixtures for either side, so no home-advantage term.
2. **Total goal rate** mu comes from *observed* completed matches in the
   warehouse (mean of home+away goals). If none are completed yet, the
   documented fallback is 2.6875 — the FIFA World Cup 2022 average
   (172 goals / 64 matches), a sourced constant, not an invention.
3. **Goal split assumption**: expected goals are allocated by win
   expectancy — lambda_home = mu * We, lambda_away = mu * (1 - We).
   This is a simplification (goal share ~ strength share) and is labeled
   as such in every response.
4. **Independence assumption**: goals are sampled as two independent
   Poisson processes (Knuth sampler, stdlib random only — no numpy in the
   application layer). Poisson goal counts are a long-standing baseline in
   football modelling (Maher 1982), not a state-of-the-art claim.
5. **Uncertainty is reported, not hidden**: each probability carries a
   Wilson 95% score interval for the Monte Carlo sample size used.

The service is deterministic for a given (inputs, seed): CI-checkable.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from footballiq.application.read_models import (
    ScoringRate,
    ScoringRateReadModel,
    TeamReadModel,
    TeamRecord,
)

METHOD_VERSION = "sim-1.0.0"

#: FIFA World Cup 2022: 172 goals in 64 matches. Used only when the
#: warehouse has no completed matches to observe.
FALLBACK_GOALS_PER_MATCH = 172 / 64

_ELO_SCALE = 400.0
_Z_95 = 1.959963984540054  # two-sided 95% normal quantile
_SCORE_CAP = 5  # score-matrix axis: 0..4 goals plus a "5+" bucket

MIN_RUNS = 100
MAX_RUNS = 10_000
DEFAULT_RUNS = 5_000


class UnknownTeamError(LookupError):
    """A referenced team does not exist in the warehouse."""


class MissingRatingError(ValueError):
    """A team has no Elo rating, so simulation would require invention."""


@dataclass(frozen=True, slots=True)
class ProbabilityWithCI:
    """A Monte Carlo probability with its Wilson 95% interval."""

    value: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True, slots=True)
class TeamSimSide:
    """One side of the simulated fixture, with its model inputs."""

    team_id: int
    name: str
    fifa_code: str
    elo_rating: int
    lambda_goals: float
    mean_goals_sampled: float


@dataclass(frozen=True, slots=True)
class MatchSimulationResult:
    """The full, self-describing output of one simulation run."""

    home: TeamSimSide
    away: TeamSimSide
    n_runs: int
    seed: int
    p_home_win: ProbabilityWithCI
    p_draw: ProbabilityWithCI
    p_away_win: ProbabilityWithCI
    #: score_matrix[h][a] = share of runs ending h:a; axis length is
    #: _SCORE_CAP + 1 and the final index is an open ">= cap" bucket.
    score_matrix: list[list[float]]
    score_cap: int
    goals_per_match_used: float
    goal_rate_source: str  # "observed" | "wc2022_baseline"
    matches_observed: int
    elo_win_expectancy_home: float
    method_version: str
    assumptions: tuple[str, ...]


def elo_win_expectancy(home_elo: float, away_elo: float) -> float:
    """Standard Elo expectancy of the home side, venue-neutral."""
    # math.pow (not **): the ** operator is typed Any-returning for floats.
    return 1.0 / (1.0 + math.pow(10.0, -(home_elo - away_elo) / _ELO_SCALE))


def wilson_interval(successes: int, n: int) -> ProbabilityWithCI:
    """Wilson 95% score interval — well-behaved near 0 and 1."""
    if n <= 0:
        msg = "wilson_interval requires n > 0"
        raise ValueError(msg)
    p = successes / n
    z2 = _Z_95**2
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (_Z_95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))) / denom
    return ProbabilityWithCI(
        value=p, ci_low=max(0.0, center - half), ci_high=min(1.0, center + half)
    )


def sample_poisson(lam: float, rng: random.Random) -> int:
    """Knuth's Poisson sampler; exact for the small lambdas of football."""
    threshold = math.exp(-lam)
    k = 0
    product = rng.random()
    while product > threshold:
        product *= rng.random()
        k += 1
    return k


def _assumptions(rate_source: str, matches_observed: int) -> tuple[str, ...]:
    rate_note = (
        f"Total-goal rate observed from {matches_observed} completed matches."
        if rate_source == "observed"
        else "No completed matches in the warehouse; total-goal rate falls back "
        "to the FIFA World Cup 2022 average (172/64 = 2.6875)."
    )
    return (
        "Win expectancy from standard Elo (scale 400), venue-neutral.",
        rate_note,
        "Expected goals split by win expectancy (goal share ~ strength share).",
        "Goals sampled as two independent Poisson processes (Maher 1982 baseline).",
        "Probabilities carry Wilson 95% intervals for the Monte Carlo sample size.",
        "This is a transparent baseline model, not a betting or forecasting product.",
    )


class SimulationService:
    """Monte Carlo match simulation over warehouse ratings — the M10 use case."""

    def __init__(self, teams: TeamReadModel, rates: ScoringRateReadModel) -> None:
        self._teams = teams
        self._rates = rates

    def simulate_match(
        self,
        *,
        home_team_id: int,
        away_team_id: int,
        n_runs: int = DEFAULT_RUNS,
        seed: int = 42,
    ) -> MatchSimulationResult:
        if not MIN_RUNS <= n_runs <= MAX_RUNS:
            msg = f"n_runs must be within [{MIN_RUNS}, {MAX_RUNS}]"
            raise ValueError(msg)
        home = self._require_team(home_team_id)
        away = self._require_team(away_team_id)
        home_elo = _require_elo(home)
        away_elo = _require_elo(away)

        rate = self._rates.observed_scoring_rate()
        mu, source, observed = _resolve_rate(rate)
        expectancy = elo_win_expectancy(home_elo, away_elo)
        lambda_home = mu * expectancy
        lambda_away = mu * (1.0 - expectancy)

        rng = random.Random(seed)
        wins = draws = losses = 0
        goals_home_total = goals_away_total = 0
        axis = _SCORE_CAP + 1
        counts = [[0] * axis for _ in range(axis)]
        for _ in range(n_runs):
            gh = sample_poisson(lambda_home, rng)
            ga = sample_poisson(lambda_away, rng)
            goals_home_total += gh
            goals_away_total += ga
            if gh > ga:
                wins += 1
            elif gh == ga:
                draws += 1
            else:
                losses += 1
            counts[min(gh, _SCORE_CAP)][min(ga, _SCORE_CAP)] += 1

        return MatchSimulationResult(
            home=_side(home, home_elo, lambda_home, goals_home_total / n_runs),
            away=_side(away, away_elo, lambda_away, goals_away_total / n_runs),
            n_runs=n_runs,
            seed=seed,
            p_home_win=wilson_interval(wins, n_runs),
            p_draw=wilson_interval(draws, n_runs),
            p_away_win=wilson_interval(losses, n_runs),
            score_matrix=[[c / n_runs for c in row] for row in counts],
            score_cap=_SCORE_CAP,
            goals_per_match_used=mu,
            goal_rate_source=source,
            matches_observed=observed,
            elo_win_expectancy_home=expectancy,
            method_version=METHOD_VERSION,
            assumptions=_assumptions(source, observed),
        )

    def _require_team(self, team_id: int) -> TeamRecord:
        team = self._teams.get_team(team_id)
        if team is None:
            msg = f"unknown team_id {team_id}"
            raise UnknownTeamError(msg)
        return team


def _resolve_rate(rate: ScoringRate | None) -> tuple[float, str, int]:
    if rate is not None and rate.matches_observed > 0:
        return rate.avg_total_goals, "observed", rate.matches_observed
    return FALLBACK_GOALS_PER_MATCH, "wc2022_baseline", 0


def _require_elo(team: TeamRecord) -> int:
    if team.elo_rating is None:
        msg = f"team {team.team_id} ({team.name}) has no Elo rating; cannot simulate"
        raise MissingRatingError(msg)
    return team.elo_rating


def _side(team: TeamRecord, elo: int, lam: float, sampled_mean: float) -> TeamSimSide:
    return TeamSimSide(
        team_id=team.team_id,
        name=team.name,
        fifa_code=team.fifa_code,
        elo_rating=elo,
        lambda_goals=lam,
        mean_goals_sampled=sampled_mean,
    )
