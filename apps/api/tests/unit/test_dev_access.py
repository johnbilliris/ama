from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from app.api.dependencies.rbac import require_simulation_admin, require_simulation_participant
from app.core.auth import AuthenticatedPrincipal, require_authenticated_persona
from app.core.dev_access import dev_access_enabled
from app.middleware.auth import authorize_management
from app.middleware import auth as management_auth
from app.middleware import entra_auth
from app.middleware.auth_middleware import add_auth_middleware
from app.middleware.tenant_middleware import add_tenant_middleware
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient


def _enable_dev_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.setenv("AMA_ENABLE_INCIDENT_MAP_AUTH", "0")


def test_dev_access_requires_dev_tier_and_explicit_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_dev_access(monkeypatch)
    assert dev_access_enabled()

    monkeypatch.setenv("AMA_ENVIRONMENT", "production")
    assert not dev_access_enabled()

    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0")
    assert not dev_access_enabled()


def test_management_jwt_uses_shared_entra_signature_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entra_auth, "_validate_jwt", lambda token: {"sub": token, "roles": ["admin"]})

    assert management_auth._validate_jwt("validated-token") == {
        "sub": "validated-token",
        "roles": ["admin"],
    }


@pytest.mark.parametrize("auth_flag", ["AMA_ENABLE_PRODUCTION_AUTH", "AMA_ENABLE_INCIDENT_MAP_AUTH"])
def test_live_auth_flags_disable_dev_access(monkeypatch: pytest.MonkeyPatch, auth_flag: str) -> None:
    _enable_dev_access(monkeypatch)
    monkeypatch.setenv(auth_flag, "1")

    assert not dev_access_enabled()


def test_dev_principal_grants_full_access_without_request_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_dev_access(monkeypatch)
    app = FastAPI()
    add_auth_middleware(app)

    @app.get("/api/personas/{persona_id}/workspace")
    async def workspace(persona_id: str, request: Request) -> dict[str, object]:
        return {
            "persona": require_authenticated_persona(request, persona_id),
            "roles": request.state.claims["roles"],
        }

    @app.post("/api/organisations/management")
    async def management(identity: dict = Depends(authorize_management)) -> dict:
        return identity

    client = TestClient(app)
    workspace_response = client.get("/api/personas/incident-commander/workspace")
    management_response = client.post("/api/organisations/management")

    assert workspace_response.status_code == 200
    assert workspace_response.json()["persona"] == "incident-commander"
    assert "system-administrator" in workspace_response.json()["roles"]
    assert "simulation.coordinator" in workspace_response.json()["roles"]
    assert management_response.status_code == 200
    assert management_response.json()["sub"] == "dev-user"


def test_dev_access_bypasses_simulation_role_and_membership_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_dev_access(monkeypatch)
    principal = AuthenticatedPrincipal(
        subject="dev-user",
        agency_id="dev",
        jurisdiction_ids=(),
        roles=("system-administrator",),
    )

    class OtherParticipantsRepository:
        async def get_by_tenant_id(self, _tenant_id: str) -> object:
            return SimpleNamespace(created_by="someone-else", participants=[])

    assert require_simulation_admin(principal) == principal
    assert (
        asyncio.run(
            require_simulation_participant(principal, "sim-existing", OtherParticipantsRepository())
        )
        == principal
    )


def test_dev_persona_workspace_can_select_its_simulation_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_dev_access(monkeypatch)
    app = FastAPI()

    class SimulationRepository:
        async def get_by_tenant_id(self, tenant_id: str) -> object:
            return SimpleNamespace(tenant_id=tenant_id, status="Running")

        async def get_by_participant(self, _subject: str) -> list[object]:
            return []

    add_tenant_middleware(app, simulation_repository=SimulationRepository())
    add_auth_middleware(app)

    @app.get("/api/personas/{persona_id}/workspace")
    async def workspace(request: Request) -> dict[str, str]:
        return {"tenant_id": request.state.tenant_context.tenant_id}

    response = TestClient(app).get(
        "/api/personas/incident-commander/workspace",
        headers={"X-Tenant-Id": "sim-dev"},
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "sim-dev"
