"""Unit tests for GovernanceHealthScore domain model validation (T029)."""

import pytest
from datetime import datetime, UTC

from packages.domain.src.domain.models.governance_health_score import (
    DimensionScore,
    GovernanceHealthScore,
    ConstitutionalGateStatus,
)


class TestDimensionScore:
    def test_valid_dimension(self):
        d = DimensionScore(
            dimension="constitutional_compliance",
            score=80.0,
            weight=0.40,
            weighted_score=32.0,
            input_count=10,
        )
        assert d.score == 80.0
        assert d.weight == 0.40

    def test_score_range_min(self):
        d = DimensionScore(
            dimension="operational_readiness",
            score=0.0, weight=0.25, weighted_score=0.0, input_count=0,
        )
        assert d.score == 0.0

    def test_score_range_max(self):
        d = DimensionScore(
            dimension="data_source_governance",
            score=100.0, weight=0.20, weighted_score=20.0, input_count=5,
        )
        assert d.score == 100.0

    def test_score_out_of_range_raises(self):
        with pytest.raises(Exception):
            DimensionScore(
                dimension="recovery_progress",
                score=101.0, weight=0.15, weighted_score=15.15, input_count=1,
            )


class TestGovernanceHealthScore:
    def _make_dimensions(self, scores=(80, 70, 60, 100)):
        weights = [0.40, 0.25, 0.20, 0.15]
        dims = ["constitutional_compliance", "operational_readiness", "data_source_governance", "recovery_progress"]
        return [
            DimensionScore(
                dimension=dim,
                score=float(score),
                weight=w,
                weighted_score=round(float(score) * w, 2),
                input_count=5,
            )
            for dim, score, w in zip(dims, scores, weights)
        ]

    def test_valid_health_score(self):
        dims = self._make_dimensions()
        composite = sum(d.weighted_score for d in dims)
        hs = GovernanceHealthScore(
            id="health-score-live-123",
            tenant_id="live",
            score=round(composite, 2),
            status=GovernanceHealthScore.derive_status(composite),
            dimensions=dims,
            calculated_at=datetime.now(UTC),
        )
        assert hs.score == round(composite, 2)
        assert len(hs.dimensions) == 4

    def test_status_green(self):
        assert GovernanceHealthScore.derive_status(80.0) == "green"
        assert GovernanceHealthScore.derive_status(100.0) == "green"

    def test_status_amber(self):
        assert GovernanceHealthScore.derive_status(79.0) == "amber"
        assert GovernanceHealthScore.derive_status(50.0) == "amber"

    def test_status_red(self):
        assert GovernanceHealthScore.derive_status(49.9) == "red"
        assert GovernanceHealthScore.derive_status(0.0) == "red"

    def test_dimension_weights_must_sum_to_one(self):
        bad_dims = [
            DimensionScore(dimension="constitutional_compliance", score=80, weight=0.50, weighted_score=40, input_count=1),
            DimensionScore(dimension="operational_readiness", score=70, weight=0.25, weighted_score=17.5, input_count=1),
            DimensionScore(dimension="data_source_governance", score=60, weight=0.20, weighted_score=12, input_count=1),
            DimensionScore(dimension="recovery_progress", score=50, weight=0.15, weighted_score=7.5, input_count=1),
        ]
        # Weights sum to 1.10 — should fail
        with pytest.raises(Exception):
            GovernanceHealthScore(
                id="test", tenant_id="live", score=77,
                status="amber", dimensions=bad_dims,
                calculated_at=datetime.now(UTC),
            )

    def test_score_mismatch_raises(self):
        dims = self._make_dimensions()
        with pytest.raises(Exception):
            GovernanceHealthScore(
                id="test", tenant_id="live", score=99.0,  # wrong
                status="green", dimensions=dims,
                calculated_at=datetime.now(UTC),
            )


class TestConstitutionalGateStatus:
    def test_valid_gate(self):
        g = ConstitutionalGateStatus(
            gate_number=1,
            gate_name="Primacy of Life",
            status="compliant",
            evidence_count=5,
            detail_url="/governance/dashboard/compliance?gate=1",
        )
        assert g.gate_number == 1
        assert g.status == "compliant"

    def test_gate_number_range(self):
        for num in range(1, 11):
            g = ConstitutionalGateStatus(
                gate_number=num, gate_name=f"Gate {num}",
                status="compliant", detail_url="/test",
            )
            assert g.gate_number == num

    def test_gate_number_out_of_range(self):
        with pytest.raises(Exception):
            ConstitutionalGateStatus(
                gate_number=0, gate_name="Invalid",
                status="compliant", detail_url="/test",
            )
        with pytest.raises(Exception):
            ConstitutionalGateStatus(
                gate_number=11, gate_name="Invalid",
                status="compliant", detail_url="/test",
            )
