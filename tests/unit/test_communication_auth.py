from __future__ import annotations

import pytest
from common.entra_principal import EntraPrincipalResolver
from fastapi import HTTPException
from starlette.requests import Request


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/alerts/ca-inc-1-v1",
            "headers": [(b"authorization", b"Bearer test-token")],
        }
    )


@pytest.mark.asyncio
async def test_valid_identity_without_operational_tenant_fails_closed(monkeypatch) -> None:
    resolver = EntraPrincipalResolver(tenant_id="entra-tenant", audience="api://communication")

    async def claims(_token: str):
        return {"oid": "commander-1", "roles": ["IncidentCommander"]}

    monkeypatch.setattr(resolver, "_validate_token", claims)

    with pytest.raises(HTTPException) as exc_info:
        await resolver(_request())

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_operational_tenant_and_roles_are_resolved_from_verified_claims(monkeypatch) -> None:
    resolver = EntraPrincipalResolver(tenant_id="entra-tenant", audience="api://communication")

    async def claims(_token: str):
        return {
            "oid": "commander-1",
            "roles": ["IncidentCommander"],
            "operational_tenant_id": "tenant-one",
        }

    monkeypatch.setattr(resolver, "_validate_token", claims)

    principal = await resolver(_request())

    assert principal.subject == "commander-1"
    assert principal.tenant_id == "tenant-one"
    assert principal.commander_role == "IncidentCommander"
