"""Health endpoints for AIDR services.

Provides /health/aidr aggregate and per-service health checks.
All endpoints must respond within 1 second (NFR target).
"""

from __future__ import annotations

import time

from app.services.state_store import (
    AIIMS_ASSIGNMENTS,
    EVACUATION_STAGES,
    LESSONS,
    PPRR_CONTEXTS,
    RECOVERY_TRACKERS,
)
from fastapi import APIRouter

router = APIRouter(prefix="/health/aidr", tags=["health"])


def _check_service(store: dict, name: str) -> dict:
    """Check a single service store is accessible."""
    start = time.perf_counter()
    try:
        count = len(store)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "service": name,
            "status": "healthy",
            "entity_count": count,
            "response_ms": round(elapsed_ms, 2),
        }
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "service": name,
            "status": "unhealthy",
            "error": str(exc),
            "response_ms": round(elapsed_ms, 2),
        }


@router.get("")
def get_aidr_health():
    """Aggregate health check for all AIDR services."""
    services = [
        _check_service(AIIMS_ASSIGNMENTS, "aiims"),
        _check_service(EVACUATION_STAGES, "evacuation"),
        _check_service(RECOVERY_TRACKERS, "recovery"),
        _check_service(LESSONS, "lessons"),
        _check_service(PPRR_CONTEXTS, "pprr"),
    ]
    overall = (
        "healthy" if all(s["status"] == "healthy" for s in services) else "degraded"
    )
    return {"status": overall, "services": services}


@router.get("/aiims")
def get_aiims_health():
    return _check_service(AIIMS_ASSIGNMENTS, "aiims")


@router.get("/evacuation")
def get_evacuation_health():
    return _check_service(EVACUATION_STAGES, "evacuation")


@router.get("/recovery")
def get_recovery_health():
    return _check_service(RECOVERY_TRACKERS, "recovery")


@router.get("/lessons")
def get_lessons_health():
    return _check_service(LESSONS, "lessons")


@router.get("/pprr")
def get_pprr_health():
    return _check_service(PPRR_CONTEXTS, "pprr")
