"""Pillar F — Signal ingest (T-F05, FR-023/024/029)."""

from __future__ import annotations

from typing import Any

from .._clients import get_registry
from .._guards import assert_au_region
from . import audit_manager


def ingest_signal(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a signal row enforcing AU-region guard + audit emission."""
    assert_au_region(payload)  # raises NonAuRegionError on non-AU
    container = get_registry().get("kpi_signals")
    container.create_item(payload)
    audit_manager.record(
        kind="signal_ingested",
        value_id=payload["id"],
        actor=payload.get("actor", "system"),
        references={"signal": payload["id"]},
        payload={
            "kpi_id": payload.get("kpi_id"),
            "scenario_id": payload.get("scenario_id"),
        },
        correlation_id=payload.get("correlation_id", ""),
    )
    return payload


def enter_degraded_mode(*, value_id: str, reason: str, correlation_id: str = "") -> None:
    """FR-027 / FR-032 — record a degraded-mode entry."""
    audit_manager.record(
        kind="degraded_mode_entered",
        value_id=value_id,
        actor="system",
        payload={"reason": reason},
        correlation_id=correlation_id,
    )
