"""Contract: Privacy Act 1988 SAR endpoint (T204).

Per FR-RAG-COMP-01 + Plan §F-A6.2 — ``GET /api/audit/sar?subject=<id>``
returns audit events filtered to subject; the response payload MUST
surface APP 1/3/5/6/11 metadata.

Proves: T206 — apps/api/app/api/routes/audit_compliance.py.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any

import pytest
from app.main import create_app
from fastapi.testclient import TestClient

from apps.api.app.api.routes.audit_compliance import _APP_SURFACES, _sar_payload


def _principal_headers(principal: dict[str, Any]) -> dict[str, str]:
    encoded = base64.b64encode(json.dumps(principal).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


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


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
    return TestClient(create_app())


def test_sar_allows_subject_self_access(client, monkeypatch) -> None:
    class _Repo:
        def fetch_for_subject(self, subject: str):
            return [{"subject": subject, "retention_until": "2099-01-01T00:00:00Z"}]

    monkeypatch.setattr("app.api.routes.audit_compliance._audit_query_callable", lambda: _Repo())
    response = client.get(
        "/api/audit/sar",
        params={"subject": "user-1"},
        headers=_principal_headers({"sub": "user-1", "roles": ["operator"]}),
    )
    assert response.status_code == 200
    assert response.json()["event_count"] == 1


def test_sar_requires_privacy_role_for_third_party_subject(client, monkeypatch) -> None:
    class _Repo:
        def fetch_for_subject(self, subject: str):
            return [{"subject": subject, "retention_until": "2099-01-01T00:00:00Z"}]

    monkeypatch.setattr("app.api.routes.audit_compliance._audit_query_callable", lambda: _Repo())
    response = client.get(
        "/api/audit/sar",
        params={"subject": "user-2"},
        headers=_principal_headers({"sub": "user-1", "roles": ["operator"]}),
    )
    assert response.status_code == 403


def test_sar_privacy_officer_can_read_third_party_subject(client, monkeypatch) -> None:
    class _Repo:
        def fetch_for_subject(self, subject: str):
            return [{"subject": subject, "retention_until": "2099-01-01T00:00:00Z"}]

    monkeypatch.setattr("app.api.routes.audit_compliance._audit_query_callable", lambda: _Repo())
    response = client.get(
        "/api/audit/sar",
        params={"subject": "user-2"},
        headers=_principal_headers({"sub": "user-1", "roles": ["privacy-officer"]}),
    )
    assert response.status_code == 200
    assert response.json()["event_count"] == 1


def test_sar_backend_failure_returns_503(client, monkeypatch) -> None:
    def _explode():
        raise RuntimeError("db unavailable")

    monkeypatch.setattr("app.api.routes.audit_compliance._audit_query_callable", _explode)
    response = client.get(
        "/api/audit/sar",
        params={"subject": "user-1"},
        headers=_principal_headers({"sub": "user-1", "roles": ["operator"]}),
    )
    assert response.status_code == 503


def test_sar_retention_filter_excludes_expired_event(client, monkeypatch) -> None:
    class _Repo:
        def fetch_for_subject(self, subject: str):
            return [
                {"subject": subject, "retention_until": "2000-01-01T00:00:00Z"},
                {"subject": subject, "retention_until": "2099-01-01T00:00:00Z"},
            ]

    monkeypatch.setattr("app.api.routes.audit_compliance._audit_query_callable", lambda: _Repo())
    response = client.get(
        "/api/audit/sar",
        params={"subject": "user-1"},
        headers=_principal_headers({"sub": "user-1", "roles": ["operator"]}),
    )
    assert response.status_code == 200
    assert response.json()["event_count"] == 1


def test_erasure_request_idempotent_and_has_30_day_sla(client) -> None:
    headers = _principal_headers({"sub": "user-1", "roles": ["operator"]})
    body = {
        "subject": "user-1",
        "legal_hold": False,
        "reason": "privacy request",
        "idempotency_key": "idem-key-123456",
    }
    first = client.post("/api/audit/erasure-requests", json=body, headers=headers)
    second = client.post("/api/audit/erasure-requests", json=body, headers=headers)
    assert first.status_code == 202
    assert second.status_code == 202
    first_json = first.json()
    second_json = second.json()
    assert first_json["request_id"] == second_json["request_id"]
    due = datetime.fromisoformat(first_json["due_by"])
    submitted = datetime.fromisoformat(first_json["submitted_at"])
    assert (due - submitted).days == 30


def test_erasure_request_legal_hold_outcome(client) -> None:
    headers = _principal_headers({"sub": "user-1", "roles": ["operator"]})
    response = client.post(
        "/api/audit/erasure-requests",
        json={
            "subject": "user-1",
            "legal_hold": True,
            "reason": "hold",
            "idempotency_key": "idem-key-legalhold",
        },
        headers=headers,
    )
    assert response.status_code == 202
    assert response.json()["status"] == "legal_hold"
