"""Integration test: Audit immutability 409 (T-AMD-20, T-AMD-06)."""
from __future__ import annotations

import os

import pytest


@pytest.fixture
def client():
    os.environ["AMA_TEST_MODE"] = "1"
    from fastapi.testclient import TestClient

    from apps.api.app.main import app

    return TestClient(app)


def test_patch_audit_returns_409(client):
    """PATCH /audit/{value_id} returns 409 (T-AMD-20, T-AMD-06, FR-040)."""
    resp = client.patch("/api/v1/evidence/audit/some-value-id", json={"payload": "should fail"})
    assert resp.status_code == 409
    data = resp.json()
    assert data.get("title") == "audit-record-immutable"
    assert "cannot be modified or deleted" in data.get("detail", "").lower()


def test_delete_audit_returns_409(client):
    """DELETE /audit/{value_id} returns 409 (T-AMD-20, T-AMD-06, FR-040)."""
    resp = client.delete("/api/v1/evidence/audit/some-value-id")
    assert resp.status_code == 409
    data = resp.json()
    assert data.get("title") == "audit-record-immutable"
    assert "cannot be modified or deleted" in data.get("detail", "").lower()


def test_get_audit_is_allowed(client):
    """GET /audit/{value_id} is allowed (returns 404 for non-existent) (T-AMD-20)."""
    resp = client.get("/api/v1/evidence/audit/non-existent-value")
    assert resp.status_code in (200, 404), f"Expected 200 or 404, got {resp.status_code}"
