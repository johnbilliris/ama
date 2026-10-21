from __future__ import annotations

import pytest
from app.api.dependencies.simulation_composition import get_simulation_repository, resolve_late_bound
from app.api.routes import incidents, simulations
from app.core.auth import AuthenticatedPrincipal
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.middleware.tenant_middleware import TenantMiddleware
from app.services.dashboard_service import DashboardService
from app.services.operational_store import OperationalStore
from app.services.state_store import reset_state
from fastapi import HTTPException

from packages.domain.src.domain.models.incident import Incident

pytestmark = pytest.mark.spec007_isolation


def test_live_and_sim_tenants_can_hold_same_incident_id_without_collision() -> None:
    reset_state()
    live_store = OperationalStore("live")
    sim_store = OperationalStore("sim-nsw-001")

    live_store.incidents.put(
        "incident-001",
        Incident(
            incident_id="incident-001",
            title="Live Incident",
            incident_type="flood",
            status="active",
            severity="warning",
            affected_jurisdiction_ids=["nsw"],
        ),
    )
    sim_store.incidents.put(
        "incident-001",
        Incident(
            incident_id="incident-001",
            title="Simulation Incident",
            incident_type="flood",
            status="rehearsal",
            severity="warning",
            affected_jurisdiction_ids=["nsw"],
        ),
    )

    assert live_store.incidents.require("incident-001").title == "Live Incident"
    assert sim_store.incidents.require("incident-001").title == "Simulation Incident"


def test_dashboard_cannot_read_foreign_tenant_incident() -> None:
    reset_state()
    OperationalStore("live").incidents.put(
        "incident-foreign",
        Incident(
            incident_id="incident-foreign",
            title="Live-only Incident",
            incident_type="storm",
            status="active",
            severity="watch",
            affected_jurisdiction_ids=["vic"],
        ),
    )

    token = set_current_tenant(
        TenantContext(
            agency_id="ses-nsw",
            jurisdiction_ids=("nsw",),
            tenant_id="sim-drill-001",
        )
    )
    try:
        with pytest.raises(KeyError):
            DashboardService().get_dashboard("incident-foreign")
    finally:
        reset_current_tenant(token)


@pytest.mark.asyncio
async def test_sim_tenant_requires_participant_membership() -> None:
    class _Repo:
        async def get_by_tenant_id(self, tenant_id: str):  # noqa: ANN202, ARG002
            return type("Tenant", (), {"created_by": "owner", "participants": [], "status": "Active"})()

    middleware = TenantMiddleware(app=lambda scope, receive, send: None, simulation_repository=_Repo())
    principal = AuthenticatedPrincipal(
        subject="user-123",
        agency_id="ses-nsw",
        jurisdiction_ids=("nsw",),
        roles=("SimulationUser",),
        persona_id="persona-1",
    )

    with pytest.raises(PermissionError, match="Simulation tenant membership required"):
        await middleware._resolve_tenant_id("/api/simulations/sim-drill-001/seed", principal)


def test_simulation_repository_is_shared_across_request_boundaries() -> None:
    shared = get_simulation_repository()
    assert resolve_late_bound(simulations._repo) is shared
    assert resolve_late_bound(incidents._sim_repo) is shared


@pytest.mark.asyncio
async def test_missing_simulation_tenant_returns_404() -> None:
    class _Repo:
        async def get_by_tenant_id(self, tenant_id: str):  # noqa: ANN202, ARG002
            return None

    middleware = TenantMiddleware(app=lambda scope, receive, send: None, simulation_repository=_Repo())
    principal = AuthenticatedPrincipal("user-123", "ses-nsw", ("nsw",), ("SimulationUser",))

    with pytest.raises(HTTPException) as exc:
        await middleware._resolve_tenant_id("/api/simulations/sim-missing/seed", principal)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_multiple_active_simulations_require_explicit_tenant() -> None:
    class _Repo:
        async def get_by_participant(self, user_oid: str):  # noqa: ANN202, ARG002
            tenant = type("Tenant", (), {})
            return [tenant(), tenant()]

    middleware = TenantMiddleware(app=lambda scope, receive, send: None, simulation_repository=_Repo())
    principal = AuthenticatedPrincipal("user-123", "ses-nsw", ("nsw",), ("SimulationUser",))

    with pytest.raises(HTTPException) as exc:
        await middleware._resolve_tenant_id("/api/signals", principal)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_repository_failure_returns_503() -> None:
    class _Repo:
        async def get_by_participant(self, user_oid: str):  # noqa: ANN202, ARG002
            raise TimeoutError("cosmos timeout")

    middleware = TenantMiddleware(app=lambda scope, receive, send: None, simulation_repository=_Repo())
    principal = AuthenticatedPrincipal("user-123", "ses-nsw", ("nsw",), ("SimulationUser",))

    with pytest.raises(HTTPException) as exc:
        await middleware._resolve_tenant_id("/api/signals", principal)
    assert exc.value.status_code == 503
