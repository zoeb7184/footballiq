"""API-key authentication (backend design §5): hashed storage,
constant-time comparison, default-deny.

Clients send `X-API-Key: <key>`; the server stores only sha256 hashes
(FIQ_API_KEY_HASHES, comma-separated). No configured hashes ⇒ every
request is rejected — the API never defaults open.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Annotated

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    request: Request,
    api_key: Annotated[str | None, Security(_scheme)],
) -> None:
    """Dependency guarding all /v1 routers. System endpoints stay open."""
    if api_key is None:
        raise HTTPException(status_code=401, detail="missing API key (X-API-Key header)")
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    hashes: tuple[str, ...] = request.app.state.settings.api_key_hashes
    if not any(hmac.compare_digest(digest, known) for known in hashes):
        raise HTTPException(status_code=401, detail="invalid API key")
