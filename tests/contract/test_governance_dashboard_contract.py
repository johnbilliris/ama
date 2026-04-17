"""Contract tests: Governance Dashboard API response schemas (T031)."""

import pytest
from pydantic import ValidationError

from apps.api.app.models.governance_health import (
    ExecutiveSummaryResponse,
    ComplianceMatrixResponse,
    AuditTrailResponse,
    OperationalReadinessResponse,
    RecoveryProgressResponse,
    RiskWarningResponse,
    DashboardConfigResponse,
)
from apps.api.app.models.audit_export import AuditExportJobResponse


class TestExecutiveSummaryContract:
    """Schema contract for GET /governance/dashboard/executive-summary."""

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            ExecutiveSummaryResponse()  # missing required fields

    def test_valid_response(self):
        resp = ExecutiveSummaryResponse(
            health_score={"score": 85.0, "status": "green", "dimensions": []},
            constitutional_gates=[],
            active_incident_count=0,
            resource_utilisation_pct=55.0,
            risk_summary={"extreme": 0, "high": 1, "medium": 3, "low": 5},
            data_freshness={"last_updated": "2025-01-01T00:00:00Z", "stale": False},
            tenant_id="live",
        )
        assert resp.tenant_id == "live"
        assert resp.active_incident_count == 0

    def test_data_freshness_required(self):
        """data_freshness must be present."""
        with pytest.raises(ValidationError):
            ExecutiveSummaryResponse(
                health_score={"score": 85.0, "status": "green"},
                constitutional_gates=[],
                active_incident_count=0,
                resource_utilisation_pct=55.0,
                risk_summary={},
                # missing data_freshness
                tenant_id="live",
            )


class TestComplianceMatrixContract:
    """Schema contract for GET /governance/dashboard/compliance-matrix."""

    def test_valid_response(self):
        resp = ComplianceMatrixResponse(
            entries=[],
            total_count=0,
            page_size=50,
            continuation_token=None,
            filters_applied={},
        )
        assert resp.total_count == 0
        assert resp.page_size == 50


class TestAuditTrailContract:
    """Schema contract for GET /governance/dashboard/audit-trail."""

    def test_valid_response(self):
        resp = AuditTrailResponse(
            entries=[],
            total_count=0,
            page_size=25,
            continuation_token=None,
            filters_applied={},
        )
        assert resp.total_count == 0


class TestOperationalReadinessContract:
    """Schema contract for GET /governance/dashboard/operational-readiness."""

    def test_valid_response(self):
        resp = OperationalReadinessResponse(
            pprr_phases=[],
            emergency_plans=[],
            aiims_role_coverage=[],
            exercise_completion_rate_pct=75.0,
            capability_gap_count=2,
            tenant_id="live",
        )
        assert resp.exercise_completion_rate_pct == 75.0


class TestRecoveryProgressContract:
    """Schema contract for GET /governance/dashboard/recovery-progress."""

    def test_valid_response_with_recovery(self):
        resp = RecoveryProgressResponse(
            has_active_recovery=True,
            domains=[],
            overall_completion_pct=45.0,
            tenant_id="live",
        )
        assert resp.has_active_recovery is True

    def test_valid_response_no_recovery(self):
        resp = RecoveryProgressResponse(
            has_active_recovery=False,
            domains=[],
            overall_completion_pct=0.0,
            tenant_id="live",
        )
        assert resp.has_active_recovery is False


class TestRiskWarningContract:
    """Schema contract for GET /governance/dashboard/risk-warning."""

    def test_valid_response(self):
        resp = RiskWarningResponse(
            risk_severity={"extreme": 0, "high": 1, "medium": 3, "low": 5},
            top_risks=[],
            treatment_closure_rate_pct=60.0,
            alert_compliance={
                "principle_compliance": [],
                "broadcast_reach_pct": 80.0,
            },
            active_warnings=[],
            tenant_id="live",
        )
        assert resp.treatment_closure_rate_pct == 60.0


class TestDashboardConfigContract:
    """Schema contract for GET /governance/dashboard/config."""

    def test_valid_response(self):
        resp = DashboardConfigResponse(
            roles=["incident_controller"],
            default_view="executive_summary",
            widgets=[],
            refresh_interval_ms=300000,
        )
        assert resp.refresh_interval_ms == 300000
        assert resp.default_view == "executive_summary"


class TestAuditExportContract:
    """Schema contract for POST /governance/dashboard/audit-trail/export."""

    def test_valid_response(self):
        resp = AuditExportJobResponse(
            job_id="export-123",
            status="queued",
            format="csv",
            requested_at="2025-01-01T00:00:00Z",
            estimated_record_count=100,
        )
        assert resp.status == "queued"
