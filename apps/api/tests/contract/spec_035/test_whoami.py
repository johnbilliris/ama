"""T023 — ``GET /api/auth/whoami`` Principal shape contract.

Asserts the response shape matches
[auth-rbac.openapi.yaml](../../../../specs/035-webapp-capstone-closure/contracts/auth-rbac.openapi.yaml)
and that the ``impersonation`` block reflects the ``X-Impersonate-Persona`` header.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _enable_production_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv(
        "AMA_ENTRA_TEST_PRINCIPAL",
        json.dumps(
            {
                "oid": "00000000-0000-0000-0000-000000000001",
                "sub": "00000000-0000-0000-0000-000000000001",
                "app_role": "incident-commander",
                "roles": ["incident-commander"],
                "persona_id": "incident-commander",
            }
        ),
    )


def _build_app(principal: dict[str, str] | None = None) -> TestClient:
    if principal is not None:
        import os

        os.environ["AMA_ENTRA_TEST_PRINCIPAL"] = json.dumps(principal)

    from app.api.routes.auth_whoami import router as whoami_router
    from app.middleware.entra_auth import add_entra_auth_middleware

    app = FastAPI()
    add_entra_auth_middleware(app)
    app.include_router(whoami_router, prefix="/api")
    return TestClient(app)


def test_whoami_returns_principal_shape_for_normal_user() -> None:
    res = _build_app().get(
        "/api/auth/whoami",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200, res.text
    body = res.json()

    assert set(body.keys()) == {
        "operator_identity",
        "app_role",
        "persona_id",
        "impersonation",
    }
    assert body["operator_identity"] == "00000000-0000-0000-0000-000000000001"
    assert body["app_role"] == "incident-commander"
    assert body["persona_id"] == "incident-commander"
    assert body["impersonation"] == {
        "impersonating": False,
        "target_persona_id": None,
    }


def test_whoami_reflects_impersonation_when_header_present() -> None:
    client = _build_app(
        {
            "oid": "admin-oid",
            "sub": "admin-oid",
            "app_role": "system-administrator",
            "roles": ["system-administrator"],
            "persona_id": "system-administrator",
        }
    )
    res = client.get(
        "/api/auth/whoami",
        headers={
            "Authorization": "Bearer test",
            "X-Impersonate-Persona": "incident-commander",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["app_role"] == "system-administrator"
    assert body["impersonation"] == {
        "impersonating": True,
        "target_persona_id": "incident-commander",
    }
