from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path

import pytest
import yaml
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.services.dead_letter_service import DeadLetterService
from app.services.event_bus import EventBus, EventEnvelope
from app.services.state_store import reset_state
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

ADDENDUM_PATH = Path("specs/003-rubric-gap-closure/contracts/openapi-addendum.yaml")


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


def _dead_letter_validator() -> Draft202012Validator:
    addendum = yaml.safe_load(ADDENDUM_PATH.read_text(encoding="utf-8"))
    schema = addendum["components"]["schemas"]["DeadLetterEntry"]
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


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


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_state()


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


def _assert_uuid(value: str) -> None:
    assert str(uuid.UUID(value)) == value


def test_dead_letters_list_defaults_to_pending_and_is_camel_case(client: TestClient) -> None:
    pending_entry_id = _seed_dead_letter(tenant_id="live", incident_id="incident-1", correlation_id="corr-1")
    replay_entry_id = _seed_dead_letter(tenant_id="live", incident_id="incident-2", correlation_id="corr-2")

    response = client.post(
        f"/api/dead-letters/{replay_entry_id}/resolve",
        json={"resolution": "replayed", "resolvedByPersonaId": "persona-live"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200

    list_response = client.get("/api/dead-letters", headers=_auth_headers())
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["entryId"] == pending_entry_id
    assert "entry_id" not in payload["items"][0]


def test_dead_letter_resolve_response_matches_addendum_schema(client: TestClient) -> None:
    validator = _dead_letter_validator()
    entry_id = _seed_dead_letter(tenant_id="live", incident_id="incident-3", correlation_id="corr-3")

    response = client.post(
        f"/api/dead-letters/{entry_id}/resolve",
        json={"resolution": "discarded", "resolvedByPersonaId": "persona-live"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    validator.validate(body)
    assert body["entryId"] == entry_id
    assert body["attemptCount"] >= 1


def test_dead_letter_query_rejects_invalid_enum_and_unknown_filter(client: TestClient) -> None:
    invalid_enum = client.get("/api/dead-letters?resolution=invalid", headers=_auth_headers())
    assert invalid_enum.status_code == 422
    _assert_uuid(invalid_enum.json()["correlationId"])

    unknown_filter = client.get("/api/dead-letters?unknownFilter=1", headers=_auth_headers())
    assert unknown_filter.status_code == 422
    _assert_uuid(unknown_filter.json()["correlationId"])


def test_dead_letter_paging_uses_limit_and_offset(client: TestClient) -> None:
    _seed_dead_letter(tenant_id="live", incident_id="incident-10", correlation_id="corr-10")
    _seed_dead_letter(tenant_id="live", incident_id="incident-11", correlation_id="corr-11")

    response = client.get("/api/dead-letters?limit=1&offset=1", headers=_auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1


def test_addendum_declares_api_server_prefix() -> None:
    addendum = yaml.safe_load(ADDENDUM_PATH.read_text(encoding="utf-8"))
    servers = addendum.get("servers", [])
    assert any(server.get("url") == "/api" for server in servers)


def test_dead_letters_openapi_has_one_get_operation(client: TestClient) -> None:
    spec = client.app.openapi()
    dead_letters = spec["paths"]["/api/dead-letters"]
    assert set(dead_letters.keys()) == {"get"}


def test_handoff_records_include_contract_fields(client: TestClient) -> None:
    bus = EventBus()

    def _subscriber(_envelope: EventEnvelope) -> None:
        return None

    bus.subscribe("handoff", _subscriber)
    bus.publish(
        EventEnvelope(
            channel="handoff",
            scope_key="live:incident-4",
            payload={
                "handoffId": "handoff-contract-1",
                "incidentId": "incident-4",
                "sourceAgent": "monitoring",
                "targetAgent": "risk_assessment",
                "confidence": 0.9,
                "payload": {"signalId": "sig-1"},
                "attemptCount": 1,
                "retryCount": 0,
            },
        )
    )

    response = client.get("/api/incidents/incident-4/handoffs", headers=_auth_headers())
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 1
    assert records[0]["confidence"] == pytest.approx(0.9)
    assert records[0]["attemptCount"] == 1
    assert records[0]["retryCount"] == 0
    assert records[0]["timelineEventId"]
    assert "payloadSummary" in records[0]


def test_handoff_status_filter_returns_failed_entries_with_dead_letter_id(client: TestClient) -> None:
    bus = EventBus(dead_letter_service=DeadLetterService())

    def _failing_subscriber(_envelope: EventEnvelope) -> None:
        raise RuntimeError("subscriber failure")

    bus.subscribe("handoff", _failing_subscriber)
    bus.publish(
        EventEnvelope(
            channel="handoff",
            scope_key="live:incident-5",
            payload={
                "handoffId": "handoff-contract-fail-1",
                "incidentId": "incident-5",
                "sourceAgent": "monitoring",
                "targetAgent": "risk_assessment",
                "confidence": 0.8,
                "attemptCount": 3,
                "retryCount": 2,
            },
        )
    )

    response = client.get("/api/incidents/incident-5/handoffs?status=failed", headers=_auth_headers())
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 1
    assert records[0]["status"] == "failed"
    assert records[0]["deadLetterEntryId"]
    assert records[0]["timelineEventId"]
