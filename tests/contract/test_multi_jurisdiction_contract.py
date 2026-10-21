"""Contract tests for multi-jurisdiction API endpoints (spec 022).

Validates:
- GET /api/jurisdictions returns sorted active jurisdictions
- GET /api/organisations?jurisdictionId=... supports multi-value
- GET /api/frameworks?jurisdictionId=... supports multi-value
- Backward compatibility: single jurisdictionId still works
"""

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "1")
    return TestClient(create_app())


class TestJurisdictionsEndpoint:
    """GET /api/jurisdictions returns sorted active jurisdictions."""

    def test_returns_200(self, client):
        resp = client.get("/api/jurisdictions")
        assert resp.status_code == 200

    def test_returns_list(self, client):
        data = client.get("/api/jurisdictions").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_each_item_has_required_fields(self, client):
        data = client.get("/api/jurisdictions").json()
        for item in data:
            assert "jurisdiction_id" in item
            assert "name" in item
            assert "level" in item

    def test_sorted_commonwealth_first(self, client):
        data = client.get("/api/jurisdictions").json()
        levels = [item["level"] for item in data]
        level_order = {"commonwealth": 0, "state": 1, "territory": 2}
        for i in range(len(levels) - 1):
            assert level_order.get(levels[i], 99) <= level_order.get(levels[i + 1], 99)

    def test_contains_nine_jurisdictions(self, client):
        data = client.get("/api/jurisdictions").json()
        ids = {item["jurisdiction_id"] for item in data}
        expected = {"commonwealth", "nsw", "vic", "qld", "sa", "wa", "tas", "act", "nt"}
        assert expected.issubset(ids)


class TestOrganisationsMultiJurisdiction:
    """GET /api/organisations?jurisdictionId=... supports repeated params."""

    def test_single_jurisdiction_backward_compat(self, client):
        resp = client.get("/api/organisations?jurisdictionId=nsw")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0

    def test_multiple_jurisdictions(self, client):
        resp = client.get("/api/organisations?jurisdictionId=nsw&jurisdictionId=vic")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0

    def test_multi_returns_union(self, client):
        nsw = client.get("/api/organisations?jurisdictionId=nsw").json()
        vic = client.get("/api/organisations?jurisdictionId=vic").json()
        both = client.get("/api/organisations?jurisdictionId=nsw&jurisdictionId=vic").json()
        assert len(both) >= max(len(nsw), len(vic))

    def test_no_duplicates(self, client):
        data = client.get("/api/organisations?jurisdictionId=nsw&jurisdictionId=commonwealth").json()
        ids = [item["organisation_id"] for item in data]
        assert len(ids) == len(set(ids))

    def test_empty_returns_empty(self, client):
        resp = client.get("/api/organisations")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_invalid_jurisdiction_returns_empty(self, client):
        resp = client.get("/api/organisations?jurisdictionId=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []


class TestFrameworksMultiJurisdiction:
    """GET /api/frameworks?jurisdictionId=... supports repeated params."""

    def test_single_jurisdiction(self, client):
        resp = client.get("/api/frameworks?jurisdictionId=nsw")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0

    def test_contains_aiims(self, client):
        data = client.get("/api/frameworks?jurisdictionId=nsw").json()
        assert any(fw["framework_id"] == "aiims-national" for fw in data)

    def test_multiple_jurisdictions(self, client):
        resp = client.get("/api/frameworks?jurisdictionId=nsw&jurisdictionId=vic")
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_empty_returns_empty(self, client):
        resp = client.get("/api/frameworks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_invalid_jurisdiction_returns_empty(self, client):
        resp = client.get("/api/frameworks?jurisdictionId=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []


class TestReplayBackwardCompatibility:
    """POST /api/scenarios/replay still works with jurisdiction_ids."""

    def test_replay_with_multiple_jurisdictions(self, client):
        resp = client.post(
            "/api/scenarios/replay",
            json={
                "scenarioName": "Cross-state Rehearsal",
                "scenarioType": "flood",
                "jurisdictionIds": ["nsw", "vic"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_type"] == "flood"
        assert set(data["jurisdiction_ids"]) == {"nsw", "vic"}
        assert len(data["framework_ids"]) > 0
