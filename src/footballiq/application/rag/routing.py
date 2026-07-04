"""Deterministic route classification (rag-design §1).

Keyword rules, ordered by specificity — no model, so routing is reproducible
and CI-checkable. Anything unmatched falls to DOCS (retrieval-only), which is
the honest default: answer from indexed documentation, not from a guess.
"""

from __future__ import annotations

from footballiq.application.rag.ports import Route

# Ordered: earlier routes win. Explanation before prediction ("why is X valued").
_RULES: tuple[tuple[Route, tuple[str, ...]], ...] = (
    (Route.EXPLANATION, ("why", "explain", "explanation", "shap", "driver",
                         "because")),
    (Route.PREDICTION, ("undervalued", "overvalued", "value gap", "mispriced",
                        "predicted value", "predicted worth", "bargain")),
    (Route.GRAPH, ("supplier", "supply", "talent flow", "which clubs",
                   "exports", "exported", "concentration", "feeder")),
    (Route.KPI, ("squad value", "total value", "how many", "how much",
                 "average", "count", "number of", "goals", "kpi")),
)


def classify(question: str) -> Route:
    """Route a question by keyword; unmatched -> DOCS (retrieval-only)."""
    q = question.lower()
    for route, keywords in _RULES:
        if any(k in q for k in keywords):
            return route
    return Route.DOCS
