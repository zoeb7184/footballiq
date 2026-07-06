"""Ask the Analyst — natural-language questions, grounded in the warehouse.

Calls the RAG endpoint; every stated number is traceable to a fact source.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import ApiError
from session import sidebar_client

_EXAMPLES = [
    "What is the total squad value?",
    "Which player is most undervalued?",
    "Which club supplies the most talent value?",
    "What does the SHAP explanation represent?",
]

st.title("Ask the Analyst")
st.caption("Answers come from stored data and indexed docs — numbers only from SQL.")

client = sidebar_client()

question = st.text_input("Your question", _EXAMPLES[0])
st.caption("Try: " + " | ".join(_EXAMPLES[1:]))

if st.button("Ask", type="primary") and question.strip():
    try:
        answer = client.ask(question)
    except ApiError as exc:
        st.error(f"The analyst could not answer ({exc}).")
        st.stop()

    if answer.get("grounded"):
        st.success("Grounded — every number traces to a fact source.")
    else:
        st.warning("Not fully grounded — treat figures with caution.")

    st.write(answer.get("answer", ""))
    st.caption(f"route: {answer.get('route', 'unknown')}")

    facts = answer.get("facts", [])
    if facts:
        st.subheader("Facts (from SQL)")
        st.dataframe(
            pd.DataFrame(facts), use_container_width=True, hide_index=True
        )

    citations = answer.get("citations", [])
    if citations:
        st.subheader("Sources")
        for c in citations:
            st.caption(f"{c['source_path']} — {c['section']} ({c['score']:.2f})")
