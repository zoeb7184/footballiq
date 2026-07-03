"""Scoring sanity check (M5 Slice 3) — run after `make score`.

    python scripts/validate_scoring.py

Read-only. Uses the repo's own DB config, so no psql/libpq needed. Mirrors
docs/ml/queries/scoring_validation.sql and independently reconstructs the
additivity invariant from the warehouse side.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from footballiq.infrastructure.config import load_settings

SCHEMA = "gold"


def _eur(x: object) -> str:
    return f"{float(x):>16,.0f}" if x is not None else f"{'<NULL>':>16}"


def main() -> int:
    engine = create_engine(load_settings().database_url)
    p = f"{SCHEMA}."
    with engine.connect() as conn:
        _top(conn, p, "1. TOP 10 UNDERVALUED (model > market)", "DESC")
        _top(conn, p, "2. TOP 10 OVERVALUED (market > model)", "ASC")
        _summary(conn, p)
        _integrity(conn, p)
        _explanations(conn, p)
    return 0


def _top(conn: object, p: str, title: str, direction: str) -> None:
    print(f"\n================ {title} ================")
    rows = conn.execute(  # type: ignore[attr-defined]
        text(
            f"SELECT pr.player_sk, dp.player_name, dp.position, "
            f"pr.market_value_eur, pr.predicted_value_eur, pr.value_gap_eur "
            f"FROM {p}prediction_player_valuation pr "
            f"JOIN {p}dim_player dp ON dp.player_sk = pr.player_sk "
            f"ORDER BY pr.value_gap_eur {direction} LIMIT 10"
        )
    ).all()
    print(f"{'sk':>5}  {'player':<22} {'pos':<4} "
          f"{'market':>16} {'predicted':>16} {'gap':>16}")
    for r in rows:
        print(f"{r[0]:>5}  {str(r[1])[:22]:<22} {str(r[2] or ''):<4} "
              f"{_eur(r[3])} {_eur(r[4])} {_eur(r[5])}")


def _summary(conn: object, p: str) -> None:
    print("\n================ 3. SUMMARY STATS (EUR) ================")
    q = text(
        f"SELECT metric, min(v), "
        "percentile_cont(0.05) WITHIN GROUP (ORDER BY v), "
        "percentile_cont(0.25) WITHIN GROUP (ORDER BY v), "
        "percentile_cont(0.50) WITHIN GROUP (ORDER BY v), "
        "avg(v), "
        "percentile_cont(0.75) WITHIN GROUP (ORDER BY v), "
        "percentile_cont(0.95) WITHIN GROUP (ORDER BY v), "
        "max(v) FROM ("
        f"  SELECT 'predicted_value_eur' AS metric, predicted_value_eur AS v "
        f"  FROM {p}prediction_player_valuation "
        "  UNION ALL "
        f"  SELECT 'value_gap_eur', value_gap_eur "
        f"  FROM {p}prediction_player_valuation) s "
        "GROUP BY metric ORDER BY metric"
    )
    cols = ["min", "p05", "p25", "median", "mean", "p75", "p95", "max"]
    for r in conn.execute(q).all():  # type: ignore[attr-defined]
        print(f"\n{r[0]}:")
        for name, val in zip(cols, r[1:], strict=True):
            print(f"    {name:<7}{_eur(val)}")


def _integrity(conn: object, p: str) -> None:
    print("\n================ 4. INTEGRITY: nulls / dupes / sanity ================")
    r = conn.execute(  # type: ignore[attr-defined]
        text(
            "SELECT count(*), count(DISTINCT player_sk), "
            "count(*) FILTER (WHERE predicted_value_eur IS NULL), "
            "count(*) FILTER (WHERE value_gap_eur IS NULL), "
            "count(*) FILTER (WHERE market_value_eur IS NULL), "
            "count(*) FILTER (WHERE player_sk <= 0), "
            "count(*) FILTER (WHERE predicted_value_eur <= 0), "
            "count(*) FILTER (WHERE predicted_value_eur > 500000000) "
            f"FROM {p}prediction_player_valuation"
        )
    ).one()
    labels = ["n_rows", "n_distinct_players", "null_predicted", "null_gap",
              "null_market", "reserved_leaked", "nonpositive_pred", "pred_over_500m"]
    for name, val in zip(labels, r, strict=True):
        flag = "  <-- CHECK" if name not in {"n_rows", "n_distinct_players"} and val else ""
        print(f"    {name:<20}{val:>8}{flag}")
    dupes = conn.execute(  # type: ignore[attr-defined]
        text(
            f"SELECT count(*) FROM (SELECT player_sk FROM {p}prediction_player_valuation "
            "GROUP BY player_sk HAVING count(*) > 1) d"
        )
    ).scalar_one()
    print(f"    {'duplicate_player_sk':<20}{dupes:>8}{'  <-- CHECK' if dupes else ''}")


def _explanations(conn: object, p: str) -> None:
    print("\n================ 5. EXPLANATION TABLE shape + additivity ================")
    r = conn.execute(  # type: ignore[attr-defined]
        text(
            f"SELECT count(*), count(DISTINCT player_sk), count(DISTINCT feature_name), "
            "count(*) FILTER (WHERE shap_log IS NULL OR multiplicative_factor IS NULL) "
            f"FROM {p}explanation_player_valuation"
        )
    ).one()
    for name, val in zip(
        ["expl_rows", "expl_players", "features_per_player", "null_shap"], r, strict=True
    ):
        print(f"    {name:<20}{val:>8}")
    worst = conn.execute(  # type: ignore[attr-defined]
        text(
            "SELECT max(abs(recon - ln(1 + predicted))) FROM ("
            "  SELECT e.player_sk, max(e.baseline_log) + sum(e.shap_log) AS recon, "
            "         max(pr.predicted_value_eur) AS predicted "
            f"  FROM {p}explanation_player_valuation e "
            f"  JOIN {p}prediction_player_valuation pr ON pr.player_sk = e.player_sk "
            "  GROUP BY e.player_sk) t"
        )
    ).scalar_one()
    dev = conn.execute(  # type: ignore[attr-defined]
        text(
            "SELECT max(abs(multiplicative_factor - exp(shap_log))) "
            f"FROM {p}explanation_player_valuation"
        )
    ).scalar_one()
    print(f"    {'worst_additivity_resid':<24}{float(worst):.2e}   (expect < 1e-4)")
    print(f"    {'worst_mult_factor_dev':<24}{float(dev):.2e}   (expect ~0)")


if __name__ == "__main__":
    raise SystemExit(main())
