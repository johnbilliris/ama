"""spec-038 T-AA195 — support handoff SLA breach emits audit, no auto-close."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ama_domain import SupportHandoffRecord
from app.services.help.support_handoff_sla_monitor import check_open_handoffs, sla_for


def _record() -> SupportHandoffRecord:
    now = datetime.now(UTC)
    return SupportHandoffRecord(
        id="shr-1",
        tenant_id="t-1",
        channel_kind="email",
        address="help@example.gov.au",
        created_at=now,
        updated_at=now,
    )


def test_incident_mode_5_min_sla() -> None:
    assert sla_for(_record(), incident_mode=True) == timedelta(minutes=5)


def test_routine_mode_4h_sla() -> None:
    assert sla_for(_record(), incident_mode=False) == timedelta(hours=4)


def test_breach_emits_audit_returns_id() -> None:
    rec = _record()
    opened = datetime.now(UTC) - timedelta(minutes=10)
    open_handoffs = [{"handoff_id": "h-1", "tenant_id": "t-1", "opened_at": opened, "record": rec}]
    breached = check_open_handoffs(open_handoffs, incident_mode=True)
    assert breached == ["h-1"]


def test_within_sla_no_breach() -> None:
    rec = _record()
    opened = datetime.now(UTC) - timedelta(minutes=1)
    open_handoffs = [{"handoff_id": "h-2", "tenant_id": "t-1", "opened_at": opened, "record": rec}]
    breached = check_open_handoffs(open_handoffs, incident_mode=True)
    assert breached == []
