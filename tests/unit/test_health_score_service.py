"""Unit tests for HealthScoreService calculation algorithm (T032)."""

import pytest

from apps.api.app.services.health_score_service import HealthScoreService, DIMENSION_WEIGHTS


class TestHealthScoreService:
    def setup_method(self):
        self.service = HealthScoreService()

    def test_weighted_dimensions(self):
        """Verify correct weights: constitutional 40%, readiness 25%, DS 20%, recovery 15%."""
        assert DIMENSION_WEIGHTS["constitutional_compliance"] == 0.40
        assert DIMENSION_WEIGHTS["operational_readiness"] == 0.25
        assert DIMENSION_WEIGHTS["data_source_governance"] == 0.20
        assert DIMENSION_WEIGHTS["recovery_progress"] == 0.15
        assert sum(DIMENSION_WEIGHTS.values()) == pytest.approx(1.0)

    def test_all_perfect_scores(self):
        result = self.service.calculate(
            constitutional_gates=[{"status": "compliant"} for _ in range(10)],
            readiness_data={"exercise_completion_rate": 100, "role_coverage_pct": 100, "plan_currency_pct": 100},
            data_source_stats={"total": 10, "compliant": 10, "partially_compliant": 0},
            recovery_data={"has_active_recovery": False},
            tenant_id="live",
        )
        assert result.score == pytest.approx(100.0, abs=0.1)
        assert result.status == "green"

    def test_traffic_light_green(self):
        result = self.service.calculate(
            constitutional_gates=[{"status": "compliant"} for _ in range(10)],
            readiness_data={"exercise_completion_rate": 80, "role_coverage_pct": 80, "plan_currency_pct": 80},
            data_source_stats={"total": 10, "compliant": 8, "partially_compliant": 2},
            recovery_data={"has_active_recovery": False},
        )
        assert result.status == "green"

    def test_traffic_light_amber(self):
        result = self.service.calculate(
            constitutional_gates=[{"status": "compliant"} for _ in range(5)] + [{"status": "non_compliant"} for _ in range(5)],
            readiness_data={"exercise_completion_rate": 60, "role_coverage_pct": 60, "plan_currency_pct": 60},
            data_source_stats={"total": 10, "compliant": 5, "partially_compliant": 2},
            recovery_data={"has_active_recovery": False},
        )
        assert result.status == "amber"

    def test_traffic_light_red(self):
        result = self.service.calculate(
            constitutional_gates=[{"status": "non_compliant"} for _ in range(10)],
            readiness_data={"exercise_completion_rate": 20, "role_coverage_pct": 20, "plan_currency_pct": 20},
            data_source_stats={"total": 10, "compliant": 1, "partially_compliant": 0},
            recovery_data={"has_active_recovery": True, "domains": [{"completion_pct": 10}]},
        )
        assert result.status == "red"
        assert result.score < 50

    def test_assessment_pending_excluded_from_denominator(self):
        """Gates with 'assessment_pending' should not count against the score."""
        gates = [
            {"status": "compliant"},
            {"status": "compliant"},
            {"status": "assessment_pending"},  # excluded
        ]
        result = self.service.calculate(
            constitutional_gates=gates,
            readiness_data={},
            data_source_stats={},
            recovery_data={},
        )
        # 2 compliant out of 2 assessed = 100% constitutional
        const_dim = [d for d in result.dimensions if d.dimension == "constitutional_compliance"][0]
        assert const_dim.score == 100.0

    def test_no_active_recovery_is_100(self):
        """No active recovery = 100% recovery dimension."""
        result = self.service.calculate(
            constitutional_gates=[],
            readiness_data={},
            data_source_stats={},
            recovery_data={"has_active_recovery": False},
        )
        rec_dim = [d for d in result.dimensions if d.dimension == "recovery_progress"][0]
        assert rec_dim.score == 100.0

    def test_all_missing_data_score_zero_ish(self):
        """With no data, constitutional/readiness/DS = 0, recovery = 100 (no recovery)."""
        result = self.service.calculate(
            constitutional_gates=[],
            readiness_data={},
            data_source_stats={},
            recovery_data={},
        )
        # Only recovery = 100% × 0.15 = 15
        assert result.score == pytest.approx(15.0, abs=0.1)
        assert result.status == "red"

    def test_stale_data_flag(self):
        """Verify dimensions report stale=False by default."""
        result = self.service.calculate(
            constitutional_gates=[{"status": "compliant"}],
        )
        for dim in result.dimensions:
            assert dim.stale is False

    def test_has_active_incident_propagated(self):
        result = self.service.calculate(
            constitutional_gates=[],
            has_active_incident=True,
        )
        assert result.has_active_incident is True

    def test_tenant_id_in_result(self):
        result = self.service.calculate(
            constitutional_gates=[],
            tenant_id="sim-test123",
        )
        assert result.tenant_id == "sim-test123"
        assert result.id.startswith("health-score-sim-test123-")
