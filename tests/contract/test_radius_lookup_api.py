"""Contract tests for radius lookup API endpoints (T035-T036)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def _env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("MANAGEMENT_API_KEY", "test-key")


@pytest.fixture
def client(_env):
    from app.main import app
    return TestClient(app)


class TestRadiusLookupEndpoints:
    """Contract: /management/radius-lookup endpoints."""

    def test_list_returns_200(self, client):
        response = client.get(
            "/api/admin/radius-lookup",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
