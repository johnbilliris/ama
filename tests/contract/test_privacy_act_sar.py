"""Contract: Privacy Act 1988 SAR endpoint (T204).

Per FR-RAG-COMP-01 + Plan §F-A6.2 — ``GET /api/audit/sar?subject=<id>``
returns audit events filtered to subject; the response payload MUST
surface APP 1/3/5/6/11 metadata.

Proves: T206 — apps/api/app/api/routes/audit_compliance.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from apps.api.app.api.routes.audit_compliance import _APP_SURFACES, _sar_payload


def _stub_event(*, subject: str, ts: str, action: str) -> dict[str, Any]:
    return {
        "actor_id": subject,
        "timestamp": ts,
        "event_type": action,
        "resource": "incident-001",
        "outcome": "success",
        "justification": "operator action",
    }


def test_sar_payload_surfaces_app1() -> None:
    payload = _sar_payload("op-1", events=[])
    assert "APP1" in payload["privacy_act_app_surfaces"]
    assert "Privacy notice" in payload["privacy_act_app_surfaces"]["APP1"]


def test_sar_payload_surfaces_app3() -> None:
    payload = _sar_payload("op-1", events=[])
    assert "APP3" in payload["privacy_act_app_surfaces"]
    assert "Collection limit" in payload["privacy_act_app_surfaces"]["APP3"]


def test_sar_payload_surfaces_app5() -> None:
    payload = _sar_payload("op-1", events=[])
    assert "APP5" in payload["privacy_act_app_surfaces"]
    assert "Notification of collection" in payload["privacy_act_app_surfaces"]["APP5"]


def test_sar_payload_surfaces_app6() -> None:
    payload = _sar_payload("op-1", events=[])
    assert "APP6" in payload["privacy_act_app_surfaces"]
    assert "Use & disclosure" in payload["privacy_act_app_surfaces"]["APP6"]


def test_sar_payload_surfaces_app11() -> None:
    payload = _sar_payload("op-1", events=[])
    assert "APP11" in payload["privacy_act_app_surfaces"]
    assert "Security & retention" in payload["privacy_act_app_surfaces"]["APP11"]
    assert "7-year" in payload["privacy_act_app_surfaces"]["APP11"]


def test_sar_payload_event_count_matches_events_list() -> None:
    events = [
        _stub_event(subject="op-1", ts="2026-06-01T00:00:00Z", action="read"),
        _stub_event(subject="op-1", ts="2026-06-02T00:00:00Z", action="write"),
    ]
    payload = _sar_payload("op-1", events=events)
    assert payload["event_count"] == 2
    assert payload["events"] == events
    assert payload["subject"] == "op-1"


def test_sar_payload_includes_retention_policy() -> None:
    payload = _sar_payload("op-1", events=[])
    retention = payload["retention_policy"]
    assert retention["retention_period_years"] == 7
    assert "spec-030" in retention["policy_ref"]


def test_sar_payload_generated_at_iso8601() -> None:
    payload = _sar_payload("op-1", events=[])
    # Must round-trip
    dt = datetime.fromisoformat(payload["generated_at"])
    assert dt.tzinfo is not None


def test_app_surfaces_constant_has_all_five_apps() -> None:
    """The constant MUST contain exactly APP 1, 3, 5, 6, 11."""
    assert set(_APP_SURFACES.keys()) == {"APP1", "APP3", "APP5", "APP6", "APP11"}
