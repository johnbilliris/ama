"""Simulation-scoped metrics carrying the ``tenant_id`` dimension (spec 007 AUD-027).

Every instrument emitted here is filtered per tenant by the shared Application
Insights dashboards and alerts, so the dimension is mandatory rather than
best-effort. Tenant resolution falls back to ``unknown`` — never ``live`` — when
background work runs without an explicit scope.
"""

from __future__ import annotations

from typing import Any

from app.observability.metrics import emit_counter, emit_histogram
from app.observability.tenant_telemetry import UNKNOWN_TENANT, current_tenant_id

WRITE_ADMISSIONS = "simulation.write_admissions"
SCHEDULER_DELIVERIES = "simulation.scheduler_deliveries"
SCHEDULER_DELIVERY_LAG = "simulation.scheduler_delivery_lag_seconds"


def tenant_attributes(tenant_id: str | None = None, **extra: Any) -> dict[str, Any]:
    resolved = (tenant_id or "").strip() or current_tenant_id(default=UNKNOWN_TENANT)
    return {"tenant_id": resolved, **extra}


def record_write_admission(tenant_id: str, decision: str, reason: str) -> None:
    emit_counter(WRITE_ADMISSIONS, 1, tenant_attributes(tenant_id, decision=decision, reason=reason))


def record_scheduler_delivery(tenant_id: str, outcome: str, lag_seconds: float | None = None) -> None:
    emit_counter(SCHEDULER_DELIVERIES, 1, tenant_attributes(tenant_id, outcome=outcome))
    if lag_seconds is not None:
        emit_histogram(
            SCHEDULER_DELIVERY_LAG,
            float(lag_seconds),
            tenant_attributes(tenant_id),
            unit="s",
        )
