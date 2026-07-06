"""Talent Flow — top supplier clubs and nation supply-concentration.

All data via the graph API endpoints; no DB access.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import ApiError
from session import sidebar_client

st.title("Talent Flow")
st.caption("Which clubs feed which nations, and how concentrated squad sourcing is.")

client = sidebar_client()

try:
    clubs = client.graph_clubs(sort="value_exported", limit=15).get("items", [])
except ApiError as exc:
    st.error(f"Could not load graph metrics ({exc}). Run `make graph`.")
    st.stop()

if not clubs:
    st.info("No talent-flow metrics yet — run `make graph`.")
    st.stop()

st.subheader("Top talent-supplier clubs (by value exported)")
club_chart = pd.DataFrame(
    {"Value exported (€m)": [round(c["value_exported"] / 1e6, 1) for c in clubs]},
    index=[c["club"] for c in clubs],
)
st.bar_chart(club_chart, horizontal=True)

st.subheader("Nation supply-concentration (HHI)")
try:
    teams = client.teams(limit=100).get("items", [])
except ApiError as exc:
    st.error(f"Could not load teams ({exc}).")
    st.stop()

by_name = {t["name"]: t["team_id"] for t in teams}
if not by_name:
    st.info("No teams available.")
    st.stop()

nation = st.selectbox("Nation", sorted(by_name))
try:
    concentration = client.nation_concentration(by_name[nation])
except ApiError as exc:
    st.error(f"No concentration data for {nation} ({exc}).")
    st.stop()

col_a, col_b, col_c = st.columns(3)
col_a.metric("HHI (0-1)", f"{concentration['hhi_players']:.3f}")
col_b.metric("Supplier clubs", concentration["supplier_count"])
col_c.metric("Squad value", f"€{concentration['total_value'] / 1e6:.1f}m")

suppliers = concentration.get("top_suppliers", [])
if suppliers:
    supplier_table = pd.DataFrame([
        {
            "Club": s["club"],
            "Players": s["player_count"],
            "Share": f"{s['share'] * 100:.0f}%",
            "Value (€m)": round(s["total_value"] / 1e6, 1),
        }
        for s in suppliers
    ])
    st.dataframe(supplier_table, width="stretch", hide_index=True)

st.caption("Higher HHI = squad drawn from fewer clubs (more concentration risk).")
