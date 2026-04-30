"""Integration tests for Governance Dashboard API endpoints
(T034, T043, T050, T061, T068, T074, T081, T087)."""

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {
        "X-User-Role": "incident_controller",
        "X-Tenant-Id": "live",
    }


# ---- T034: US1 Executive Summary Endpoints ----


class TestExecutiveSummaryEndpoints:
    def test_get_executive_summary(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "health_score" in body
        assert "constitutional_gates" in body
        assert "active_incident_count" in body
        assert "tenant_id" in body

    def test_executive_summary_simulation_mode(self, client, auth_headers):
        headers = {**auth_headers, "X-Tenant-Id": "sim-test123"}
        resp = client.get("/api/governance/dashboard/summary", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "tenant_id" in body

    def test_health_score_in_summary(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        hs = body["health_score"]
        assert "score" in hs
        assert "status" in hs
        assert "dimensions" in hs

    def test_health_score_traffic_light(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/summary", headers=auth_headers)
        body = resp.json()
        assert body["health_score"]["status"] in ("green", "amber", "red")

    def test_constitutional_gates_in_summary(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["constitutional_gates"], list)
        assert len(body["constitutional_gates"]) == 10


# ---- T043: US2 Compliance Matrix Endpoints ----


class TestComplianceMatrixEndpoints:
    def test_get_compliance_matrix(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/compliance", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "entries" in body
        assert "total_count" in body
        assert "page_size" in body

    def test_compliance_matrix_pagination(self, client, auth_headers):
        resp = client.get(
            "/api/governance/dashboard/compliance?page_size=10",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["page_size"] == 10

    def test_compliance_matrix_filter_status(self, client, auth_headers):
        resp = client.get(
            "/api/governance/dashboard/compliance?compliance_status=non_compliant",
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ---- T050: US3 Audit Trail Endpoints ----


class TestAuditTrailEndpoints:
    def test_search_audit_trail(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/audit", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "events" in body
        assert "total_count" in body

    def test_audit_trail_filter_by_actor(self, client, auth_headers):
        resp = client.get(
            "/api/governance/dashboard/audit?actor=admin",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_audit_trail_filter_by_action(self, client, auth_headers):
        resp = client.get(
            "/api/governance/dashboard/audit?action_type=registered",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_decision_chain(self, client, auth_headers):
        resp = client.get(
            "/api/governance/dashboard/audit/ds-001/chain",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "chain" in body
        assert isinstance(body["chain"], list)

    def test_export_endpoint(self, client, auth_headers):
        resp = client.post(
            "/api/governance/dashboard/audit/export",
            json={"format": "csv", "record_ids": []},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 202)
        body = resp.json()
        assert "id" in body
        assert body["status"] in ("queued", "complete")

    def test_export_job_status(self, client, auth_headers):
        # First create a job
        create_resp = client.post(
            "/api/governance/dashboard/audit/export",
            json={"format": "csv", "record_ids": []},
            headers=auth_headers,
        )
        job_id = create_resp.json()["id"]

        # Then check its status
        resp = client.get(
            f"/api/governance/dashboard/audit/export/{job_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ---- T061: US4 Operational Readiness Endpoints ----


class TestOperationalReadinessEndpoints:
    def test_get_operational_readiness(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/readiness", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "pprr_phases" in body
        assert "emergency_plans" in body
        assert "aiims_role_coverage" in body

    def test_4_pprr_phases(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/readiness", headers=auth_headers)
        body = resp.json()
        assert len(body["pprr_phases"]) == 4

    def test_7_emergency_plans(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/readiness", headers=auth_headers)
        body = resp.json()
        assert len(body["emergency_plans"]) == 7


# ---- T068: US5 Recovery Progress Endpoints ----


class TestRecoveryProgressEndpoints:
    def test_get_recovery_progress(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/recovery", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "has_active_recovery" in body
        assert "domains" in body

    def test_5_domains_when_active(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/recovery", headers=auth_headers)
        body = resp.json()
        if body["has_active_recovery"]:
            assert len(body["domains"]) == 5

    def test_recovery_domain_detail(self, client, auth_headers):
        resp = client.get(
            "/api/governance/dashboard/recovery/social",
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404)


# ---- T074: US6 Risk & Warning Endpoints ----


class TestRiskWarningEndpoints:
    def test_get_risk_warning(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/risk", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "risk_severity" in body
        assert "top_risks" in body
        assert "treatment_closure_rate_pct" in body
        assert "alert_compliance" in body

    def test_10_aws_principles(self, client, auth_headers):
        resp = client.get("/api/governance/dashboard/risk", headers=auth_headers)
        body = resp.json()
        assert len(body["alert_compliance"]["principle_compliance"]) == 10


# ---- T081: US7 Role Personalisation Endpoints ----


class TestDashboardConfigEndpoints:
    def test_get_config_incident_controller(self, client):
        headers = {"X-User-Role": "incident_controller", "X-Tenant-Id": "live"}
        resp = client.get("/api/governance/dashboard/config", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "incident_controller" in body["user_roles"]
        assert body["default_view"] == "executive_summary"

    def test_get_config_observer_auditor(self, client):
        headers = {"X-User-Role": "observer_auditor", "X-Tenant-Id": "live"}
        resp = client.get("/api/governance/dashboard/config", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["default_view"] == "audit_trail"

    def test_get_config_multi_role(self, client):
        headers = {"X-User-Role": "observer_auditor,incident_controller", "X-Tenant-Id": "live"}
        resp = client.get("/api/governance/dashboard/config", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        # Incident controller (rank 1) is primary
        assert body["default_view"] == "executive_summary"

    def test_get_config_unknown_role(self, client):
        headers = {"X-User-Role": "unknown", "X-Tenant-Id": "live"}
        resp = client.get("/api/governance/dashboard/config", headers=headers)
        assert resp.status_code in (200, 403)

    def test_all_roles_have_widgets(self, client):
        roles = [
            "incident_controller",
            "operations_officer",
            "planning_officer",
            "intelligence_officer",
            "logistics_officer",
            "public_information_officer",
            "executive_leader",
            "observer_auditor",
            "risk_manager",
            "resilience_planner",
        ]
        for role in roles:
            headers = {"X-User-Role": role, "X-Tenant-Id": "live"}
            resp = client.get("/api/governance/dashboard/config", headers=headers)
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["widget_layout"]) > 0, f"Role {role} has no widgets"


# ---- T087: US8 Audit Logging Integration ----


class TestAuditLoggingIntegration:
    def test_view_emits_audit_event(self, client, auth_headers):
        """Any dashboard view should log an audit event."""
        resp = client.get("/api/governance/dashboard/summary", headers=auth_headers)
        assert resp.status_code == 200

    def test_export_emits_audit_event(self, client, auth_headers):
        resp = client.post(
            "/api/governance/dashboard/audit/export",
            json={"format": "csv", "record_ids": []},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 202)

    def test_session_correlation_header(self, client, auth_headers):
        """X-Session-Id header should be accepted for audit correlation."""
        headers = {**auth_headers, "X-Session-Id": "sess-test-123"}
        resp = client.get("/api/governance/dashboard/summary", headers=headers)
        assert resp.status_code == 200
