"""Regression tests for require_simulation_participant error taxonomy.

Bug fixed: stopping a simulation whose in-memory tenant had been wiped
(e.g. uvicorn reload) produced a misleading "User anonymous is not a
participant …" 403. The helper now distinguishes:

* missing tenant → HTTPException(404)
* creator bypass → allowed even if participants drifted
* genuine non-member → PermissionError (→ 403)
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from apps.api.app.api.dependencies.rbac import require_simulation_admin, require_simulation_participant
from apps.api.app.core.auth import AuthenticatedPrincipal


class _StubRepo:
    def __init__(self, tenant):
        self._tenant = tenant

    async def get_by_tenant_id(self, _tenant_id):
        return self._tenant


class _Tenant:
    def __init__(self, created_by, participants):
        self.created_by = created_by
        self.participants = list(participants)


def _principal(sub: str) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject=sub,
        agency_id="agency",
        jurisdiction_ids=(),
        roles=("SimulationUser",),
    )


@pytest.mark.asyncio
async def test_missing_tenant_returns_404() -> None:
    repo = _StubRepo(tenant=None)
    with pytest.raises(HTTPException) as exc:
        await require_simulation_participant(_principal("anonymous"), "sim-x", repo)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_creator_is_always_allowed() -> None:
    # Even if participants list somehow doesn't include the creator, the
    # creator can still drive the simulation.
    repo = _StubRepo(tenant=_Tenant(created_by="anonymous", participants=[]))
    result = await require_simulation_participant(_principal("anonymous"), "sim-x", repo)
    assert result.subject == "anonymous"


@pytest.mark.asyncio
async def test_participant_in_list_allowed() -> None:
    repo = _StubRepo(tenant=_Tenant(created_by="alice", participants=["alice", "bob"]))
    result = await require_simulation_participant(_principal("bob"), "sim-x", repo)
    assert result.subject == "bob"


@pytest.mark.asyncio
async def test_non_participant_raises_permission_error() -> None:
    repo = _StubRepo(tenant=_Tenant(created_by="alice", participants=["alice"]))
    with pytest.raises(PermissionError) as exc:
        await require_simulation_participant(_principal("mallory"), "sim-x", repo)
    assert "mallory" in str(exc.value)
    assert "not a participant" in str(exc.value)


@pytest.mark.parametrize("role", ["simulation.admin", "system-administrator"])
def test_simulation_admin_roles_are_accepted(role: str) -> None:
    principal = AuthenticatedPrincipal("admin", "agency", (), (role,))

    assert require_simulation_admin(principal) is principal


def test_non_admin_is_rejected() -> None:
    with pytest.raises(PermissionError, match="administrator"):
        require_simulation_admin(_principal("participant"))
