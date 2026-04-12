"""Tests for evacuation.agent endpoints — health, override, replan (T043)."""

import pytest
from evacuation.agent import EvacuationAgent, create_app
from evacuation.config import EvacuationConfig
from evacuation.road_network import RoadNetworkLoader
from fastapi.testclient import TestClient

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


@pytest.fixture
def app():
    """Create a FastAPI app with a minimal agent (no Cosmos, no LLM)."""
    config = EvacuationConfig()
    road_network = RoadNetworkLoader()
    road_network.load(SAMPLE_FILE)

    agent = EvacuationAgent(
        config=config,
        road_network=road_network,
        cosmos_plans_container=None,
        cosmos_decisions_container=None,
        cosmos_assessments_container=None,
    )
    return create_app(agent=agent, config=config)


@pytest.fixture
def client(app):
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /health returns valid JSON
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert "agent_version" in data
        assert "timestamp" in data
        assert "checks" in data

    def test_health_checks_structure(self, client):
        resp = client.get("/health")
        checks = resp.json()["checks"]
        assert "road_network_loaded" in checks
        assert "llm_connectivity" in checks
        assert "cosmos_connectivity" in checks
        assert "active_plan_count" in checks
        assert "processing_queue_depth" in checks
        assert "audit_store" in checks

    def test_road_network_loaded(self, client):
        resp = client.get("/health")
        rn = resp.json()["checks"]["road_network_loaded"]
        assert rn["node_count"] == 50
        assert rn["edge_count"] == 120


# ---------------------------------------------------------------------------
# POST /override with valid actions
# ---------------------------------------------------------------------------


class TestOverrideEndpoint:
    def test_valid_override_approve(self, client):
        """Override without Cosmos just applies the action."""
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-v1",
                "action": "approve",
                "user_id": "user-1",
                "role": "incident_commander",
                "justification": "Plan looks good",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_status"] == "approved"
        assert data["plan_id"] == "ep-inc-v1"

    def test_override_response_fields(self, client):
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-v1",
                "action": "reject",
                "user_id": "user-1",
                "role": "reviewer",
                "justification": "Insufficient routes",
            },
        )
        data = resp.json()
        assert "previous_status" in data
        assert "new_status" in data
        assert "override_timestamp" in data
        assert "audit_record_id" in data


# ---------------------------------------------------------------------------
# Invalid action returns 422
# ---------------------------------------------------------------------------


class TestInvalidOverride:
    def test_invalid_action_returns_422(self, client):
        resp = client.post(
            "/override",
            json={
                "plan_id": "ep-inc-v1",
                "action": "invalid_action",
                "user_id": "user-1",
                "role": "admin",
                "justification": "test",
            },
        )
        assert resp.status_code == 422

    def test_missing_fields_returns_422(self, client):
        resp = client.post(
            "/override",
            json={"plan_id": "ep-inc-v1"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /replan triggers replanning
# ---------------------------------------------------------------------------


class TestReplanEndpoint:
    def test_replan_with_triggers(self, client):
        resp = client.post(
            "/replan",
            json={
                "incident_id": "inc-001",
                "manual_trigger": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["triggered"] is True
        assert len(data["triggers"]) > 0
        assert data["incident_id"] == "inc-001"

    def test_replan_no_triggers(self, client):
        resp = client.post(
            "/replan",
            json={
                "incident_id": "inc-001",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["triggered"] is False

    def test_replan_with_road_closures(self, client):
        resp = client.post(
            "/replan",
            json={
                "incident_id": "inc-001",
                "new_road_closures": ["edge-1", "edge-2"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["triggered"] is True

    def test_replan_response_fields(self, client):
        resp = client.post(
            "/replan",
            json={
                "incident_id": "inc-001",
                "manual_trigger": True,
            },
        )
        data = resp.json()
        assert "incident_id" in data
        assert "triggered" in data
        assert "triggers" in data
        assert "rate_limited" in data
        assert "material_change" in data


# ---------------------------------------------------------------------------
# Rate limiting returns 429 (via rate_limited field)
# ---------------------------------------------------------------------------


class TestReplanRateLimiting:
    def test_rapid_replans_rate_limited(self, client):
        """Second rapid replan should be rate-limited."""
        # First replan — should succeed
        resp1 = client.post(
            "/replan",
            json={"incident_id": "inc-rl", "manual_trigger": True},
        )
        assert resp1.json()["rate_limited"] is False

        # Second replan immediately — should be rate-limited
        resp2 = client.post(
            "/replan",
            json={"incident_id": "inc-rl", "manual_trigger": True},
        )
        assert resp2.json()["rate_limited"] is True
