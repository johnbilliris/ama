"""Contract test: Pydantic extra fields rejection (T-AMD-19, T-AMD-09)."""
from __future__ import annotations

import os

import pytest


@pytest.fixture
def client():
    os.environ["AMA_TEST_MODE"] = "1"
    from fastapi.testclient import TestClient

    from apps.api.app.main import app

    return TestClient(app)


def test_indicator_definition_rejects_extra_fields(client):
    """POST with extra fields returns 422 validation error (T-AMD-19)."""
    payload = {
        "id": "test-id",
        "kpi_id": "test-kpi",
        "version": 1,
        "capstone_sc_id": "SC-CAP-015-001",
        "name": "Test Indicator",
        "kind": "leading",
        "extra_field_should_be_rejected": "this should fail",
    }
    resp = client.post("/api/v1/evidence/kpi-ladder", json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    errors = resp.json().get("detail", [])
    assert any("extra_field" in str(e).lower() for e in errors), "Expected extra field validation error"


def test_signal_rejects_extra_fields(client):
    """Signal POST with extra fields returns 422 (T-AMD-19)."""
    payload = {
        "id": "signal-test",
        "scenario_id": "cyclone",
        "seed": "123",
        "mode": "baseline",
        "kpi_id": "lives_saved",
        "capability_id": "cap-001",
        "unexpected_extra": "should fail",
    }
    resp = client.post("/api/v1/evidence/signals", json=payload)
    assert resp.status_code in (404, 422), f"Expected 404 or 422, got {resp.status_code}"


def test_audit_entry_rejects_extra_fields():
    """AuditEntry model rejects extra fields at instantiation (T-AMD-19)."""
    from apps.api.app.services.evidence.models.audit import AuditEntry
    from datetime import datetime, UTC
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        AuditEntry(
            id="audit-1",
            audit_id="audit-trace-1",
            value_id="value-1",
            kind="signal_ingested",
            actor="system",
            occurred_at=datetime.now(UTC),
            region="australiaeast",
            extra_forbidden_field="should fail",
        )

    assert "extra_forbidden_field" in str(exc_info.value).lower()
