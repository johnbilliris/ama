"""Contract tests for Planning Agent API endpoints.

Verifies endpoint existence, request/response shapes, and status codes.
"""
import pytest
from fastapi.testclient import TestClient
from planning.agent import create_app
from planning.config import PlanningConfig


@pytest.fixture
def client():
    config = PlanningConfig()
    app = create_app(config=config)
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "agent_version" in data


class TestPlanEndpoints:
    def test_create_plan_returns_201(self, client):
        resp = client.post("/plans", json={
            "title": "Flood Emergency Plan", "region_id": "r-au-nsw-sydney",
            "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "plan_id" in data
        assert data["lifecycle_state"] == "draft"

    def test_get_plan_returns_200(self, client):
        # Create first
        create_resp = client.post("/plans", json={
            "title": "Test", "region_id": "r-1", "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        plan_id = create_resp.json()["plan_id"]
        resp = client.get(f"/plans/{plan_id}")
        assert resp.status_code == 200

    def test_list_plans_returns_200(self, client):
        resp = client.get("/plans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_update_section_returns_200(self, client):
        create_resp = client.post("/plans", json={
            "title": "Test", "region_id": "r-1", "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        plan_id = create_resp.json()["plan_id"]
        resp = client.put(f"/plans/{plan_id}/sections/authority", json={
            "content": "Issued by NSW SES", "title": "Authority",
        })
        assert resp.status_code == 200

    def test_transition_returns_200(self, client):
        create_resp = client.post("/plans", json={
            "title": "Test", "region_id": "r-1", "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        plan_id = create_resp.json()["plan_id"]
        resp = client.post(f"/plans/{plan_id}/transition", json={
            "target_state": "in_consultation", "user_role": "planning_officer",
        })
        assert resp.status_code == 200

    def test_completeness_returns_200(self, client):
        create_resp = client.post("/plans", json={
            "title": "Test", "region_id": "r-1", "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        plan_id = create_resp.json()["plan_id"]
        resp = client.get(f"/plans/{plan_id}/completeness")
        assert resp.status_code == 200
        data = resp.json()
        assert "section_completeness" in data
        assert "principles_completeness" in data

    def test_get_plan_not_found_404(self, client):
        resp = client.get("/plans/nonexistent")
        assert resp.status_code == 404

    def test_hierarchy_returns_200(self, client):
        client.post("/plans", json={
            "title": "Test", "region_id": "r-1", "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        resp = client.get("/plans/by-region/r-1/hierarchy")
        assert resp.status_code == 200

    def test_update_process_step_returns_200(self, client):
        create_resp = client.post("/plans", json={
            "title": "Test", "region_id": "r-1", "hazard_types": ["flood"], "hierarchy_level": "local",
        })
        plan_id = create_resp.json()["plan_id"]
        resp = client.put(f"/plans/{plan_id}/process/steps/1", json={
            "is_complete": True, "notes": "Project plan established",
        })
        assert resp.status_code == 200
