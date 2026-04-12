"""Contract tests for Risk Assessment Agent reproducibility guarantees."""

from apps.agents.risk_assessment.agent import RiskAssessmentAgent
from apps.agents.risk_assessment.config import RiskAssessmentConfig
from apps.agents.risk_assessment.correlation import (
    ContradictionResult,
    SignalCorrelator,
)


def _build_signals() -> list[dict]:
    return [
        {
            "signal_id": "sig-001",
            "confidence_score": 0.9,
            "freshness_score": 1.0,
            "source_kind": "authoritative",
            "category": "fire",
        },
    ]


# ── Deterministic output for identical inputs ────────────────────


def test_identical_inputs_produce_identical_confidence_and_severity() -> None:
    config = RiskAssessmentConfig()
    agent = RiskAssessmentAgent(config=config)

    signals = _build_signals()
    correlator = SignalCorrelator(config)
    correlation = correlator.compute_weighted_confidence(signals)
    contradiction = ContradictionResult()
    config_hash = config.compute_config_hash()

    assessment1 = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )
    assessment2 = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )

    assert assessment1.confidence_adjusted == assessment2.confidence_adjusted
    assert assessment1.severity_level == assessment2.severity_level


def test_identical_inputs_produce_identical_recommendation_types() -> None:
    config = RiskAssessmentConfig()
    agent = RiskAssessmentAgent(config=config)

    signals = _build_signals()
    correlator = SignalCorrelator(config)
    correlation = correlator.compute_weighted_confidence(signals)
    contradiction = ContradictionResult()
    config_hash = config.compute_config_hash()

    assessment1 = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )
    assessment2 = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )

    recs1 = agent.generate_recommendations(assessment1, signals)
    recs2 = agent.generate_recommendations(assessment2, signals)

    types1 = sorted(r.type for r in recs1)
    types2 = sorted(r.type for r in recs2)
    assert types1 == types2


# ── Configuration version tracking ───────────────────────────────


def test_configuration_version_tracked_in_assessment() -> None:
    config = RiskAssessmentConfig()
    agent = RiskAssessmentAgent(config=config)

    signals = _build_signals()
    correlator = SignalCorrelator(config)
    correlation = correlator.compute_weighted_confidence(signals)
    contradiction = ContradictionResult()
    config_hash = config.compute_config_hash()

    assessment = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )

    assert assessment.configuration_version == config_hash
    assert assessment.configuration_version != ""


# ── Input snapshot completeness ──────────────────────────────────


def test_input_snapshot_contains_all_signals_with_provenance() -> None:
    config = RiskAssessmentConfig()
    agent = RiskAssessmentAgent(config=config)

    signals = [
        {
            "signal_id": "sig-010",
            "confidence_score": 0.8,
            "freshness_score": 0.9,
            "source_kind": "iot",
            "category": "fire",
            "provenance": {"sensor_id": "s-42"},
        },
        {
            "signal_id": "sig-011",
            "confidence_score": 0.7,
            "freshness_score": 1.0,
            "source_kind": "authoritative",
            "category": "fire",
            "provenance": {"agency": "bom"},
        },
    ]
    correlator = SignalCorrelator(config)
    correlation = correlator.compute_weighted_confidence(signals)
    contradiction = ContradictionResult()
    config_hash = config.compute_config_hash()

    assessment = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )

    snapshot = assessment.input_snapshot
    assert "signals" in snapshot
    assert len(snapshot["signals"]) == 2

    for snap_signal in snapshot["signals"]:
        assert "signal_id" in snap_signal
        assert "confidence_score" in snap_signal
        assert "freshness_score" in snap_signal
        assert "source_kind" in snap_signal
        assert "provenance" in snap_signal

    ids = {s["signal_id"] for s in snapshot["signals"]}
    assert ids == {"sig-010", "sig-011"}


# ── Model deployment ID recorded ─────────────────────────────────


def test_model_deployment_id_recorded() -> None:
    config = RiskAssessmentConfig()
    agent = RiskAssessmentAgent(config=config)

    signals = _build_signals()
    correlator = SignalCorrelator(config)
    correlation = correlator.compute_weighted_confidence(signals)
    contradiction = ContradictionResult()
    config_hash = config.compute_config_hash()

    assessment = agent.generate_assessment(
        "inc-001", signals, correlation, contradiction,
        "spread_prediction", 1, config_hash,
    )

    snapshot = assessment.input_snapshot
    assert "model_deployment_id" in snapshot
    # Also recorded at the assessment level (None when no LLM available)
    assert hasattr(assessment, "model_deployment_id")
