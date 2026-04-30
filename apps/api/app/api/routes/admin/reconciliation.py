"""Daily reconciliation job (T058, SC-004)."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def reconcile(
    *,
    expected_invocations: int,
    audit_count: int,
    span_count: int,
    window_hours: int = 24,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    audit_gap = expected_invocations - audit_count
    span_gap = expected_invocations - span_count
    has_gap = audit_gap != 0 or span_gap != 0
    correlation_id = correlation_id or uuid.uuid4().hex
    now = _now()
    report = {
        "id": correlation_id,
        "window_hours": window_hours,
        "ended_at": now.isoformat(),
        "started_at": (now - timedelta(hours=window_hours)).isoformat(),
        "expected_invocations": expected_invocations,
        "audit_count": audit_count,
        "span_count": span_count,
        "audit_gap": audit_gap,
        "span_gap": span_gap,
        "has_gap": has_gap,
        "outcome": "fail" if has_gap else "pass",
    }
    if has_gap:
        logger.error(
            "reconciliation.gap correlation_id=%s audit_gap=%d span_gap=%d",
            correlation_id,
            audit_gap,
            span_gap,
        )
    else:
        logger.info(
            "reconciliation.ok correlation_id=%s checks=%d",
            correlation_id,
            expected_invocations,
        )
    return report


def emit_metric(report: dict[str, Any]) -> None:
    try:
        from opentelemetry import metrics

        meter = metrics.get_meter("ama.maf_runtime.reconciliation")
        gauge = meter.create_gauge(
            "reconciliation.gap",
            description="Gap between expected agent invocations and audit/span counts (SC-004)",
            unit="1",
        )
        gauge.set(int(report["audit_gap"]), {"kind": "audit", "window_hours": str(report["window_hours"])})
        gauge.set(int(report["span_gap"]), {"kind": "span", "window_hours": str(report["window_hours"])})
    except Exception:  # noqa: BLE001
        logger.debug("reconciliation: metric emit failed; ignoring", exc_info=True)


def run_daily_reconciliation() -> dict[str, Any]:
    expected = int(os.environ.get("RECONCILIATION_EXPECTED_INVOCATIONS", "0"))
    audit = int(os.environ.get("RECONCILIATION_AUDIT_COUNT", "0"))
    spans = int(os.environ.get("RECONCILIATION_SPAN_COUNT", "0"))
    report = reconcile(expected_invocations=expected, audit_count=audit, span_count=spans)
    emit_metric(report)
    return report


__all__ = ["reconcile", "run_daily_reconciliation", "emit_metric"]
