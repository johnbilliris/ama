"""Spec-036 Wave 4 — T-M04 RBAC integration sweep across all simulation routes.

Verifies that:

1. The four coordinator-only routes (``/inject-telemetry``, ``/pause``,
   ``/resume``, ``/abort``) reject anonymous callers (no claims) with
   HTTP 403 ``forbidden-role`` and write an
   ``audit.rbac.unauthorized_attempt`` envelope.
2. The same four routes reject callers carrying the wrong app-role
   (``simulation.observer``) with the same 403 + audit envelope.
3. A coordinator (``simulation.coordinator``) is admitted and the
   downstream business logic runs.
4. Tenant-mismatch (``X-Tenant-Id`` header diverges from the JWT
   ``tenant_id`` claim) is rejected with HTTP 403 ``forbidden-tenant``.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies.simulation_rbac import (
    CoordinatorPrincipal,
    require_simulation_coordinator,
)
from apps.api.app.api.routes.simulations_036 import router
from apps.api.app.services.simulation import cancellation as cancel_scope
from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.repositories.simulation_state import (
    reset_simulation_state_repository_for_tests,
)

SIM_ID = "11111111-2222-3333-4444-555555555555"


def _claims_for(roles: list[str], tenant: str = "tenant-1", sub: str = "user-x") -> dict:
    return {"sub": sub, "roles": roles, "tenant_id": tenant}


def _client_with_claims(claims: dict | None = None) -> TestClient:
    """Build a test client that injects ``claims`` into ``request.state``.

    Uses a tiny ASGI middleware so the route's RBAC dependency runs
    against realistic claim data (rather than via an
    ``app.dependency_overrides`` shortcut).
    """

    AuditWriter.reset_memory_for_test()
    reset_audit_writer_for_tests()
    cancel_scope.reset_for_tests()
    reset_simulation_state_repository_for_tests()

    app = FastAPI()
    app.include_router(router, prefix="/api")

    @app.middleware("http")
    async def _inject_claims(request, call_next):  # type: ignore[no-untyped-def]
        if claims is not None:
            request.state.claims = claims
        return await call_next(request)

    return TestClient(app)


def _client_with_principal(principal: CoordinatorPrincipal) -> TestClient:
    """Bypass the dependency entirely (positive-path business logic test)."""

    AuditWriter.reset_memory_for_test()
    reset_audit_writer_for_tests()
    cancel_scope.reset_for_tests()
    reset_simulation_state_repository_for_tests()

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[require_simulation_coordinator] = lambda: principal
    return TestClient(app)


# ---------------------------------------------------------------------------
# Route×denial matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("verb", "method", "body"),
    [
        ("inject-telemetry", "POST", {"chat_text": "temperature 41C in penrith at 14:00"}),
        ("pause", "POST", None),
        ("resume", "POST", None),
        ("abort", "POST", {"reason": "drill-end"}),
    ],
)
def test_anonymous_caller_rejected_403(verb: str, method: str, body: dict | None) -> None:
    client = _client_with_claims(claims=None)
    response = (
        client.post(f"/api/simulations/{SIM_ID}/{verb}", json=body)
        if method == "POST"
        else client.get(f"/api/simulations/{SIM_ID}/{verb}")
    )
    assert response.status_code == 403, response.text
    detail = response.json()["detail"]
    assert detail["type"].endswith("forbidden-role")
    assert detail["status"] == 403


@pytest.mark.parametrize(
    ("verb", "method", "body"),
    [
        ("inject-telemetry", "POST", {"chat_text": "temperature 41C in penrith at 14:00"}),
        ("pause", "POST", None),
        ("resume", "POST", None),
        ("abort", "POST", {"reason": "drill-end"}),
    ],
)
def test_observer_role_rejected_403(verb: str, method: str, body: dict | None) -> None:
    client = _client_with_claims(claims=_claims_for(["simulation.observer"]))
    response = (
        client.post(f"/api/simulations/{SIM_ID}/{verb}", json=body)
        if method == "POST"
        else client.get(f"/api/simulations/{SIM_ID}/{verb}")
    )
    assert response.status_code == 403, response.text
    detail = response.json()["detail"]
    assert detail["type"].endswith("forbidden-role")
    assert "simulation.observer" in str(detail.get("actual_roles") or [])


def test_anonymous_emits_audit_rbac_unauthorized_attempt() -> None:
    client = _client_with_claims(claims=None)
    response = client.post(f"/api/simulations/{SIM_ID}/pause")
    assert response.status_code == 403
    entries = AuditWriter.memory_for_test(SIM_ID)
    rbac_denials = [e for e in entries if e.entry_type == "audit.rbac.unauthorized_attempt"]
    assert len(rbac_denials) == 1, [e.entry_type for e in entries]
    details = rbac_denials[0].details
    assert details["reason"] == "missing_role"
    assert details["sim_id"] == SIM_ID
    assert details["actual_roles"] == []


def test_observer_emits_audit_rbac_unauthorized_attempt_with_actual_roles() -> None:
    client = _client_with_claims(claims=_claims_for(["simulation.observer"]))
    response = client.post(f"/api/simulations/{SIM_ID}/resume")
    assert response.status_code == 403
    entries = AuditWriter.memory_for_test(SIM_ID)
    rbac_denials = [e for e in entries if e.entry_type == "audit.rbac.unauthorized_attempt"]
    assert len(rbac_denials) == 1
    details = rbac_denials[0].details
    assert details["actual_roles"] == ["simulation.observer"]
    assert details["reason"] == "missing_role"


def test_tenant_mismatch_rejected_403() -> None:
    """X-Tenant-Id header diverging from JWT ``tenant_id`` → forbidden-tenant."""
    client = _client_with_claims(
        claims=_claims_for(["simulation.coordinator"], tenant="tenant-A"),
    )
    response = client.post(
        f"/api/simulations/{SIM_ID}/pause",
        headers={"X-Tenant-Id": "tenant-B"},
    )
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["type"].endswith("forbidden-tenant")
    entries = AuditWriter.memory_for_test(SIM_ID)
    rbac_denials = [e for e in entries if e.entry_type == "audit.rbac.unauthorized_attempt"]
    assert any(e.details["reason"] == "tenant_mismatch" for e in rbac_denials)


# ---------------------------------------------------------------------------
# Coordinator happy path (one per route)
# ---------------------------------------------------------------------------


def test_coordinator_can_pause() -> None:
    principal = CoordinatorPrincipal(user_id="coord-1", tenant_id="tenant-1", roles=("simulation.coordinator",))
    client = _client_with_principal(principal)
    response = client.post(f"/api/simulations/{SIM_ID}/pause")
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "paused"


def test_coordinator_can_resume() -> None:
    principal = CoordinatorPrincipal(user_id="coord-2", tenant_id="tenant-1", roles=("simulation.coordinator",))
    client = _client_with_principal(principal)
    response = client.post(f"/api/simulations/{SIM_ID}/resume")
    assert response.status_code == 200
    assert response.json()["state"] == "active"


def test_coordinator_can_abort() -> None:
    principal = CoordinatorPrincipal(user_id="coord-3", tenant_id="tenant-1", roles=("simulation.coordinator",))
    client = _client_with_principal(principal)
    response = client.post(
        f"/api/simulations/{SIM_ID}/abort",
        json={"reason": "drill-end"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["aborted"] is True


def test_coordinator_can_inject_benign() -> None:
    principal = CoordinatorPrincipal(user_id="coord-4", tenant_id="tenant-1", roles=("simulation.coordinator",))
    client = _client_with_principal(principal)
    response = client.post(
        f"/api/simulations/{SIM_ID}/inject-telemetry",
        json={"chat_text": "temperature 41C in penrith at 14:00"},
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["injection_correlation_id"]
