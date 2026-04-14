"""Contract tests for recovery catalogue API endpoints.

Verifies endpoint existence, request/response shapes, and status codes.
"""
import pytest
from fastapi.testclient import TestClient

# The catalogue endpoints will be on the monitoring agent
from monitoring.agent import create_app
from monitoring.config import MonitoringConfig


@pytest.fixture
def client():
    config = MonitoringConfig()
    app = create_app(config=config)
    return TestClient(app)


class TestCatalogueEndpoints:
    def test_list_outcomes_returns_200(self, client):
        resp = client.get("/catalogue/outcomes")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_outcomes_by_domain(self, client):
        resp = client.get("/catalogue/outcomes?domain=social")
        assert resp.status_code == 200

    def test_get_outcome_not_found_404(self, client):
        resp = client.get("/catalogue/outcomes/nonexistent")
        assert resp.status_code == 404

    def test_get_domain_summary(self, client):
        resp = client.get("/catalogue/domains/social/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "domain" in data
        assert "outcome_count" in data

    def test_get_evaluation_questions(self, client):
        resp = client.get("/catalogue/evaluation-questions/governance")
        assert resp.status_code == 200

    def test_suggest_activities(self, client):
        resp = client.post("/catalogue/suggest-activities", json={
            "lagging_indicator_ids": ["aidr:social:community-health-levels:ind:1"],
        })
        assert resp.status_code == 200


class TestAnalysisEndpoints:
    """Contract tests for AI analysis endpoints on the monitoring agent."""

    def test_cross_domain_analysis(self, client):
        resp = client.post("/analysis/cross-domain", json={
            "indicator_data": [
                {"domain": "social", "indicator_name": "health", "trend": "negative",
                 "value": 0.3, "target_value": 1.0},
                {"domain": "economic", "indicator_name": "employment", "trend": "positive",
                 "value": 0.8, "target_value": 1.0},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "analysis_id" in data
        assert "correlations" in data

    def test_recommendations_endpoint(self, client):
        resp = client.post("/analysis/recommendations", json={
            "lagging_indicator_ids": ["aidr:social:community-health-levels:ind:1"],
        })
        assert resp.status_code == 200

    def test_community_summary_endpoint(self, client):
        resp = client.post("/analysis/community-summary", json={
            "indicator_data": [
                {"domain": "social", "indicator_name": "health", "trend": "positive"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
