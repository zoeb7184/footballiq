"""End-to-end smoke check for `make demo`.

Confirms every layer produced data: warehouse -> features -> model predictions
-> explanations -> talent-flow graph -> RAG index. Exit non-zero if any layer is
empty so `make demo` fails loudly rather than pretending success.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from footballiq.infrastructure.config import load_settings

_CHECKS = [
    ("gold.fact_match", "matches"),
    ("gold.feature_player_valuation", "features"),
    ("gold.prediction_player_valuation", "predictions"),
    ("gold.explanation_player_valuation", "explanations"),
    ("gold.graph_edge_talent_flow", "graph edges"),
    ("ai.document_chunk", "indexed chunks"),
]


def main() -> int:
    engine = create_engine(load_settings().database_url)
    ok = True
    print("=== FootballIQ end-to-end smoke check ===")
    with engine.connect() as conn:
        for table, label in _CHECKS:
            try:
                count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            except Exception as exc:  # missing table = layer never ran
                print(f"FAIL  {label:16} {table} ({type(exc).__name__})")
                ok = False
                continue
            if count:
                print(f"OK    {label:16} {int(count):>6}  {table}")
            else:
                print(f"EMPTY {label:16} {table}")
                ok = False
    print("\nDEMO OK — every layer produced data." if ok
          else "\nDEMO INCOMPLETE — a layer is empty (see above).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
