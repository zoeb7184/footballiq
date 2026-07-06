"""Portal API client tests (xai-design §5) — httpx MockTransport, no server.

Proves the portal talks to the API only: right paths, API-key header, params,
JSON parsing, and error surfacing. No warehouse access exists to test.
"""

import json

import httpx
import pytest

from portal.api_client import ApiClient, ApiError


def _client(handler: object) -> ApiClient:
    http = httpx.Client(
        base_url="http://test",
        headers={"X-API-Key": "k"},
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
    )
    return ApiClient(client=http)


def test_valuations_sends_params_and_api_key() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("X-API-Key", "")
        return httpx.Response(200, json={"items": [], "total": 0})

    body = _client(handler).valuations(sort="value_gap", limit=5)
    assert body["total"] == 0
    assert "/v1/valuations" in seen["url"]
    assert "sort=value_gap" in seen["url"] and "limit=5" in seen["url"]
    assert seen["key"] == "k"


def test_explanation_path_includes_player_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/players/517/valuation/explanation"
        return httpx.Response(200, json={"contributions": []})

    assert _client(handler).explanation(517) == {"contributions": []}


def test_ask_posts_question_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        payload = json.loads(request.content)
        return httpx.Response(200, json={"question": payload["question"],
                                         "route": "kpi", "grounded": True})

    body = _client(handler).ask("total squad value?")
    assert body["question"] == "total squad value?" and body["grounded"] is True


def test_non_success_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # noqa: ARG001
        return httpx.Response(404, json={"detail": "player 999 not found"})

    with pytest.raises(ApiError, match="404"):
        _client(handler).valuation(999)
