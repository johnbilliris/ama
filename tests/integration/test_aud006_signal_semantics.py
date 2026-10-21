from uuid import uuid4

import pytest
from app.api.dependencies.governance_composition import get_governance_composition
from app.main import create_app
from app.services.operational_store import OperationalStore
from app.services.state_store import reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.data_source import DataSource


@pytest.fixture(autouse=True)
def _clean_state_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)


def _register_source(client: TestClient, kind: str, trust_tier: str) -> DataSource:
    source = DataSource(
        data_source_id=f"ds-{kind}-{uuid4().hex[:8]}",
        name=f"{kind}-source",
        kind=kind,
        trust_tier=trust_tier,
    )
    registry = get_governance_composition(client.app).registry
    return registry.register_source(source, actor_id="test-suite")


def _payload(source_id: str, kind: str) -> dict[str, object]:
    return {
        "source": {"dataSourceId": source_id, "name": "test", "kind": kind},
        "incidentId": "incident-006",
        "category": "weather",
        "occurredAt": "2026-03-09T00:00:00+00:00",
        "receivedAt": "2026-03-09T00:01:00+00:00",
        "jurisdictionId": "nsw",
        "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        "payload": {"warning": "storm"},
        "confidenceScore": 0.9,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {"sourceUri": "https://example.test/signal", "collectionMethod": "api"},
    }


def test_aud006_rejects_source_kind_spoofing() -> None:
    app = create_app()
    client = TestClient(app)
    source = _register_source(client, "authoritative", "tier_1_authoritative_government")
    payload = _payload(source.data_source_id, "community")

    response = client.post("/api/signals", json=payload)

    assert response.status_code == 403


def test_aud006_rejects_community_validated_self_assertion() -> None:
    app = create_app()
    client = TestClient(app)
    source = _register_source(client, "community", "tier_5_community_volunteer")
    payload = _payload(source.data_source_id, "community")

    response = client.post("/api/signals", json=payload)

    assert response.status_code == 403


def test_aud006_rejects_unassociated_signal_without_explicit_unassigned_path() -> None:
    app = create_app()
    client = TestClient(app)
    source = _register_source(client, "authoritative", "tier_1_authoritative_government")
    payload = _payload(source.data_source_id, "authoritative")
    payload.pop("incidentId")

    response = client.post("/api/signals", json=payload)

    assert response.status_code == 422
    store = OperationalStore.current()
    assert len(store.incidents.values()) == 0
    assert len(store.signals.values()) == 0


def test_aud006_accepts_explicit_unassigned_path() -> None:
    app = create_app()
    client = TestClient(app)
    source = _register_source(client, "authoritative", "tier_1_authoritative_government")
    payload = _payload(source.data_source_id, "authoritative")
    payload.pop("incidentId")
    payload["payload"] = {"warning": "storm", "allowUnassignedIncident": True}

    response = client.post("/api/signals", json=payload)

    assert response.status_code == 202
    store = OperationalStore.current()
    stored_signals = store.signals.values()
    assert len(stored_signals) == 1
    assert str(stored_signals[0].incident_id).startswith("unassigned-")
