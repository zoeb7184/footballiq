"""ML batch CLI: `python -m footballiq.ml features`."""

from __future__ import annotations

import sys

from sqlalchemy import create_engine

from footballiq.infrastructure.config import load_settings
from footballiq.ml.features import build_valuation_features
from footballiq.ml.registry import VALUATION_FEATURE_VERSION


def main(args: list[str]) -> int:
    if args != ["features"]:
        print("usage: python -m footballiq.ml features")
        return 2
    engine = create_engine(load_settings().database_url)
    count = build_valuation_features(engine)
    print(f"gold.feature_player_valuation: {count} rows (v{VALUATION_FEATURE_VERSION})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
