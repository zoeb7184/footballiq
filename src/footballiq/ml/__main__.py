"""ML batch CLI: `python -m footballiq.ml <features|train-valuation>`."""

from __future__ import annotations

import json
import sys

from sqlalchemy import create_engine

from footballiq.infrastructure.config import load_settings
from footballiq.ml.features import build_valuation_features
from footballiq.ml.registry import VALUATION_FEATURE_VERSION


def main(args: list[str]) -> int:
    engine = create_engine(load_settings().database_url)
    if args == ["features"]:
        count = build_valuation_features(engine)
        print(
            f"gold.feature_player_valuation: {count} rows "
            f"(v{VALUATION_FEATURE_VERSION})"
        )
        return 0
    if args == ["train-valuation"]:
        from footballiq.ml.valuation import train_production

        metrics = train_production(engine)
        print(json.dumps(metrics, indent=2))
        print("gate PASSED — model registered as production")
        return 0
    print("usage: python -m footballiq.ml <features|train-valuation>")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
