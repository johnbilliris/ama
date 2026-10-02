from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.main import create_app
from app.services.state_store import reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.signal import Signal


@pytest.fixture(autouse=True)
def _auth_context(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    token = set_current_tenant(TenantContext(agency_id="ses-nsw", jurisdiction_ids=("nsw",), tenant_id="live"))
    try:
        yield
    finally:
        reset_current_tenant(token)


def _auth_headers() -> dict[str, str]:
    claims = {
        "sub": "user-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": ["incident-commander"],
        "persona_id": "persona-incident-commander",
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def _seed_source(client: TestClient) -> str:
    source = client.app.state.governance_registry.register_source(
        DataSource(
            data_source_id="ds-aud044",
            name="AUD044 Source",
            kind="authoritative",
            sub_category="weather_climate",
            provider="Test Provider",
            collection_method="api_pull",
            data_type="json",
            update_frequency="5_minutes",
            trust_tier="tier_1_authoritative_government",
            geographic_coverage="nsw",
        ),
        actor_id="test-suite",
    )
    return source.data_source_id


def _seed_signal(client: TestClient, *, signal_id: str, occurred_at: datetime, source_id: str) -> None:
    from app.services.operational_store import OperationalStore

    op_store = OperationalStore("live")
    op_store.signals.put(
        signal_id,
        Signal(
            signal_id=signal_id,
            incident_id="incident-aud044",
            data_source_id=source_id,
            category="weather",
            occurred_at=occurred_at,
            received_at=occurred_at,
            jurisdiction_id="nsw",
            location={"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
            payload={"warning": signal_id},
            owning_agency_id="ses-nsw",
            classification="official",
            pii_fields=[],
            retention_until=occurred_at + timedelta(minutes=30),
            confidence_score=0.9,
            freshness_score=0.9,
            validation_status="validated",
            provenance={"collectionMethod": "api", "sourceUri": "https://example.gov.au", "collector": "user-001"},
        ),
    )


def test_list_signals_supports_naive_since_and_returns_deterministic_order() -> None:
    reset_state()
    client = TestClient(create_app())
    source_id = _seed_source(client)

    at = datetime.now(UTC).replace(microsecond=0)
    _seed_signal(client, signal_id="sig-b", occurred_at=at, source_id=source_id)
    _seed_signal(client, signal_id="sig-a", occurred_at=at, source_id=source_id)

    response = client.get(
        f"/api/signals?since={at.strftime('%Y-%m-%dT%H:%M:%S')}&validationStatus=validated&limit=2&offset=0",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [item["signal_id"] for item in payload["items"]] == ["sig-b", "sig-a"]


def test_list_signals_rejects_invalid_query_parameters_with_422_and_no_mutation() -> None:
    reset_state()
    client = TestClient(create_app())
    source_id = _seed_source(client)
    _seed_signal(
        client,
        signal_id="sig-stable",
        occurred_at=datetime(2026, 3, 9, 0, 0, 0, tzinfo=UTC),
        source_id=source_id,
    )

    from app.services.operational_store import OperationalStore

    before = len(OperationalStore.current().signals.values())

    bad_queries = [
        "/api/signals?validationStatus=bogus",
        "/api/signals?since=not-a-date",
        "/api/signals?limit=1001",
        "/api/signals?offset=-1",
    ]

    for query in bad_queries:
        response = client.get(query, headers=_auth_headers())
        assert response.status_code == 422

    after = len(OperationalStore.current().signals.values())
    assert after == before
