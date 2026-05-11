"""T-C09/T-C10 inject-telemetry endpoint smoke test (Wave 4 RBAC-aware)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies.simulation_rbac import (
    CoordinatorPrincipal,
    require_simulation_coordinator,
)
from apps.api.app.api.routes.simulations_036 import router
from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)


def _coordinator_principal() -> CoordinatorPrincipal:
    return CoordinatorPrincipal(
        user_id="coord-1",
        tenant_id="tenant-1",
        roles=("simulation.coordinator",),
    )


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_audit_writer_for_tests()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    # Wave 4 — bypass RBAC by injecting a coordinator principal.
    app.dependency_overrides[require_simulation_coordinator] = _coordinator_principal
    return TestClient(app)


def test_invalid_sim_id_400() -> None:
    c = _client()
    r = c.post(
        "/api/simulations/not-a-uuid/inject-telemetry",
        json={"chat_text": "temperature 41C"},
    )
    assert r.status_code == 400


def test_life_safety_phrasing_refused() -> None:
    c = _client()
    sim = "11111111-2222-3333-4444-555555555555"
    r = c.post(
        f"/api/simulations/{sim}/inject-telemetry",
        json={"chat_text": "issue an evacuation order for Lismore"},
    )
    assert r.status_code == 400
    body = r.json()
    assert "Injection refused" in str(body)


def test_benign_signal_accepted_via_fallback() -> None:
    c = _client()
    sim = "11111111-2222-3333-4444-555555555555"
    r = c.post(
        f"/api/simulations/{sim}/inject-telemetry",
        json={"chat_text": "temperature 41C in penrith at 14:00"},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["injection_correlation_id"]
    assert body["signals"], body
    assert body["signals"][0]["synthetic_signal"] is True


def test_audit_writer_emits_attempted_and_success() -> None:
    c = _client()
    sim = "11111111-2222-3333-4444-555555555555"
    r = c.post(
        f"/api/simulations/{sim}/inject-telemetry",
        json={"chat_text": "river gauge rising 2m at gauge-3"},
    )
    assert r.status_code == 202
    entries = AuditWriter.memory_for_test(sim)
    types = [e.entry_type for e in entries]
    assert "injection.attempted" in types
    assert "injection.success" in types
