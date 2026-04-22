"""Tests for management API authentication middleware (T015).

Covers:
- API key auth in local mode
- Missing API key → 401
- Invalid API key → 401
- Security audit logging on 401/403
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def _local_env(monkeypatch):
    """Configure local dev environment."""
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("MANAGEMENT_API_KEY", "test-secret-key")


@pytest.fixture
def app(_local_env):
    """Create a minimal FastAPI app with auth middleware."""
    # Re-import after env is set so module-level vars pick up test values
    import importlib

    import app.middleware.auth as auth_mod
    importlib.reload(auth_mod)

    from app.middleware.auth import authorize_management

    app = FastAPI()

    @app.get("/test-auth")
    async def protected_endpoint(
        auth: dict = Depends(authorize_management),
    ):
        return {"status": "ok", "identity": auth}

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestLocalApiKeyAuth:
    """API key authentication in local dev mode."""

    def test_valid_api_key(self, client):
        """Valid API key grants access."""
        response = client.get(
            "/test-auth",
            headers={"X-API-Key": "test-secret-key"},
        )
        assert response.status_code == 200

    def test_missing_api_key(self, client):
        """Missing API key returns 401."""
        response = client.get("/test-auth")
        assert response.status_code == 401

    def test_invalid_api_key(self, client):
        """Wrong API key returns 401."""
        response = client.get(
            "/test-auth",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


class TestSecurityAuditLogging:
    """Verify security audit events are logged."""

    def test_failed_auth_logged(self, client, caplog):
        """Failed auth attempts produce security audit log entries."""
        with caplog.at_level("WARNING"):
            client.get(
                "/test-auth",
                headers={"X-API-Key": "wrong-key"},
            )

        assert any(
            "management_auth_failure" in r.message
            for r in caplog.records
        )
