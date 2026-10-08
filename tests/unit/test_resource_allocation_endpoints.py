"""Unit tests for override endpoint and processing.

Covers:
- Reassign, add, remove, priority-change overrides
- Approve/reject/cancel plan transitions
- Override metadata recording
- Justification required
"""

from __future__ import annotations

import pytest
from resource_allocation.agent import ResourceAllocationAgent, create_app
from resource_allocation.config import ResourceAllocationConfig


class _FakePlansStore:
    def __init__(self):
        self.docs = {
            "rdp-inc001-v1": {
                "id": "rdp-inc001-v1",
                "status": "proposed",
                "version": 1,
                "_etag": "v1",
            }
        }

    def read_item(self, item: str, partition_key: str):
        if item != partition_key or item not in self.docs:
            raise RuntimeError("404 NotFound")
        return dict(self.docs[item])

    def replace_item(self, item: str, body: dict, etag: str | None = None, match_condition: str | None = None):
        if item not in self.docs:
            raise RuntimeError("404 NotFound")
        current = self.docs[item]
        if etag is not None and etag != current.get("_etag"):
            raise RuntimeError("412 PreconditionFailed")
        next_doc = dict(body)
        next_doc["_etag"] = f"v{int(current.get('version', 1)) + 1}"
        self.docs[item] = next_doc
        return dict(next_doc)


class TestOverrideEndpoint:
    """Test the POST /override FastAPI endpoint."""

    @pytest.fixture
    def app(self):
        config = ResourceAllocationConfig()
        agent = ResourceAllocationAgent(config=config, cosmos_plans_container=_FakePlansStore())
        return create_app(agent=agent, config=config)

    @pytest.fixture
    def client(self, app):
        from fastapi.testclient import TestClient

        return TestClient(app)

    def test_approve_override(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "approve",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Plan meets requirements",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_applied"] == "approve"

    def test_reject_override(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "reject",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Insufficient resources allocated",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_cancel_override(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "cancel",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Incident downgraded",
            },
        )
        assert response.status_code == 200

    def test_reassign_override(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "reassign",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Better resource available",
                "details": {"resource_id": "veh-amb-002", "demand_id": "dem-001"},
            },
        )
        assert response.status_code == 200
        assert response.json()["action_applied"] == "reassign"
        assert response.json()["success"] is True

    def test_invalid_action_rejected(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "invalid_action",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Testing",
            },
        )
        assert response.status_code == 400

    def test_empty_justification_rejected(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "approve",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "   ",
            },
        )
        assert response.status_code == 400

    def test_no_material_change_returns_success_false(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "reassign",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "No effective plan delta",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_unknown_plan_returns_404(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-missing-v1",
                "action": "approve",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Plan missing",
            },
        )
        assert response.status_code == 404

    def test_unauthorized_role_returns_403(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "approve",
                "user_id": "cmd-001",
                "role": "observer",
                "justification": "Not allowed",
            },
        )
        assert response.status_code == 403

    def test_override_returns_record_id(self, client):
        response = client.post(
            "/override",
            json={
                "plan_id": "rdp-inc001-v1",
                "action": "approve",
                "user_id": "cmd-001",
                "role": "incident_commander",
                "justification": "Approved after review",
            },
        )
        data = response.json()
        assert data["override_record_id"] is not None


class TestHealthEndpoint:
    """Test the GET /health FastAPI endpoint."""

    @pytest.fixture
    def client(self):
        config = ResourceAllocationConfig()
        agent = ResourceAllocationAgent(config=config)
        app = create_app(agent=agent, config=config)
        from fastapi.testclient import TestClient

        return TestClient(app)

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert data["agent_version"] == "0.1.0"
        assert "timestamp" in data
        assert isinstance(data["checks"], list)

    def test_health_includes_checks(self, client):
        response = client.get("/health")
        data = response.json()
        check_names = {c["name"] for c in data["checks"]}
        assert "inventory_loaded" in check_names
        assert "llm_connectivity" in check_names
        assert "cosmos_connectivity" in check_names
