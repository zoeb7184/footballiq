"""Deterministic route classification (rag-design §1).

Normalizes the question (lowercase, punctuation stripped, crude singular/plural
folding) then matches an ordered keyword catalog — no model, so routing is
reproducible and CI-checkable. Single-word keywords match whole tokens (so
"club" doesn't fire on "clubhouse"); phrases match as substrings. Anything
unmatched falls to DOCS (retrieval-only), the honest default.
"""

from __future__ import annotations

import re

from footballiq.application.rag.ports import Route

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_MIN_IES_LEN = 4  # keep "ties"->"ty" but leave short words alone
_MIN_PLURAL_LEN = 2  # don't strip the 's' off 2-letter tokens ("is", "as")


def _singularize(token: str) -> str:
    """Crude English plural -> singular so 'clubs'/'supplies' fold together."""
    if token.endswith("ies") and len(token) > _MIN_IES_LEN:
        return token[:-3] + "y"
    if token.endswith(("ches", "shes", "sses", "xes")):
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > _MIN_PLURAL_LEN:
        return token[:-1]
    return token


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, singularize each token."""
    tokens = _NON_ALNUM.sub(" ", text.lower()).split()
    return " ".join(_singularize(t) for t in tokens)


# Ordered: earlier routes win. Explanation before prediction ("why is X valued").
_RULES: tuple[tuple[Route, tuple[str, ...]], ...] = (
    (Route.EXPLANATION, ("why", "explain", "explanation", "shap", "driver",
                         "because")),
    (Route.PREDICTION, ("undervalued", "overvalued", "value gap", "mispriced",
                        "predicted value", "predicted worth", "bargain")),
    (Route.GRAPH, ("supply", "supplies", "supplier", "talent", "talent value",
                   "club", "clubs", "team", "teams", "network", "graph", "flow",
                   "relationship", "connection", "feeder", "concentration")),
    (Route.KPI, ("squad value", "total value", "how many", "how much",
                 "average", "count", "number of", "goals", "kpi")),
)
# Normalize keywords once, so query and catalog fold plurals the same way.
_NORMALIZED_RULES: tuple[tuple[Route, tuple[str, ...]], ...] = tuple(
    (route, tuple(normalize(k) for k in keywords)) for route, keywords in _RULES
)


def classify(question: str) -> Route:
    """Route a question by normalized keyword match; unmatched -> DOCS."""
    q = normalize(question)
    tokens = set(q.split())
    for route, keywords in _NORMALIZED_RULES:
        for keyword in keywords:
            if (" " in keyword and keyword in q) or (
                " " not in keyword and keyword in tokens
            ):
                return route
    return Route.DOCS
