"""Integration test: Audit immutability 409 (T-AMD-20, T-AMD-06)."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def client():
    os.environ["AMA_TEST_MODE"] = "1"
    from app.main import create_app
    from app.services.evidence._clients import reset_registry
    from app.services.evidence.instrumentation import audit_manager
    from fastapi.testclient import TestClient

    reset_registry()
    audit_manager.record(
        kind="signal_ingested",
        value_id="known-value-id",
        actor="fixture",
        references={"signal_id": "known-value-id"},
    )
    return TestClient(create_app())


def test_patch_audit_returns_409(client):
    """PATCH /audit/{value_id} returns 409 (T-AMD-20, T-AMD-06, FR-040)."""
    resp = client.patch(
        "/api/v1/evidence/audit/known-value-id",
        json={"payload": "should fail"},
        headers={"x-ama-correlation-id": "tamper-patch"},
    )
    assert resp.status_code == 409
    data = resp.json()
    assert data.get("title") == "audit-record-immutable"
    assert "cannot be modified or deleted" in data.get("detail", "").lower()
    assert resp.headers["x-ama-correlation-id"] == "tamper-patch"


def test_delete_audit_returns_409(client):
    """DELETE /audit/{value_id} returns 409 (T-AMD-20, T-AMD-06, FR-040)."""
    resp = client.delete("/api/v1/evidence/audit/known-value-id")
    assert resp.status_code == 409
    data = resp.json()
    assert data.get("title") == "audit-record-immutable"
    assert "cannot be modified or deleted" in data.get("detail", "").lower()


def test_put_audit_returns_409(client):
    resp = client.put(
        "/api/v1/evidence/audit/known-value-id",
        json={"payload": "should fail"},
    )

    assert resp.status_code == 409
    assert resp.json()["title"] == "audit-record-immutable"


def test_each_refusal_preserves_original_and_records_one_attempt(client):
    from app.services.evidence._clients import get_registry

    container = get_registry().get("evidence_audit")
    original = next(row for row in container.all() if row["kind"] == "signal_ingested")
    original_hash = original["payload_sha256"]

    client.patch("/api/v1/evidence/audit/known-value-id")
    client.put("/api/v1/evidence/audit/known-value-id")
    client.delete("/api/v1/evidence/audit/known-value-id")

    rows = container.all()
    preserved = next(row for row in rows if row["id"] == original["id"])
    attempts = [row for row in rows if row["kind"] == "audit_mutation_attempted"]
    assert preserved["payload_sha256"] == original_hash
    assert [row["payload"]["method"] for row in attempts] == [
        "PATCH",
        "PUT",
        "DELETE",
    ]
    assert all(row["actor"] == "anonymous" for row in attempts)
    assert len(get_registry().blob_archive.list_json("audit/known-value-id/")) == 4


def test_get_audit_is_allowed(client):
    """GET /audit/{value_id} is allowed (returns 404 for non-existent) (T-AMD-20)."""
    resp = client.get("/api/v1/evidence/audit/known-value-id")
    assert resp.status_code == 200
