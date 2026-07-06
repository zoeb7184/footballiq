"""FootballIQ customer portal — landing page.

Run: `make portal` (streamlit run portal/app.py). Three pages, all reading the
public API only (xai-design §5): Scout Shortlist, Talent Flow, Ask the Analyst.
"""

from __future__ import annotations

import streamlit as st

from api_client import ApiError
from session import sidebar_client

st.set_page_config(page_title="FootballIQ", page_icon="⚽", layout="wide")

st.title("FootballIQ — Talent Intelligence")
st.write(
    "A scouting portal over the FootballIQ API. Every page reads the public "
    "HTTP API with an API key — nothing here touches the warehouse directly, "
    "which proves the API contract is sufficient for a real client."
)

st.subheader("Pages")
st.markdown(
    "- **Scout Shortlist** — model valuations, biggest value gaps, and the "
    "SHAP drivers behind any player's valuation.\n"
    "- **Talent Flow** — which clubs supply the most talent, and how "
    "concentrated each nation's squad sourcing is.\n"
    "- **Ask the Analyst** — natural-language questions answered from the "
    "warehouse, with every number traceable to SQL."
)

client = sidebar_client()
try:
    ready = client.teams(limit=1)
    st.success(f"Connected — API reachable ({ready.get('total', 0)} teams).")
except ApiError as exc:
    st.error(f"Could not reach the API ({exc}). Is `make api` running?")

st.caption("Use the sidebar to point the portal at a different API URL or key.")
