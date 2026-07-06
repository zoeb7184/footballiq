# FootballIQ Portal (Streamlit)

A customer-facing portal that reads the FootballIQ API **only** — no direct
warehouse access. This is deliberate: it proves the public API contract is
sufficient for a real client (xai-design §5).

## Run

```bash
pip install -e ".[portal]"   # streamlit + httpx + pandas
make api                     # in one terminal (the portal needs the API up)
make portal                  # streamlit run portal/app.py
```

Configure the target API from the sidebar, or via env: `FIQ_API_URL`
(default `http://localhost:8000`) and `FIQ_API_KEY` (default `dev-local-key`).

## Pages

- **Scout Shortlist** — valuations sorted by value gap; pick a player to see
  their predicted vs market value and the SHAP drivers behind it.
- **Talent Flow** — top talent-supplier clubs and per-nation supply
  concentration (HHI).
- **Ask the Analyst** — natural-language questions answered from the warehouse,
  with a grounded badge, the SQL facts used, and document citations.

## Design

`api_client.py` is a thin, typed httpx wrapper over `/v1` and the only data
source; it has no Streamlit dependency and is unit-tested
(`tests/unit/test_portal_client.py`) with `httpx.MockTransport`. The Streamlit
pages are thin views over that client.
