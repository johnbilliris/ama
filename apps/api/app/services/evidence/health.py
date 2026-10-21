from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from ._clients import EvidenceClientRegistry, get_registry

router = APIRouter(tags=["evidence-health"])


class HealthReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded", "down"]
    checks: dict[str, bool]
    degraded: bool


def build_health_report(
    registry: EvidenceClientRegistry | None = None,
) -> tuple[int, HealthReport]:
    clients = registry or get_registry()
    cosmos_checks = clients.health()
    checks = {
        **cosmos_checks,
        "evidence_audit_cold_blob": _probe_blob(clients),
        "audit_change_feed_mirror": _probe_mirror(clients),
        "app_insights_ingestion": (
            clients.telemetry_configured and bool(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))
        ),
    }
    critical_names = {
        *clients.CONTAINER_NAMES,
        "evidence_audit_cold_blob",
        "audit_change_feed_mirror",
    }
    critical_ok = all(checks.get(name, False) for name in critical_names)
    noncritical_ok = checks["app_insights_ingestion"]

    if not critical_ok:
        return 503, HealthReport(
            status="down",
            checks=checks,
            degraded=True,
        )
    if not noncritical_ok:
        return 200, HealthReport(
            status="degraded",
            checks=checks,
            degraded=True,
        )
    return 200, HealthReport(
        status="ok",
        checks=checks,
        degraded=False,
    )


@router.get(
    "/healthz/evidence",
    response_model=HealthReport,
    operation_id="healthzEvidence",
)
def healthz_evidence() -> JSONResponse:
    status_code, report = build_health_report()
    return JSONResponse(
        status_code=status_code,
        content=report.model_dump(mode="json"),
    )


def _probe_blob(registry: EvidenceClientRegistry) -> bool:
    try:
        return registry.blob_archive.health()
    except Exception:
        return False


def _probe_mirror(registry: EvidenceClientRegistry) -> bool:
    try:
        rows = [
            row
            for row in registry.get("evidence_audit_dlq").all()
            if row.get("kind") in {"audit_mirror_checkpoint", "audit_mirror_heartbeat"}
        ]
    except Exception:
        return False
    if os.environ.get("AMA_TEST_MODE") == "1":
        return True
    if not rows:
        return False
    latest = max(datetime.fromisoformat(str(row["recorded_at"])) for row in rows)
    interval = float(os.environ.get("AUDIT_MIRROR_INTERVAL_S", "5"))
    return datetime.now(UTC) - latest <= timedelta(seconds=max(30.0, interval * 3))
