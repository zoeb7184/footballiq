"""Scout Shortlist — valuations, value gaps, and per-player SHAP drivers.

All data via the API (valuations + explanation endpoints); no DB access.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import ApiError
from session import sidebar_client

_TOP_DRIVERS = 8

st.title("Scout Shortlist")
st.caption("Model valuations sorted by value gap (predicted minus market).")

client = sidebar_client()

try:
    page = client.valuations(sort="value_gap", order="desc", limit=25)
except ApiError as exc:
    st.error(f"Could not load valuations ({exc}). Is the platform scored?")
    st.stop()

items = page.get("items", [])
if not items:
    st.info("No valuations yet — run `make features && make score`.")
    st.stop()

table = pd.DataFrame([
    {
        "Player": it["name"],
        "Position": it["position"],
        "Market (€m)": round(it["market_value_eur"] / 1e6, 1),
        "Predicted (€m)": round(it["predicted_value_eur"] / 1e6, 1),
        "Gap (€m)": round(it["value_gap_eur"] / 1e6, 1),
    }
    for it in items
])
st.dataframe(table, use_container_width=True, hide_index=True)

st.subheader("Player valuation & drivers")
by_label = {f"{it['name']} — {it['position']}": it["player_id"] for it in items}
choice = st.selectbox("Player", list(by_label))
player_id = by_label[choice]

try:
    valuation = client.valuation(player_id)
    explanation = client.explanation(player_id)
except ApiError as exc:
    st.error(f"Could not load player detail ({exc}).")
    st.stop()

col_a, col_b, col_c = st.columns(3)
col_a.metric("Market value", f"€{valuation['market_value_eur'] / 1e6:.1f}m")
col_b.metric("Predicted value", f"€{valuation['predicted_value_eur'] / 1e6:.1f}m")
col_c.metric("Value gap", f"€{valuation['value_gap_eur'] / 1e6:.1f}m")

drivers = explanation.get("contributions", [])[:_TOP_DRIVERS]
if drivers:
    chart = pd.DataFrame(
        {"multiplicative factor": [d["multiplicative_factor"] for d in drivers]},
        index=[d["feature_name"] for d in drivers],
    )
    st.bar_chart(chart, horizontal=True)

st.caption(valuation.get("accuracy_note", ""))
st.caption(
    f"model {valuation['model_version']} | features {valuation['feature_version']} "
    f"| scored {valuation['scored_at']}"
)
