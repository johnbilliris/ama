import uuid

from app.main import create_app
from fastapi import APIRouter
from fastapi.testclient import TestClient


def _assert_uuid(value: str) -> None:
    assert str(uuid.UUID(value)) == value


def test_error_responses_are_structured_json() -> None:
    client = TestClient(create_app())

    response = client.post("/api/dead-letters/missing-entry/resolve", json={"resolution": "replayed"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["correlationId"] == response.headers["X-Correlation-ID"]
    _assert_uuid(payload["correlationId"])
    assert payload["statusCode"] == 422
    assert payload["errorCategory"] == "validation_error"
    assert "message" in payload


def test_route_not_found_uses_starlette_handler_and_shared_correlation_id() -> None:
    client = TestClient(create_app())

    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    payload = response.json()
    assert payload["correlationId"] == response.headers["X-Correlation-ID"]
    _assert_uuid(payload["correlationId"])
    assert payload["errorCategory"] == "not_found"


def test_method_not_allowed_uses_shared_correlation_id() -> None:
    client = TestClient(create_app())

    response = client.put("/api/dead-letters")

    assert response.status_code == 405
    payload = response.json()
    assert payload["correlationId"] == response.headers["X-Correlation-ID"]
    _assert_uuid(payload["correlationId"])
    assert payload["message"] == "HTTP method is not allowed for this endpoint"


def test_permission_error_never_echoes_secret_marker() -> None:
    app = create_app()
    router = APIRouter()

    @router.get("/secret-permission-error")
    async def _secret_permission_error() -> dict[str, str]:
        raise PermissionError("SECRET_MARKER should never leak")

    app.include_router(router, prefix="/api/test-errors")
    client = TestClient(app)

    response = client.get("/api/test-errors/secret-permission-error")

    assert response.status_code == 403
    payload = response.json()
    assert payload["correlationId"] == response.headers["X-Correlation-ID"]
    _assert_uuid(payload["correlationId"])
    assert payload["errorCategory"] == "authorization_error"
    assert "SECRET_MARKER" not in payload["message"]
