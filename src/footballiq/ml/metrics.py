"""Valuation metrics (ML design §1): RMSLE, MdAPE, share within ±20%.

All functions take EUR-scale arrays; log transforms happen here so metric
definitions live in exactly one place.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def rmsle(y_true_eur: FloatArray, y_pred_eur: FloatArray) -> float:
    """Root mean squared log error (log1p)."""
    diff = np.log1p(y_pred_eur) - np.log1p(y_true_eur)
    return float(np.sqrt(np.mean(diff**2)))


def mdape(y_true_eur: FloatArray, y_pred_eur: FloatArray) -> float:
    """Median absolute percentage error."""
    return float(np.median(np.abs(y_pred_eur - y_true_eur) / y_true_eur))


def within_20pct(y_true_eur: FloatArray, y_pred_eur: FloatArray) -> float:
    """Share of predictions within ±20% of actual (scope.md metric)."""
    return float(np.mean(np.abs(y_pred_eur - y_true_eur) / y_true_eur <= 0.20))


def evaluate(y_true_eur: FloatArray, y_pred_eur: FloatArray) -> dict[str, float]:
    """The full metric block, EUR scale in, dict out."""
    return {
        "rmsle": rmsle(y_true_eur, y_pred_eur),
        "mdape": mdape(y_true_eur, y_pred_eur),
        "within_20pct": within_20pct(y_true_eur, y_pred_eur),
    }
