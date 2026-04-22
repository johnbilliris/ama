"""Contract tests for dead-letter API endpoints (T023-T024)."""

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


class TestDeadLetterEndpoints:
    """Contract: GET /management/dead-letters, POST /management/dead-letters/{id}/redeliver."""

    def test_list_dead_letters_returns_200(self, client):
        response = client.get(
            "/api/dead-letters",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_redeliver_nonexistent_returns_404(self, client):
        response = client.post(
            "/api/dead-letters/nonexistent/redeliver",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 404
