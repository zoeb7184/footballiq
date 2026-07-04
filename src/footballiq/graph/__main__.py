"""Graph batch CLI: `python -m footballiq.graph build`."""

from __future__ import annotations

import sys

from sqlalchemy import create_engine

from footballiq.graph.build import build_talent_flow
from footballiq.infrastructure.config import load_settings


def main(args: list[str]) -> int:
    if args == ["build"]:
        engine = create_engine(load_settings().database_url)
        result = build_talent_flow(engine)
        print(
            f"gold.graph_edge_talent_flow: {result.n_edges} edges "
            f"({result.n_clubs} clubs, {result.n_nations} nations, "
            f"{result.total_players} players, v{result.graph_version})"
        )
        return 0
    print("usage: python -m footballiq.graph build")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
