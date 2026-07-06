"""Typed HTTP client for the FootballIQ API (portal's only data source).

Thin wrapper over the public /v1 endpoints with API-key auth. No warehouse
access — the portal can only ever see what the API contract exposes, which is
exactly the point (xai-design §5). Injectable httpx client for testing.
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_KEY = "dev-local-key"
_TIMEOUT = 30.0


class ApiError(RuntimeError):
    """The API returned a non-success status."""


class ApiClient:
    """Reads the FootballIQ API. One client per session; close when done."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str = DEFAULT_API_KEY,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=_TIMEOUT,
        )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            msg = f"request to {path} failed: {exc}"
            raise ApiError(msg) from exc
        return self._unwrap(response)

    @staticmethod
    def _unwrap(response: httpx.Response) -> Any:
        if response.status_code >= httpx.codes.BAD_REQUEST:
            detail = _safe_detail(response)
            msg = f"API {response.status_code}: {detail}"
            raise ApiError(msg)
        return response.json()

    # --- valuations (scout story 1) ---------------------------------------
    def valuations(
        self, *, sort: str = "value_gap", order: str = "desc", limit: int = 25
    ) -> dict[str, Any]:
        return self._get(
            "/v1/valuations", {"sort": sort, "order": order, "limit": limit}
        )

    def valuation(self, player_id: int) -> dict[str, Any]:
        return self._get(f"/v1/players/{player_id}/valuation")

    def explanation(self, player_id: int) -> dict[str, Any]:
        return self._get(f"/v1/players/{player_id}/valuation/explanation")

    # --- graph (talent flow) ----------------------------------------------
    def graph_clubs(
        self, *, sort: str = "value_exported", limit: int = 20
    ) -> dict[str, Any]:
        return self._get("/v1/graph/clubs", {"sort": sort, "limit": limit})

    def nation_concentration(self, nation_id: int, *, top: int = 10) -> dict[str, Any]:
        return self._get(
            f"/v1/graph/nations/{nation_id}/supply-concentration", {"top": top}
        )

    def teams(self, *, limit: int = 100) -> dict[str, Any]:
        return self._get("/v1/teams", {"limit": limit})

    # --- analyst (RAG, story 3) -------------------------------------------
    def ask(self, question: str) -> dict[str, Any]:
        try:
            response = self._client.post(
                "/v1/analyst/ask", json={"question": question}
            )
        except httpx.HTTPError as exc:
            msg = f"analyst request failed: {exc}"
            raise ApiError(msg) from exc
        return self._unwrap(response)

    def close(self) -> None:
        self._client.close()


def _safe_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(body, dict):
        return str(body.get("detail", body))
    return str(body)
