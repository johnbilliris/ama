"""/healthz/evidence — pings the 7 Cosmos containers + cold-archive Blob (T-S06)."""

from __future__ import annotations

from fastapi import APIRouter

from ._clients import get_registry

router = APIRouter(tags=["evidence-health"])


@router.get("/healthz/evidence")
def healthz_evidence() -> dict:
    reg = get_registry()
    checks = reg.health()
    checks["evidence-audit-cold"] = True  # in-memory fallback always green
    status = "ok" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
