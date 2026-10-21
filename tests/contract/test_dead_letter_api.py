"""Contract tests for dead-letter API endpoints (T023-T024)."""

from __future__ import annotations

import base64
import json

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.services.dead_letter_service import DeadLetterService
from app.services.state_store import HANDOFF_EVENTS, reset_state
from fastapi.testclient import TestClient


@pytest.fixture
def _env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("MANAGEMENT_API_KEY", "test-key")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")


@pytest.fixture
def client(_env):
    from app.main import app

    return TestClient(app)


def _auth_headers(persona_id: str = "persona-live") -> dict[str, str]:
    claims = {
        "sub": "user-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": ["incident-commander"],
        "persona_id": persona_id,
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def _seed_dead_letter(*, tenant_id: str, incident_id: str, correlation_id: str) -> str:
    token = set_current_tenant(
        TenantContext(
            agency_id="ses-nsw",
            jurisdiction_ids=("nsw",),
            persona_id="persona-seed",
            tenant_id=tenant_id,
        )
    )
    try:
        entry = DeadLetterService().create_entry(
            entry_type="event_delivery_failure",
            correlation_id=correlation_id,
            original_payload={"incidentId": incident_id},
            failure_reason="seed",
            failure_code="DELIVERY_FAILED",
            source_service="test",
            target_service="test-target",
            tenant_scope_key=tenant_id,
            incident_id=incident_id,
        )
    finally:
        reset_current_tenant(token)
    return entry.entry_id


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_state()


class TestDeadLetterEndpoints:
    """Contract: /api/dead-letters and /api/incidents/{incident_id}/handoffs are tenant-scoped and authenticated."""

    def test_list_dead_letters_requires_authenticated_persona(self, client):
        response = client.get(
            "/api/dead-letters",
        )
        assert response.status_code == 401

    def test_list_dead_letters_returns_tenant_local_total(self, client):
        _seed_dead_letter(tenant_id="live", incident_id="incident-shared", correlation_id="corr-live")
        _seed_dead_letter(tenant_id="sim-other", incident_id="incident-shared", correlation_id="corr-other")

        response = client.get("/api/dead-letters", headers=_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["correlationId"] == "corr-live"

    def test_resolve_dead_letter_rejects_forged_persona(self, client):
        entry_id = _seed_dead_letter(tenant_id="live", incident_id="incident-1", correlation_id="corr-1")

        response = client.post(
            f"/api/dead-letters/{entry_id}/resolve",
            json={"resolution": "replayed", "resolvedByPersonaId": "persona-forged"},
            headers=_auth_headers(persona_id="persona-live"),
        )
        assert response.status_code == 403

    def test_resolve_dead_letter_blocks_cross_tenant_entry_ids(self, client):
        entry_id = _seed_dead_letter(tenant_id="sim-tenant-b", incident_id="incident-2", correlation_id="corr-b")

        response = client.post(
            f"/api/dead-letters/{entry_id}/resolve",
            json={"resolution": "discarded", "resolvedByPersonaId": "persona-live"},
            headers=_auth_headers(persona_id="persona-live"),
        )
        assert response.status_code == 404

    def test_resolve_dead_letter_succeeds_for_own_tenant(self, client):
        entry_id = _seed_dead_letter(tenant_id="live", incident_id="incident-3", correlation_id="corr-3")

        response = client.post(
            f"/api/dead-letters/{entry_id}/resolve",
            json={"resolution": "escalated", "resolvedByPersonaId": "persona-live"},
            headers=_auth_headers(persona_id="persona-live"),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["entryId"] == entry_id
        assert body["resolution"] == "escalated"
        assert body["reviewedBy"] == "persona-live"


class TestHandoffEndpoints:
    def test_handoff_list_requires_authenticated_persona(self, client):
        response = client.get("/api/incidents/incident-h-1/handoffs")
        assert response.status_code == 401

    def test_handoff_list_is_tenant_scoped(self, client):
        live_token = set_current_tenant(
            TenantContext(
                agency_id="ses-nsw",
                jurisdiction_ids=("nsw",),
                persona_id="persona-seed",
                tenant_id="live",
            )
        )
        try:
            HANDOFF_EVENTS["incident-h-2"] = [
                {
                    "handoffId": "h-live-1",
                    "incidentId": "incident-h-2",
                    "status": "delivered",
                }
            ]
        finally:
            reset_current_tenant(live_token)

        other_token = set_current_tenant(
            TenantContext(
                agency_id="ses-qld",
                jurisdiction_ids=("qld",),
                persona_id="persona-seed",
                tenant_id="sim-tenant-z",
            )
        )
        try:
            HANDOFF_EVENTS["incident-h-2"] = [
                {
                    "handoffId": "h-other-1",
                    "incidentId": "incident-h-2",
                    "status": "dead_lettered",
                }
            ]
        finally:
            reset_current_tenant(other_token)

        response = client.get(
            "/api/incidents/incident-h-2/handoffs",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["handoffId"] == "h-live-1"
