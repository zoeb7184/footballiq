"""Simulation math tests — pure functions, no app, no DB."""

import random

import pytest

from footballiq.application.simulation import (
    FALLBACK_GOALS_PER_MATCH,
    elo_win_expectancy,
    sample_poisson,
    wilson_interval,
)

_HALF = 0.5


def test_elo_expectancy_equal_ratings_is_half() -> None:
    assert elo_win_expectancy(1800, 1800) == pytest.approx(_HALF)


def test_elo_expectancy_is_symmetric() -> None:
    assert elo_win_expectancy(1900, 1700) + elo_win_expectancy(1700, 1900) == pytest.approx(1.0)


def test_elo_expectancy_400_points_is_10_to_1() -> None:
    # By definition of the Elo scale: +400 rating points ⇒ 10:1 odds.
    assert elo_win_expectancy(2000, 1600) == pytest.approx(10 / 11)


def test_wilson_interval_brackets_the_point_estimate() -> None:
    ci = wilson_interval(600, 1000)
    assert ci.ci_low < ci.value < ci.ci_high
    assert ci.value == pytest.approx(0.6)


def test_wilson_interval_stays_in_unit_range_at_extremes() -> None:
    zero = wilson_interval(0, 50)
    one = wilson_interval(50, 50)
    assert zero.ci_low == pytest.approx(0.0, abs=1e-12)
    assert zero.ci_high > 0.0
    assert one.ci_high == pytest.approx(1.0, abs=1e-12)
    assert one.ci_low < 1.0


def test_wilson_interval_rejects_empty_sample() -> None:
    with pytest.raises(ValueError, match="n > 0"):
        wilson_interval(0, 0)


def test_wilson_interval_narrows_with_sample_size() -> None:
    wide = wilson_interval(60, 100)
    narrow = wilson_interval(6000, 10_000)
    assert (narrow.ci_high - narrow.ci_low) < (wide.ci_high - wide.ci_low)


def test_poisson_sampler_mean_approximates_lambda() -> None:
    rng = random.Random(42)
    lam = 1.4
    n = 20_000
    mean = sum(sample_poisson(lam, rng) for _ in range(n)) / n
    assert mean == pytest.approx(lam, abs=0.05)


def test_poisson_sampler_is_deterministic_per_seed() -> None:
    a = [sample_poisson(1.3, random.Random(7)) for _ in range(100)]
    b = [sample_poisson(1.3, random.Random(7)) for _ in range(100)]
    assert a == b


def test_fallback_rate_is_the_documented_wc2022_average() -> None:
    assert pytest.approx(172 / 64) == FALLBACK_GOALS_PER_MATCH
