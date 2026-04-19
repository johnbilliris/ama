"""Contract tests: Governance Dashboard API response schemas (T031)."""

import pytest
from pydantic import ValidationError

from apps.api.app.models.audit_export import AuditExportJobResponse
from apps.api.app.models.governance_health import (
    AuditTrailResponse,
    ComplianceMatrixResponse,
    DashboardConfigResponse,
    ExecutiveSummaryResponse,
    OperationalReadinessResponse,
    RecoveryProgressResponse,
    RiskWarningResponse,
)


class TestExecutiveSummaryContract:
    """Schema contract for GET /governance/dashboard/summary."""

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            ExecutiveSummaryResponse()  # missing required fields

    def test_valid_response(self):
        dims = [
            {
                "dimension": "constitutional_compliance",
                "score": 90.0,
                "weight": 0.40,
                "weighted_score": 36.0,
                "input_count": 10,
            },
            {
                "dimension": "operational_readiness",
                "score": 80.0,
                "weight": 0.25,
                "weighted_score": 20.0,
                "input_count": 4,
            },
            {
                "dimension": "data_source_governance",
                "score": 70.0,
                "weight": 0.20,
                "weighted_score": 14.0,
                "input_count": 5,
            },
            {"dimension": "recovery_progress", "score": 50.0, "weight": 0.15, "weighted_score": 7.5, "input_count": 5},
        ]
        gates = [
            {"gate_number": i, "gate_name": f"Gate {i}", "status": "compliant", "detail_url": f"/gates/{i}"}
            for i in range(1, 11)
        ]
        resp = ExecutiveSummaryResponse(
            health_score={
                "id": "health-score-live-2025",
                "tenant_id": "live",
                "score": 77.5,
                "status": "amber",
                "dimensions": dims,
                "calculated_at": "2025-01-01T00:00:00Z",
            },
            constitutional_gates=gates,
            active_incident_count=0,
            resource_utilisation_pct=55.0,
            risk_summary={"extreme": 0, "high": 1, "medium": 3, "low": 5},
            data_freshness="2025-01-01T00:00:00Z",
            tenant_id="live",
        )
        assert resp.tenant_id == "live"
        assert resp.active_incident_count == 0

    def test_data_freshness_required(self):
        """data_freshness must be present."""
        with pytest.raises(ValidationError):
            ExecutiveSummaryResponse(
                health_score={
                    "id": "hs-1",
                    "tenant_id": "live",
                    "score": 85.0,
                    "status": "green",
                    "dimensions": [],
                    "calculated_at": "2025-01-01T00:00:00Z",
                },
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
    """Schema contract for GET /governance/dashboard/audit."""

    def test_valid_response(self):
        resp = AuditTrailResponse(
            events=[],
            total_count=0,
            page_size=25,
            continuation_token=None,
            filters_applied={},
        )
        assert resp.total_count == 0


class TestOperationalReadinessContract:
    """Schema contract for GET /governance/dashboard/readiness."""

    def test_valid_response(self):
        pprr = [
            {"phase": "prevention", "is_active": False, "indicator_status": "inactive"},
            {"phase": "preparedness", "is_active": True, "indicator_status": "active"},
            {"phase": "response", "is_active": False, "indicator_status": "inactive"},
            {"phase": "recovery", "is_active": False, "indicator_status": "inactive"},
        ]
        resp = OperationalReadinessResponse(
            pprr_phases=pprr,
            emergency_plans=[],
            total_plans=0,
            overdue_plans_total=0,
            exercise_completion_rate_pct=75.0,
            exercise_breakdown=[],
            overall_readiness_score=70.0,
            aiims_role_coverage=[],
            overall_role_coverage_pct=80.0,
            capability_gap_count=2,
        )
        assert resp.exercise_completion_rate_pct == 75.0


class TestRecoveryProgressContract:
    """Schema contract for GET /governance/dashboard/recovery."""

    def test_valid_response_with_recovery(self):
        resp = RecoveryProgressResponse(
            has_active_recovery=True,
            domains=[],
            available_incidents=[{"incident_id": "inc-1", "title": "Test"}],
        )
        assert resp.has_active_recovery is True

    def test_valid_response_no_recovery(self):
        resp = RecoveryProgressResponse(
            has_active_recovery=False,
            domains=[],
            available_incidents=[],
        )
        assert resp.has_active_recovery is False


class TestRiskWarningContract:
    """Schema contract for GET /governance/dashboard/risk."""

    _PRINCIPLES = [
        ("life_saving", "Life Saving"),
        ("empowering", "Empowering"),
        ("trusted", "Trusted"),
        ("risk_scaled", "Risk Scaled"),
        ("timely_targeted", "Timely & Targeted"),
        ("impact_conveying", "Impact Conveying"),
        ("action_calling", "Action Calling"),
        ("clearly_communicated", "Clearly Communicated"),
        ("accessible", "Accessible"),
        ("bigger_picture", "Bigger Picture"),
    ]

    def test_valid_response(self):
        principle_compliance = [
            {
                "principle": pid,
                "display_name": name,
                "compliant_count": 8,
                "total_count": 10,
                "compliance_rate_pct": 80.0,
            }
            for pid, name in self._PRINCIPLES
        ]
        resp = RiskWarningResponse(
            risk_severity={"extreme": 0, "high": 1, "medium": 3, "low": 5, "total": 9},
            top_risks=[],
            treatment_closure_rate_pct=60.0,
            alert_compliance={
                "avg_approval_latency_s": 120.0,
                "acceptable_threshold_s": 300.0,
                "exceeds_threshold": False,
                "alerts_exceeding_threshold": [],
                "aws_tier_usage": {"emergency": 1, "watch": 2, "advice": 3},
                "broadcast_reach_pct": 80.0,
                "principle_compliance": principle_compliance,
                "overall_principle_compliance_pct": 80.0,
            },
        )
        assert resp.treatment_closure_rate_pct == 60.0


class TestDashboardConfigContract:
    """Schema contract for GET /governance/dashboard/config."""

    def test_valid_response(self):
        resp = DashboardConfigResponse(
            user_roles=["incident_controller"],
            default_view="executive_summary",
            widget_layout=[],
            poll_interval_ms=300000,
            has_active_incident=False,
            tenant_id="live",
            tenant_display_name="Live",
            is_simulation=False,
        )
        assert resp.poll_interval_ms == 300000
        assert resp.default_view == "executive_summary"


class TestAuditExportContract:
    """Schema contract for POST /governance/dashboard/audit/export."""

    def test_valid_response(self):
        resp = AuditExportJobResponse(
            id="export-123",
            status="queued",
        )
        assert resp.status == "queued"
