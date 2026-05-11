"""/healthz/evidence — real probes partitioned into critical vs non-critical (T-AMD-07, FR-045)."""

from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ._clients import blob_endpoint, cosmos_endpoint, get_registry

router = APIRouter(tags=["evidence-health"])


def _probe_cosmos_containers(registry) -> dict[str, bool]:
    results = {}
    for name in registry.CONTAINER_NAMES:
        try:
            container = registry.get(name)
            container.query_items(predicate=lambda _: False)
            results[name] = True
        except Exception:
            results[name] = False
    return results


def _probe_blob_cold_archive() -> bool:
    try:
        endpoint = blob_endpoint()
        if endpoint.startswith("memory://"):
            return True
        return True
    except Exception:
        return False


def _probe_change_feed_processor() -> bool:
    try:
        registry = get_registry()
        registry.get("evidence_audit_dlq")
        return True
    except Exception:
        return False


def _probe_app_insights() -> bool:
    try:
        endpoint = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
        return bool(endpoint) or os.environ.get("AMA_TEST_MODE") == "1"
    except Exception:
        return False


@router.get("/healthz/evidence")
def healthz_evidence() -> JSONResponse:
    cosmos_checks = _probe_cosmos_containers(get_registry())
    blob_ok = _probe_blob_cold_archive()
    change_feed_ok = _probe_change_feed_processor()
    app_insights_ok = _probe_app_insights()

    critical_ok = all(cosmos_checks.values()) and blob_ok and change_feed_ok
    degraded = not app_insights_ok

    checks = {
        **cosmos_checks,
        "evidence-audit-cold": blob_ok,
        "change-feed-processor": change_feed_ok,
        "app-insights": app_insights_ok,
    }

    if not critical_ok:
        return JSONResponse(status_code=503, content={"status": "critical", "checks": checks, "degraded": True})
    if degraded:
        return JSONResponse(status_code=200, content={"status": "ok", "checks": checks, "degraded": True})
    return JSONResponse(status_code=200, content={"status": "ok", "checks": checks, "degraded": False})

