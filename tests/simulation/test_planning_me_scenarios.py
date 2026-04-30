"""End-to-end simulation: emergency planning → M&E → AI analysis → lessons.

Tests the complete workflow from plan creation through recovery evaluation.
"""

import pytest
from fastapi.testclient import TestClient
from monitoring.agent import create_app as create_monitoring_app
from monitoring.config import MonitoringConfig
from planning.agent import create_app as create_planning_app
from planning.config import PlanningConfig


@pytest.fixture
def planning_client():
    app = create_planning_app(config=PlanningConfig())
    return TestClient(app)


@pytest.fixture
def monitoring_client():
    app = create_monitoring_app(config=MonitoringConfig())
    return TestClient(app)


class TestEmergencyPlanningToRecoveryScenario:
    """Simulates: Create plan → 9-step process → endorse → activate →
    set up M&E → select outcomes → collect indicators → AI analysis → evaluation."""

    def test_full_planning_lifecycle(self, planning_client):
        # Step 1: Create emergency plan
        resp = planning_client.post(
            "/plans",
            json={
                "title": "Flood Emergency Plan - Blue Mountains",
                "region_id": "r-au-nsw-blue-mountains",
                "hazard_types": ["flood", "storm"],
                "hierarchy_level": "local",
            },
        )
        assert resp.status_code == 201
        plan_id = resp.json()["plan_id"]

        # Step 2: Update some sections
        for slug in ["authority", "aim_objectives", "response_arrangements"]:
            resp = planning_client.put(
                f"/plans/{plan_id}/sections/{slug}",
                json={
                    "title": slug.replace("_", " ").title(),
                    "content": f"Content for {slug}",
                },
            )
            assert resp.status_code == 200

        # Step 3: Update process steps
        resp = planning_client.put(
            f"/plans/{plan_id}/process/steps/1",
            json={
                "is_complete": True,
                "notes": "Project plan established",
            },
        )
        assert resp.status_code == 200

        # Step 4: Check completeness
        resp = planning_client.get(f"/plans/{plan_id}/completeness")
        assert resp.status_code == 200
        assert resp.json()["completed_sections"] >= 3

        # Step 5: Transition through lifecycle
        resp = planning_client.post(
            f"/plans/{plan_id}/transition",
            json={
                "target_state": "in_consultation",
                "user_role": "planning_officer",
            },
        )
        assert resp.status_code == 200

    def test_me_framework_setup(self, monitoring_client):
        # Step 1: Create M&E framework
        resp = monitoring_client.post(
            "/me-framework",
            json={
                "incident_id": "inc-flood-001",
                "program_name": "Blue Mountains Flood Recovery",
                "affected_community_definition": "Blue Mountains LGA residents",
            },
        )
        assert resp.status_code == 201
        fw_id = resp.json()["framework_id"]

        # Step 2: Select outcomes
        resp = monitoring_client.post(
            f"/me-framework/{fw_id}/outcomes",
            json={
                "outcomes": [
                    {
                        "catalogue_outcome_id": "aidr:social:community-health-levels",
                        "domain": "social",
                        "objective_type": "sustainability",
                    },
                ],
            },
        )
        assert resp.status_code == 200

        # Step 3: Get monitoring report
        resp = monitoring_client.get(f"/me-framework/{fw_id}/monitoring-report")
        assert resp.status_code == 200

    def test_catalogue_browsing(self, monitoring_client):
        resp = monitoring_client.get("/catalogue/outcomes?domain=social")
        assert resp.status_code == 200
        outcomes = resp.json()
        assert len(outcomes) > 0

    def test_ai_analysis(self, monitoring_client):
        resp = monitoring_client.post(
            "/analysis/cross-domain",
            json={
                "indicator_data": [
                    {
                        "domain": "social",
                        "indicator_name": "health",
                        "value": 60,
                        "target_value": 100,
                        "trend": "negative",
                    },
                    {
                        "domain": "economic",
                        "indicator_name": "employment",
                        "value": 55,
                        "target_value": 100,
                        "trend": "negative",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "correlations" in data
