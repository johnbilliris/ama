"""Contract tests for M&E framework API on the Monitoring Agent.

Validates all 8 M&E endpoints using TestClient against the monitoring
agent's create_app() FastAPI application.

FRs: FR-008–014
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from monitoring.agent import create_app


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def _create_framework(client, **overrides) -> dict:
    """Helper: create an M&E framework and return the response body."""
    payload = {
        "incident_id": "inc-100",
        "program_name": "Flood Recovery M&E",
        "affected_community_definition": "Lismore CBD residents",
        "created_by": "analyst-1",
        **overrides,
    }
    resp = client.post("/me-framework", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---- POST /me-framework ----


class TestCreateMEFramework:
    """POST /me-framework — create a new M&E framework (201)."""

    def test_create_returns_201_with_framework_id(self, client):
        body = _create_framework(client)
        assert "framework_id" in body
        assert body["framework_id"].startswith("mef-")
        assert body["incident_id"] == "inc-100"
        assert body["program_name"] == "Flood Recovery M&E"
        assert body["status"] == "configuring"

    def test_create_sets_evaluation_domains(self, client):
        body = _create_framework(client)
        domains = body["active_evaluation_domains"]
        assert len(domains) == 5
        assert "governance" in domains
        assert "community_engagement" in domains

    def test_create_initialises_empty_collections(self, client):
        body = _create_framework(client)
        assert body["selected_outcomes"] == []
        assert body["standards_of_success"] == []
        assert body["indicator_collection_schedule"] == []
        assert body["evaluation_reports"] == []
        assert body["program_logic_id"] is None


# ---- GET /me-framework/{framework_id} ----


class TestGetMEFramework:
    """GET /me-framework/{framework_id} — retrieve a framework (200)."""

    def test_get_existing_framework(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        resp = client.get(f"/me-framework/{fid}")
        assert resp.status_code == 200
        assert resp.json()["framework_id"] == fid

    def test_get_nonexistent_framework_returns_404(self, client):
        resp = client.get("/me-framework/mef-nonexistent")
        assert resp.status_code == 404


# ---- POST /me-framework/{framework_id}/outcomes ----


class TestSelectOutcomes:
    """POST /me-framework/{framework_id}/outcomes — select outcomes (200)."""

    def test_select_outcomes_returns_updated_framework(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        outcomes = [
            {"catalogue_outcome_id": "out-1", "domain": "built", "objective_type": "recovery"},
            {"catalogue_outcome_id": "out-2", "domain": "social", "objective_type": "resilience"},
        ]
        resp = client.post(f"/me-framework/{fid}/outcomes", json={"outcomes": outcomes})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["selected_outcomes"]) == 2
        assert body["updated_at"] is not None

    def test_select_outcomes_nonexistent_framework(self, client):
        resp = client.post(
            "/me-framework/mef-nonexistent/outcomes",
            json={"outcomes": []},
        )
        assert resp.status_code == 404


# ---- POST /me-framework/{framework_id}/program-logic ----


class TestCreateProgramLogic:
    """POST /me-framework/{framework_id}/program-logic — create logic (201)."""

    def test_create_program_logic_returns_201(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        logic_payload = {
            "model_type": "ex_ante",
            "resources_inputs": [{"name": "Funding", "amount": 500000}],
            "activities": [{"name": "Rebuild homes"}],
            "outputs": [{"name": "Homes rebuilt", "target": 50}],
        }
        resp = client.post(f"/me-framework/{fid}/program-logic", json=logic_payload)
        assert resp.status_code == 201
        body = resp.json()
        assert "model_id" in body
        assert body["model_id"].startswith("plm-")
        assert body["framework_id"] == fid

    def test_program_logic_links_to_framework(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        resp = client.post(f"/me-framework/{fid}/program-logic", json={"model_type": "ex_ante"})
        assert resp.status_code == 201
        model_id = resp.json()["model_id"]
        # Framework should now reference the logic model
        fw = client.get(f"/me-framework/{fid}").json()
        assert fw["program_logic_id"] == model_id

    def test_program_logic_nonexistent_framework(self, client):
        resp = client.post(
            "/me-framework/mef-nonexistent/program-logic",
            json={"model_type": "ex_ante"},
        )
        assert resp.status_code == 404


# ---- POST /me-framework/{framework_id}/standards ----


class TestSetStandards:
    """POST /me-framework/{framework_id}/standards — set standards (200)."""

    def test_set_standards_returns_updated_framework(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        standards = [
            {
                "catalogue_outcome_id": "out-1",
                "indicator_id": "ind-1",
                "threshold_value": 80,
                "threshold_operator": ">=",
            },
        ]
        resp = client.post(f"/me-framework/{fid}/standards", json={"standards": standards})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["standards_of_success"]) == 1

    def test_set_standards_nonexistent_framework(self, client):
        resp = client.post(
            "/me-framework/mef-nonexistent/standards",
            json={"standards": []},
        )
        assert resp.status_code == 404


# ---- POST /me-framework/{framework_id}/collection-schedule ----


class TestSetCollectionSchedule:
    """POST /me-framework/{framework_id}/collection-schedule — set schedule (200)."""

    def test_set_schedule_activates_framework(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        assert created["status"] == "configuring"
        schedules = [
            {"indicator_id": "ind-1", "frequency": "weekly", "next_due_date": "2026-02-01"},
        ]
        resp = client.post(f"/me-framework/{fid}/collection-schedule", json={"schedules": schedules})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "active"
        assert len(body["indicator_collection_schedule"]) == 1

    def test_set_schedule_nonexistent_framework(self, client):
        resp = client.post(
            "/me-framework/mef-nonexistent/collection-schedule",
            json={"schedules": []},
        )
        assert resp.status_code == 404


# ---- GET /me-framework/{framework_id}/monitoring-report ----


class TestGetMonitoringReport:
    """GET /me-framework/{framework_id}/monitoring-report — report (200)."""

    def test_monitoring_report_structure(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        resp = client.get(f"/me-framework/{fid}/monitoring-report")
        assert resp.status_code == 200
        body = resp.json()
        assert body["framework_id"] == fid
        assert body["incident_id"] == "inc-100"
        assert "indicators_status" in body
        assert "overdue_indicators" in body
        assert "staleness_warnings" in body
        assert "generated_at" in body

    def test_monitoring_report_nonexistent_framework(self, client):
        resp = client.get("/me-framework/mef-nonexistent/monitoring-report")
        assert resp.status_code == 404


# ---- POST /me-framework/{framework_id}/evaluation ----


class TestCreateEvaluation:
    """POST /me-framework/{framework_id}/evaluation — evaluation (201)."""

    def test_create_evaluation_returns_201(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        eval_payload = {
            "evaluation_period_start": "2026-01-01",
            "evaluation_period_end": "2026-06-30",
            "generated_by": "manual",
            "created_by": "analyst-1",
        }
        resp = client.post(f"/me-framework/{fid}/evaluation", json=eval_payload)
        assert resp.status_code == 201
        body = resp.json()
        assert "report_id" in body
        assert body["report_id"].startswith("er-")
        assert body["framework_id"] == fid
        assert body["generated_by"] == "manual"

    def test_evaluation_added_to_framework(self, client):
        created = _create_framework(client)
        fid = created["framework_id"]
        eval_payload = {
            "evaluation_period_start": "2026-01-01",
            "evaluation_period_end": "2026-06-30",
        }
        resp = client.post(f"/me-framework/{fid}/evaluation", json=eval_payload)
        assert resp.status_code == 201
        report_id = resp.json()["report_id"]
        fw = client.get(f"/me-framework/{fid}").json()
        assert report_id in fw["evaluation_reports"]

    def test_evaluation_nonexistent_framework(self, client):
        resp = client.post(
            "/me-framework/mef-nonexistent/evaluation",
            json={
                "evaluation_period_start": "2026-01-01",
                "evaluation_period_end": "2026-06-30",
            },
        )
        assert resp.status_code == 404


# ---- Full lifecycle test ----


class TestMEFrameworkLifecycle:
    """End-to-end lifecycle through all 8 endpoints."""

    def test_full_lifecycle(self, client):
        # 1. Create framework
        fw = _create_framework(client, program_name="Bushfire Recovery M&E")
        fid = fw["framework_id"]
        assert fw["status"] == "configuring"

        # 2. Select outcomes
        outcomes = [{"catalogue_outcome_id": "o1", "domain": "built", "objective_type": "recovery"}]
        resp = client.post(f"/me-framework/{fid}/outcomes", json={"outcomes": outcomes})
        assert resp.status_code == 200

        # 3. Create program logic
        resp = client.post(
            f"/me-framework/{fid}/program-logic",
            json={"model_type": "ex_ante", "activities": [{"name": "Rebuild"}]},
        )
        assert resp.status_code == 201

        # 4. Set standards
        standards = [{"indicator_id": "ind-1", "threshold_value": 75, "threshold_operator": ">="}]
        resp = client.post(f"/me-framework/{fid}/standards", json={"standards": standards})
        assert resp.status_code == 200

        # 5. Set collection schedule (activates framework)
        schedules = [{"indicator_id": "ind-1", "frequency": "monthly", "next_due_date": "2026-03-01"}]
        resp = client.post(f"/me-framework/{fid}/collection-schedule", json={"schedules": schedules})
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

        # 6. Get monitoring report
        resp = client.get(f"/me-framework/{fid}/monitoring-report")
        assert resp.status_code == 200
        assert resp.json()["framework_id"] == fid

        # 7. Create evaluation
        resp = client.post(
            f"/me-framework/{fid}/evaluation",
            json={"evaluation_period_start": "2026-01-01", "evaluation_period_end": "2026-06-30"},
        )
        assert resp.status_code == 201

        # 8. Verify framework state
        fw_final = client.get(f"/me-framework/{fid}").json()
        assert fw_final["status"] == "active"
        assert len(fw_final["selected_outcomes"]) == 1
        assert fw_final["program_logic_id"] is not None
        assert len(fw_final["evaluation_reports"]) == 1
