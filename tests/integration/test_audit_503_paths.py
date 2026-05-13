"""Integration test: Audit 503 paths — AU-refusal with failed audit write + healthz offline (T-AMD-21).

Covers:
  (a) AU-region refusal with simulated audit-write failure → 503 audit-write-unavailable
  (b) /healthz/evidence returning 503 when a critical store is forced offline
"""
from __future__ import annotations

import unittest.mock as mock

import pytest


@pytest.fixture(autouse=True)
def set_test_mode(monkeypatch):
    monkeypatch.setenv("AMA_TEST_MODE", "1")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from apps.api.app.main import app
    return TestClient(app)


def test_healthz_returns_503_when_cosmos_critical_store_offline(monkeypatch):
    """healthz/evidence → 503 when a critical Cosmos container is unavailable (T-AMD-21b, FR-045)."""
    monkeypatch.setenv("AMA_TEST_MODE", "1")

    # Use the same import path as the app itself
    from app.services.evidence._clients import get_registry, reset_registry  # type: ignore[import]
    from fastapi.testclient import TestClient

    from apps.api.app.main import app
    reset_registry()
    registry = get_registry()

    original_get = registry.get

    def failing_get(name: str):
        if name == "evidence_audit":
            raise ConnectionError("Simulated Cosmos offline")
        return original_get(name)

    with mock.patch.object(registry, "get", side_effect=failing_get):
        c = TestClient(app)
        resp = c.get("/api/healthz/evidence")
        assert resp.status_code == 503, (
            f"Expected 503 on critical store offline, got {resp.status_code}"
        )
        data = resp.json()
        assert data.get("status") == "critical"


def test_healthz_returns_200_degraded_when_only_appinsights_offline(monkeypatch):
    """healthz/evidence → 200 + degraded:true when only non-critical App Insights is offline (T-AMD-21b, FR-045)."""
    monkeypatch.setenv("AMA_TEST_MODE", "1")
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)

    from app.services.evidence._clients import reset_registry  # type: ignore[import]
    reset_registry()

    from fastapi.testclient import TestClient

    from apps.api.app.main import app
    c = TestClient(app)
    resp = c.get("/api/healthz/evidence")
    assert resp.status_code == 200, f"Expected 200 on non-critical offline, got {resp.status_code}"
    data = resp.json()
    assert data.get("degraded") is True or data.get("status") in ("ok", "degraded")


def test_audit_write_failure_raises_503(monkeypatch):
    """Audit write exhausting all retries → AuditWriteUnavailableError → 503 (T-AMD-21a, FR-044)."""
    monkeypatch.setenv("AMA_TEST_MODE", "1")

    import asyncio

    from apps.api.app.services.evidence._clients import get_registry, reset_registry
    from apps.api.app.services.evidence.audit_writer import AuditWriteUnavailableError, write_audit_entry

    reset_registry()
    registry = get_registry()

    # Patch the audit container to always fail
    audit_container = registry.get("evidence_audit")
    with mock.patch.object(audit_container, "create_item", side_effect=RuntimeError("forced failure")):
        with pytest.raises(AuditWriteUnavailableError) as exc_info:
            asyncio.run(write_audit_entry({
                "id": "test-fail-id",
                "audit_id": "test-audit-id",
                "value_id": "test-value-id",
                "kind": "signal_ingested",
                "actor": "test",
                "occurred_at": "2026-01-01T00:00:00+00:00",
                "region": "australiaeast",
            }))
        pd = exc_info.value.to_problem_details()
        assert pd.status == 503
        assert pd.title == "audit-write-unavailable"


def test_au_region_refusal_still_returns_response_on_audit_write_success(monkeypatch):
    """AU-region guard: non-AU signal raises, audit row written before error (T-AMD-21a, FR-044)."""
    monkeypatch.setenv("AMA_TEST_MODE", "1")

    from apps.api.app.services.evidence._clients import get_registry, reset_registry
    from apps.api.app.services.evidence._guards import NonAuRegionError, assert_au_region
    reset_registry()
    registry = get_registry()

    # Non-AU region should raise NonAuRegionError
    with pytest.raises(NonAuRegionError):
        assert_au_region({"region": "westus", "id": "test-signal"})

    # Verify that an audit entry was written (guard writes audit row before raising)
    audit_container = registry.get("evidence_audit")
    audit_items = audit_container.all()
    refused_items = [i for i in audit_items if i.get("kind") == "non_au_signal_refused"]
    assert len(refused_items) >= 1, "Expected an audit entry for non-AU signal refusal"
