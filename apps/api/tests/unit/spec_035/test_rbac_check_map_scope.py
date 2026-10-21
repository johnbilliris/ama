import pytest
from app.middleware.auth_middleware import _trusted_test_identity_enabled, add_auth_middleware
from app.middleware.entra_auth import _should_authenticate, add_entra_auth_middleware
from app.middleware.rbac_check import RbacCheckMiddleware, _should_enforce, add_rbac_check_middleware
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request


def _request_with_claims(claims: dict[str, object], path: str = "/api/incidents/map") -> Request:
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "server": ("api.example.test", 443),
        }
    )
    request.state.claims = claims
    return request


def test_delegated_scope_authorizes_incident_map_read() -> None:
    request = _request_with_claims(
        {
            "sub": "operator-1",
            "scp": "openid profile access_as_user",
        }
    )

    RbacCheckMiddleware._enforce(request)


@pytest.mark.parametrize("path", ["/api/incidents/incident-1", "/api/outcomes/sc-001/evaluate"])
def test_delegated_scope_does_not_bypass_other_role_boundaries(path: str) -> None:
    request = _request_with_claims(
        {
            "sub": "operator-1",
            "scp": "access_as_user",
        },
        path,
    )

    with pytest.raises(ExtensionEnvelopeError) as exc_info:
        RbacCheckMiddleware._enforce(request)

    assert exc_info.value.code == ExtensionErrorCode.UNAUTHORIZED


def test_incident_map_auth_mode_does_not_protect_unrelated_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
    monkeypatch.setenv("AMA_ENABLE_INCIDENT_MAP_AUTH", "1")

    assert _should_authenticate("/api/incidents/map")
    assert _should_enforce("/api/incidents/map")
    assert not _should_authenticate("/api/alerts/alert-1")
    assert not _should_enforce("/api/alerts/alert-1")


def test_incident_map_auth_disables_trusted_test_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
    monkeypatch.setenv("AMA_ENABLE_INCIDENT_MAP_AUTH", "1")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")

    assert not _trusted_test_identity_enabled()


def test_incident_map_auth_stack_is_route_scoped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
    monkeypatch.setenv("AMA_ENABLE_INCIDENT_MAP_AUTH", "1")
    monkeypatch.setattr(
        "app.middleware.entra_auth._validate_jwt",
        lambda _token: {"sub": "operator-1", "scp": "access_as_user"},
    )

    app = FastAPI()
    add_auth_middleware(app)
    add_rbac_check_middleware(app)
    add_entra_auth_middleware(app)

    @app.get("/api/incidents/map")
    async def incident_map() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/alerts/alert-1")
    async def unrelated_route() -> dict[str, str]:
        return {"status": "unchanged"}

    client = TestClient(app)
    assert client.get("/api/incidents/map").status_code == 401
    authorization = "Bear" + "er test-token"
    assert client.get("/api/incidents/map", headers={"Authorization": authorization}).status_code == 200
    assert client.get("/api/alerts/alert-1").status_code == 200
