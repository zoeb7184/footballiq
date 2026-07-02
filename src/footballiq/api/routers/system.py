"""System endpoints: liveness and readiness (backend design §5).

Unauthenticated by design — orchestrator probes must reach them.
/ready refuses to be ready without data: an empty platform reports itself
unfit instead of serving empty shortlists.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

import footballiq
from footballiq.application.ports import ReadinessProbe

router = APIRouter(tags=["system"])


def get_probe(request: Request) -> ReadinessProbe:
    probe: ReadinessProbe = request.app.state.probe
    return probe


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "alive", "version": footballiq.__version__}


@router.get("/ready")
def ready(
    probe: Annotated[ReadinessProbe, Depends(get_probe)],
    response: Response,
) -> dict[str, object]:
    """Readiness: the platform can actually serve (warehouse + data)."""
    report = probe.check()
    if not report.ready:
        response.status_code = 503
    return {
        "status": "ready" if report.ready else "not_ready",
        "failures": list(report.failures),
        "version": footballiq.__version__,
    }
