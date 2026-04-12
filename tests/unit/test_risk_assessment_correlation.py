"""Tests for risk_assessment.correlation – SignalCorrelator & ContradictionDetector."""

import pytest
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.correlation import (
    ContradictionDetector,
    SignalCorrelator,
)


def _signal(
    signal_id="sig-1",
    source_kind="authoritative",
    confidence=0.8,
    freshness=1.0,
    direction="increasing",
    hazard_parameter="general",
):
    return {
        "signal_id": signal_id,
        "source_kind": source_kind,
        "confidence_score": confidence,
        "freshness_score": freshness,
        "risk_direction": direction,
        "hazard_parameter": hazard_parameter,
    }


# ---------------------------------------------------------------------------
# SignalCorrelator
# ---------------------------------------------------------------------------


class TestSignalCorrelator:
    def test_single_authoritative_signal(self):
        correlator = SignalCorrelator()
        result = correlator.compute_weighted_confidence(
            [_signal(confidence=0.9, source_kind="authoritative")]
        )
        assert 0.85 <= result.weighted_confidence <= 0.95
        assert result.signal_count == 1

    def test_authoritative_weight_higher(self):
        correlator = SignalCorrelator()
        auth = _signal(signal_id="s1", source_kind="authoritative", confidence=0.9)
        social = _signal(signal_id="s2", source_kind="social", confidence=0.3)
        result = correlator.compute_weighted_confidence([auth, social])
        # Authoritative (weight 2.0) dominates over social (weight 0.5)
        assert result.weighted_confidence > 0.5

    def test_mixed_sources_diversity(self):
        correlator = SignalCorrelator()
        signals = [
            _signal(signal_id="s1", source_kind="authoritative", confidence=0.8),
            _signal(signal_id="s2", source_kind="iot", confidence=0.7),
            _signal(signal_id="s3", source_kind="social", confidence=0.6),
        ]
        result = correlator.compute_weighted_confidence(signals)
        assert result.source_diversity == 3
        assert result.source_kinds == {"authoritative", "iot", "social"}

    def test_stale_signal_flagged(self):
        correlator = SignalCorrelator()
        signals = [
            _signal(signal_id="s1", freshness=0.3),  # below 0.5 threshold
            _signal(signal_id="s2", freshness=0.9),
        ]
        result = correlator.compute_weighted_confidence(signals)
        assert "s1" in result.stale_signal_ids
        assert "s2" not in result.stale_signal_ids

    def test_all_stale_signals_low_confidence(self):
        correlator = SignalCorrelator()
        signals = [
            _signal(signal_id="s1", freshness=0.1, confidence=0.9),
            _signal(signal_id="s2", freshness=0.2, confidence=0.8),
        ]
        result = correlator.compute_weighted_confidence(signals)
        assert result.all_stale is True

    def test_single_source_assessment(self):
        correlator = SignalCorrelator()
        result = correlator.compute_weighted_confidence(
            [_signal(signal_id="s1", source_kind="iot", confidence=0.6)]
        )
        assert result.source_diversity == 1
        assert result.signal_count == 1

    def test_relies_on_unverified_when_majority_social(self):
        correlator = SignalCorrelator()
        # 5 social signals (weight 0.5 each = 2.5) vs 1 authoritative (weight 2.0)
        # social_weight / total_weight = 2.5 / 4.5 > 0.5
        signals = [
            _signal(signal_id="s1", source_kind="social", confidence=0.7),
            _signal(signal_id="s2", source_kind="social", confidence=0.6),
            _signal(signal_id="s3", source_kind="social", confidence=0.7),
            _signal(signal_id="s4", source_kind="social", confidence=0.6),
            _signal(signal_id="s5", source_kind="social", confidence=0.5),
            _signal(signal_id="s6", source_kind="authoritative", confidence=0.8),
        ]
        result = correlator.compute_weighted_confidence(signals)
        assert result.relies_on_unverified is True


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------


class TestContradictionDetector:
    def test_two_opposing_signals_detected(self):
        detector = ContradictionDetector()
        signals = [
            _signal(signal_id="s1", direction="increasing"),
            _signal(signal_id="s2", direction="decreasing"),
        ]
        result = detector.detect(signals)
        assert result.detected is True
        assert len(result.pairs) >= 1

    def test_three_way_single_reduction(self):
        detector = ContradictionDetector()
        signals = [
            _signal(signal_id="s1", direction="increasing"),
            _signal(signal_id="s2", direction="decreasing"),
            _signal(signal_id="s3", direction="stable"),
        ]
        result = detector.detect(signals)
        assert result.detected is True

    def test_no_contradiction_when_consistent(self):
        detector = ContradictionDetector()
        signals = [
            _signal(signal_id="s1", direction="increasing"),
            _signal(signal_id="s2", direction="increasing"),
        ]
        result = detector.detect(signals)
        assert result.detected is False
        assert len(result.pairs) == 0

    def test_apply_contradiction_penalty(self):
        config = RiskAssessmentConfig()
        detector = ContradictionDetector(config=config)
        signals = [
            _signal(signal_id="s1", direction="increasing"),
            _signal(signal_id="s2", direction="decreasing"),
        ]
        contradiction = detector.detect(signals)
        adjusted = detector.apply_contradiction_penalty(0.8, contradiction)
        # 0.8 * 0.7 = 0.56
        assert adjusted == pytest.approx(0.8 * config.contradiction_reduction_factor, rel=0.01)

    def test_no_penalty_when_no_contradictions(self):
        detector = ContradictionDetector()
        signals = [
            _signal(signal_id="s1", direction="increasing"),
            _signal(signal_id="s2", direction="increasing"),
        ]
        contradiction = detector.detect(signals)
        adjusted = detector.apply_contradiction_penalty(0.8, contradiction)
        assert adjusted == pytest.approx(0.8, rel=0.01)
