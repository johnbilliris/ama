"""Contract tests for Risk Assessment Agent escalation thresholds."""

from apps.agents.risk_assessment.agent import RiskAssessmentAgent
from packages.domain.src.domain.models.recommendation import Recommendation


def _make_recommendation(**overrides) -> Recommendation:
    """Build a Recommendation with sensible defaults, applying overrides."""
    defaults = {
        "recommendation_id": "rec-inc001-pa-001",
        "incident_id": "inc-001",
        "type": "public_alert",
        "summary": "Test alert",
        "explanation": "Test explanation with sig-001",
        "supporting_signal_ids": ["sig-001"],
        "required_approval_level": "incident_commander",
        "confidence_level": "high",
        "confidence_score": 0.85,
        "severity_level": "high",
        "assessment_id": "ha-inc001-spread-v1",
        "incident_scope_key": "live:inc-001",
        "tenant_id": "live",
    }
    defaults.update(overrides)
    return Recommendation(**defaults)


# ── Communication handoff (public_alert, threshold ≥ 0.7) ─────────


def test_communication_handoff_created_when_confidence_above_threshold() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(confidence_score=0.85)
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None


def test_communication_no_handoff_when_confidence_below_threshold() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(confidence_score=0.65)
    handoff = agent.build_communication_handoff(rec)

    assert handoff is None


def test_communication_handoff_payload_contains_required_fields() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(confidence_score=0.85)
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None
    payload = handoff.payload
    assert payload["recommendationId"] == rec.recommendation_id
    assert payload["summary"] == rec.summary
    assert payload["explanation"] == rec.explanation
    assert payload["assessmentId"] == rec.assessment_id


def test_communication_handoff_uses_numeric_confidence_score() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(confidence_score=0.85)
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None
    assert isinstance(handoff.confidence, float)
    assert handoff.confidence == 0.85


# ── Evacuation handoff (severity ≥ high AND confidence ≥ 0.6) ─────


def test_evacuation_handoff_created_when_severity_high_and_confidence_above_threshold() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="evacuation",
        severity_level="high",
        confidence_score=0.75,
    )
    handoff = agent.build_evacuation_handoff(rec)

    assert handoff is not None


def test_evacuation_no_handoff_when_severity_below_high() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="evacuation",
        severity_level="moderate",
        confidence_score=0.75,
    )
    handoff = agent.build_evacuation_handoff(rec)

    assert handoff is None


def test_evacuation_no_handoff_when_confidence_below_threshold() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="evacuation",
        severity_level="high",
        confidence_score=0.55,
    )
    handoff = agent.build_evacuation_handoff(rec)

    assert handoff is None


def test_evacuation_handoff_payload_contains_required_fields() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="evacuation",
        severity_level="high",
        confidence_score=0.75,
    )
    handoff = agent.build_evacuation_handoff(rec)

    assert handoff is not None
    payload = handoff.payload
    assert payload["recommendationId"] == rec.recommendation_id
    assert payload["summary"] == rec.summary
    assert payload["assessmentId"] == rec.assessment_id


# ── Resource Allocation handoff (coordination/resource_allocation type) ──


def test_resource_allocation_handoff_created_for_resource_allocation_type() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(type="resource_allocation")
    handoff = agent.build_resource_allocation_handoff(rec)

    assert handoff is not None


def test_resource_allocation_handoff_created_for_coordination_type() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(type="coordination")
    handoff = agent.build_resource_allocation_handoff(rec)

    assert handoff is not None


def test_resource_allocation_no_handoff_for_unrelated_type() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(type="public_alert")
    handoff = agent.build_resource_allocation_handoff(rec)

    assert handoff is None


def test_resource_allocation_handoff_payload_contains_required_fields() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(type="resource_allocation")
    handoff = agent.build_resource_allocation_handoff(rec)

    assert handoff is not None
    payload = handoff.payload
    assert payload["recommendationId"] == rec.recommendation_id
    assert payload["summary"] == rec.summary
    assert payload["assessmentId"] == rec.assessment_id
