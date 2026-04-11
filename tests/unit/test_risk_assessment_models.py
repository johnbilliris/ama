"""Tests for risk_assessment.models and domain model validation."""

from datetime import UTC, datetime, timedelta

import pytest

from risk_assessment.models import (
    AssessmentType,
    AuditBufferEntry,
    ConfidenceLevel,
    DecisionType,
    RiskAssessmentDecisionRecord,
    SeverityLevel,
    confidence_to_level,
)
from packages.domain.src.domain.models.hazard_assessment import (
    HazardAssessment,
    HazardMap,
)
from packages.domain.src.domain.models.recommendation import Recommendation


# ---------------------------------------------------------------------------
# DecisionType enum
# ---------------------------------------------------------------------------


class TestDecisionType:
    def test_has_exactly_twelve_values(self):
        assert len(DecisionType) == 12

    def test_all_expected_values_present(self):
        expected = {
            "handoff_received",
            "handoff_rejected",
            "duplicate_discarded",
            "signals_retrieved",
            "assessment_generated",
            "recommendation_generated",
            "handoff_created",
            "handoff_delivered",
            "handoff_dead_lettered",
            "contradiction_detected",
            "degradation_detected",
            "content_safety_failure",
        }
        assert {e.value for e in DecisionType} == expected


# ---------------------------------------------------------------------------
# AssessmentType enum
# ---------------------------------------------------------------------------


class TestAssessmentType:
    def test_has_five_values(self):
        assert len(AssessmentType) == 5

    def test_expected_values(self):
        expected = {
            "spread_prediction",
            "impact_projection",
            "route_risk",
            "infrastructure_risk",
            "community_impact",
        }
        assert {e.value for e in AssessmentType} == expected


# ---------------------------------------------------------------------------
# ConfidenceLevel enum
# ---------------------------------------------------------------------------


class TestConfidenceLevel:
    def test_has_three_values(self):
        assert len(ConfidenceLevel) == 3

    def test_expected_values(self):
        assert {e.value for e in ConfidenceLevel} == {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# SeverityLevel enum
# ---------------------------------------------------------------------------


class TestSeverityLevel:
    def test_has_four_values(self):
        assert len(SeverityLevel) == 4

    def test_expected_values(self):
        assert {e.value for e in SeverityLevel} == {
            "low",
            "moderate",
            "high",
            "critical",
        }


# ---------------------------------------------------------------------------
# confidence_to_level
# ---------------------------------------------------------------------------


class TestConfidenceToLevel:
    @pytest.mark.parametrize(
        "score, expected",
        [
            (0.0, ConfidenceLevel.low),
            (0.39, ConfidenceLevel.low),
            (0.4, ConfidenceLevel.medium),
            (0.5, ConfidenceLevel.medium),
            (0.69, ConfidenceLevel.medium),
            (0.7, ConfidenceLevel.high),
            (0.85, ConfidenceLevel.high),
            (1.0, ConfidenceLevel.high),
        ],
    )
    def test_maps_correctly(self, score, expected):
        assert confidence_to_level(score) == expected


# ---------------------------------------------------------------------------
# RiskAssessmentDecisionRecord
# ---------------------------------------------------------------------------


class TestRiskAssessmentDecisionRecord:
    def test_required_fields(self):
        record = RiskAssessmentDecisionRecord(
            handoff_id="hf-1",
            decision_type=DecisionType.handoff_received,
        )
        assert record.handoff_id == "hf-1"
        assert record.decision_type == DecisionType.handoff_received

    def test_confidence_clamped_above_one(self):
        record = RiskAssessmentDecisionRecord(
            handoff_id="hf-2",
            decision_type=DecisionType.assessment_generated,
            confidence_raw=1.5,
            confidence_adjusted=2.0,
        )
        assert record.confidence_raw == 1.0
        assert record.confidence_adjusted == 1.0

    def test_confidence_clamped_below_zero(self):
        record = RiskAssessmentDecisionRecord(
            handoff_id="hf-3",
            decision_type=DecisionType.assessment_generated,
            confidence_raw=-0.5,
            confidence_adjusted=-1.0,
        )
        assert record.confidence_raw == 0.0
        assert record.confidence_adjusted == 0.0

    def test_default_values(self):
        record = RiskAssessmentDecisionRecord(
            handoff_id="hf-4",
            decision_type=DecisionType.handoff_received,
        )
        assert record.input_signal_ids == []
        assert record.confidence_raw == 0.0
        assert record.confidence_adjusted == 0.0
        assert record.agent_version == "0.1.0"
        assert record.prompt_template_version == "1.0"
        assert record.generation_method == "llm"

    def test_missing_handoff_id_raises(self):
        with pytest.raises(Exception):
            RiskAssessmentDecisionRecord(
                decision_type=DecisionType.handoff_received,
            )

    def test_missing_decision_type_raises(self):
        with pytest.raises(Exception):
            RiskAssessmentDecisionRecord(handoff_id="hf-5")


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class TestAuditBufferEntry:
    def test_wraps_record(self):
        record = RiskAssessmentDecisionRecord(
            handoff_id="hf-6",
            decision_type=DecisionType.handoff_received,
        )
        entry = AuditBufferEntry(record=record)
        assert entry.record.handoff_id == "hf-6"
        assert entry.retry_count == 0
        assert entry.last_retry_at is None
        assert entry.buffered_at is not None


# ---------------------------------------------------------------------------
# HazardAssessment domain model
# ---------------------------------------------------------------------------


class TestHazardAssessment:
    def _minimal(self, **overrides):
        now = datetime.now(UTC)
        defaults = dict(
            hazard_assessment_id="ha-1",
            incident_id="inc-1",
            assessment_type="spread_prediction",
            summary="Test summary",
            confidence_level="medium",
            generated_at=now,
            valid_until=now + timedelta(hours=2),
        )
        defaults.update(overrides)
        return HazardAssessment(**defaults)

    def test_valid_construction(self):
        ha = self._minimal()
        assert ha.hazard_assessment_id == "ha-1"

    def test_version_defaults_to_one(self):
        ha = self._minimal()
        assert ha.version >= 1

    def test_valid_until_must_be_after_generated_at(self):
        now = datetime.now(UTC)
        with pytest.raises(Exception):
            self._minimal(generated_at=now, valid_until=now - timedelta(hours=1))

    def test_confidence_score_in_range(self):
        ha = self._minimal(confidence_score=0.5)
        assert 0.0 <= ha.confidence_score <= 1.0

    def test_hazard_map_embedded(self):
        hm = HazardMap(
            affected_area={"lat": -33.8, "lng": 151.2, "radius_km": 10},
            severity_level="high",
            hazard_type="fire",
            confidence_score=0.8,
            time_horizon="24h",
            population_estimate=5000,
        )
        ha = self._minimal(hazard_map=hm)
        assert ha.hazard_map.hazard_type == "fire"
        assert ha.hazard_map.population_estimate == 5000


class TestHazardMap:
    def test_valid_construction(self):
        hm = HazardMap(
            affected_area={"lat": -33.8, "lng": 151.2},
            severity_level="high",
            hazard_type="fire",
            confidence_score=0.9,
            time_horizon="12h",
        )
        assert hm.severity_level == "high"

    def test_confidence_score_range(self):
        with pytest.raises(Exception):
            HazardMap(
                affected_area={"lat": 0, "lng": 0},
                severity_level="low",
                hazard_type="test",
                confidence_score=1.5,
                time_horizon="1h",
            )


# ---------------------------------------------------------------------------
# Recommendation domain model
# ---------------------------------------------------------------------------


class TestRecommendation:
    def _minimal(self, **overrides):
        defaults = dict(
            recommendation_id="rec-1",
            incident_id="inc-1",
            type="evacuation",
            summary="Evacuate area",
            explanation="Fire approaching",
            required_approval_level="incident_commander",
        )
        defaults.update(overrides)
        return Recommendation(**defaults)

    def test_valid_construction(self):
        rec = self._minimal()
        assert rec.recommendation_id == "rec-1"

    def test_confidence_score_valid_range(self):
        rec = self._minimal(confidence_score=0.5)
        assert rec.confidence_score == 0.5

    def test_confidence_score_above_one_raises(self):
        with pytest.raises(Exception):
            self._minimal(confidence_score=1.1)

    def test_confidence_score_below_zero_raises(self):
        with pytest.raises(Exception):
            self._minimal(confidence_score=-0.1)

    def test_default_status_is_proposed(self):
        rec = self._minimal()
        assert rec.status == "proposed"

    def test_default_generation_method_is_template(self):
        rec = self._minimal()
        assert rec.generation_method == "template"
