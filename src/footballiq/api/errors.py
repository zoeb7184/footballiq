"""RFC 7807 problem+json error handling (backend design §5)."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_MEDIA_TYPE = "application/problem+json"


def _problem(status: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type=_MEDIA_TYPE,
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "correlation_id": str(uuid.uuid4()),
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Install problem+json handlers for HTTP, validation, and unexpected errors."""

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(exc.status_code, exc.detail or "HTTP error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem(422, "Validation failed", str(exc.errors()[:3]))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        # Opaque by design: detail stays server-side, correlation id goes out.
        return _problem(500, "Internal server error", "unexpected error (see logs)")
