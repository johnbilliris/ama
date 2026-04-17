"""Unit tests for DashboardAggregationService (T033, T042, T060, T067, T073)."""

import pytest
from datetime import datetime, UTC

from apps.api.app.services.dashboard_aggregation_service import DashboardAggregationService


class TestGetExecutiveSummary:
    """T033: Tests for DashboardAggregationService.get_executive_summary()."""

    def setup_method(self):
        self.service = DashboardAggregationService()

    def test_returns_correct_shape(self):
        result = self.service.get_executive_summary(tenant_id="live")
        assert hasattr(result, "health_score")
        assert hasattr(result, "constitutional_gates")
        assert hasattr(result, "active_incident_count")
        assert hasattr(result, "resource_utilisation_pct")
        assert hasattr(result, "risk_summary")
        assert hasattr(result, "data_freshness")
        assert hasattr(result, "tenant_id")

    def test_constitutional_gates_count_10(self):
        result = self.service.get_executive_summary(tenant_id="live")
        assert len(result.constitutional_gates) == 10

    def test_risk_summary_has_4_severities(self):
        result = self.service.get_executive_summary(tenant_id="live")
        assert "extreme" in result.risk_summary
        assert "high" in result.risk_summary
        assert "medium" in result.risk_summary
        assert "low" in result.risk_summary

    def test_active_incident_count_non_negative(self):
        result = self.service.get_executive_summary(tenant_id="live")
        assert result.active_incident_count >= 0

    def test_tenant_id_passed_through(self):
        result = self.service.get_executive_summary(tenant_id="sim-test")
        assert result.tenant_id == "sim-test"


class TestGetComplianceMatrix:
    """T042: Tests for compliance matrix retrieval."""

    def setup_method(self):
        self.service = DashboardAggregationService()

    def test_pagination_default(self):
        result = self.service.get_compliance_matrix(tenant_id="live")
        assert hasattr(result, "entries")
        assert hasattr(result, "total_count")
        assert hasattr(result, "continuation_token")
        assert result.page_size == 50

    def test_filter_by_compliance_status(self):
        result = self.service.get_compliance_matrix(
            tenant_id="live", compliance_status="non_compliant",
        )
        assert hasattr(result, "filters_applied")
        assert result.filters_applied.get("compliance_status") == "non_compliant"


class TestGetOperationalReadiness:
    """T060: Tests for operational readiness."""

    def setup_method(self):
        self.service = DashboardAggregationService()

    def test_4_pprr_phases(self):
        result = self.service.get_operational_readiness(tenant_id="live")
        assert len(result.pprr_phases) == 4
        phases = {p.phase for p in result.pprr_phases}
        assert phases == {"prevention", "preparedness", "response", "recovery"}

    def test_7_plan_lifecycle_states(self):
        result = self.service.get_operational_readiness(tenant_id="live")
        assert len(result.emergency_plans) == 7

    def test_10_role_coverage(self):
        result = self.service.get_operational_readiness(tenant_id="live")
        assert len(result.aiims_role_coverage) == 10

    def test_capability_gap_count_non_negative(self):
        result = self.service.get_operational_readiness(tenant_id="live")
        assert result.capability_gap_count >= 0


class TestGetRecoveryProgress:
    """T067: Tests for recovery progress."""

    def setup_method(self):
        self.service = DashboardAggregationService()

    def test_5_domains_returned(self):
        result = self.service.get_recovery_progress(tenant_id="live")
        if result.has_active_recovery:
            assert len(result.domains) == 5

    def test_overarching_is_average(self):
        result = self.service.get_recovery_progress(tenant_id="live")
        if result.has_active_recovery and len(result.domains) == 5:
            overarching = [d for d in result.domains if d.domain == "overarching"][0]
            concrete = [d for d in result.domains if not d.is_cross_cutting]
            avg = sum(d.completion_pct for d in concrete) / len(concrete)
            assert abs(overarching.completion_pct - avg) < 1.0

    def test_no_active_recovery(self):
        # Subclass to simulate no recovery
        class NoRecoveryService(DashboardAggregationService):
            def _has_active_recovery(self, tenant_id):
                return False

        service = NoRecoveryService()
        result = service.get_recovery_progress(tenant_id="live")
        assert result.has_active_recovery is False
        assert len(result.domains) == 0

    def test_domain_detail(self):
        detail = self.service.get_recovery_domain_detail("social", tenant_id="live")
        assert detail is not None
        assert detail.domain == "social"

    def test_invalid_domain_returns_none(self):
        detail = self.service.get_recovery_domain_detail("invalid", tenant_id="live")
        assert detail is None


class TestGetRiskAndWarning:
    """T073: Tests for risk and warning data."""

    def setup_method(self):
        self.service = DashboardAggregationService()

    def test_risk_severity_counts(self):
        result = self.service.get_risk_and_warning(tenant_id="live")
        assert result.risk_severity.extreme >= 0
        assert result.risk_severity.high >= 0
        assert result.risk_severity.medium >= 0
        assert result.risk_severity.low >= 0

    def test_treatment_closure_rate(self):
        result = self.service.get_risk_and_warning(tenant_id="live")
        assert 0 <= result.treatment_closure_rate_pct <= 100

    def test_10_aws_principles(self):
        result = self.service.get_risk_and_warning(tenant_id="live")
        assert len(result.alert_compliance.principle_compliance) == 10

    def test_broadcast_reach(self):
        result = self.service.get_risk_and_warning(tenant_id="live")
        assert 0 <= result.alert_compliance.broadcast_reach_pct <= 100
