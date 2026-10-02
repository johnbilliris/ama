from __future__ import annotations

import pytest
from app.middleware.auth_middleware import _anonymous_incident_map_enabled, add_auth_middleware
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request


def _request(method: str, path: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "server": ("api.example.test", 443),
        }
    )


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_anonymous_incident_map_is_exact_read_only_dev_exception(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_INCIDENT_MAP", "1")
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)

    assert _anonymous_incident_map_enabled(_request(method, "/api/incidents/map"))
    assert not _anonymous_incident_map_enabled(_request("POST", "/api/incidents/map"))
    assert not _anonymous_incident_map_enabled(_request(method, "/api/incidents/incident-1"))


@pytest.mark.parametrize("environment", ["staging", "production", "prod"])
def test_anonymous_incident_map_is_disabled_outside_dev(
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", environment)
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_INCIDENT_MAP", "1")
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)

    assert not _anonymous_incident_map_enabled(_request("GET", "/api/incidents/map"))


def test_production_auth_overrides_anonymous_map_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_INCIDENT_MAP", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")

    assert not _anonymous_incident_map_enabled(_request("GET", "/api/incidents/map"))


def test_auth_middleware_allows_only_anonymous_map_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_INCIDENT_MAP", "1")
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)

    app = FastAPI()
    add_auth_middleware(app)

    @app.get("/api/incidents/map")
    async def incident_map() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/incidents/incident-1")
    async def incident_detail() -> dict[str, str]:
        return {"status": "unexpected"}

    client = TestClient(app)
    assert client.get("/api/incidents/map").status_code == 200
    assert client.get("/api/incidents/incident-1").status_code == 401
