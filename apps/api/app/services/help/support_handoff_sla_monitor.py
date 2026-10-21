"""spec-038 T-AA057 — support-handoff SLA monitor (FR-023a/b)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from ama_domain import SupportHandoffRecord
from app.observability.audit import emit_audit_event


class OpenHandoff(TypedDict):
    handoff_id: str
    tenant_id: str
    opened_at: datetime
    record: SupportHandoffRecord


def sla_for(record: SupportHandoffRecord, *, incident_mode: bool) -> timedelta:
    """FR-023b — 5 min in incident mode, 4 h otherwise."""
    if incident_mode:
        return timedelta(minutes=record.sla_incident_minutes)
    return timedelta(hours=record.sla_routine_business_hours)


def check_open_handoffs(
    open_handoffs: Iterable[OpenHandoff],
    *,
    incident_mode: bool,
    now: datetime | None = None,
) -> list[str]:
    """Emit ``audit.support_handoff_unack_timeout`` for any breached handoff.

    ``open_handoffs`` is an iterable of dicts with at least ``handoff_id``,
    ``tenant_id``, ``opened_at``, ``record`` (SupportHandoffRecord).
    Returns the list of breached handoff ids.
    """
    now = now or datetime.now(UTC)
    breached: list[str] = []
    for h in open_handoffs:
        rec: SupportHandoffRecord = h["record"]
        deadline = h["opened_at"] + sla_for(rec, incident_mode=incident_mode)
        if now > deadline:
            breached.append(h["handoff_id"])
            emit_audit_event(
                "audit.support_handoff_unack_timeout",
                {
                    "handoff_id": h["handoff_id"],
                    "tenant_id": h["tenant_id"],
                    "incident_mode": incident_mode,
                    "deadline": deadline.isoformat(),
                },
            )
    return breached


__all__ = ["check_open_handoffs", "sla_for"]
