"""Shared Streamlit helper: the connection sidebar + API client factory."""

from __future__ import annotations

import os

import streamlit as st

from api_client import DEFAULT_API_KEY, DEFAULT_BASE_URL, ApiClient


def sidebar_client() -> ApiClient:
    """Render the connection sidebar and return a configured API client."""
    st.sidebar.header("API connection")
    base_url = st.sidebar.text_input(
        "Base URL", os.environ.get("FIQ_API_URL", DEFAULT_BASE_URL)
    )
    api_key = st.sidebar.text_input(
        "API key",
        os.environ.get("FIQ_API_KEY", DEFAULT_API_KEY),
        type="password",
    )
    st.sidebar.caption("The portal reads the API only — no direct database access.")
    return ApiClient(base_url, api_key)
