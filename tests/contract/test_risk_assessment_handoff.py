"""Contract tests for Risk Assessment Agent handoff structure."""

from apps.agents.risk_assessment.agent import RiskAssessmentAgent
from packages.domain.src.domain.models.recommendation import Recommendation


def _make_recommendation(**overrides) -> Recommendation:
    """Build a Recommendation with sensible defaults, applying overrides."""
    defaults = {
        "recommendation_id": "rec-inc002-pa-001",
        "incident_id": "inc-002",
        "type": "public_alert",
        "summary": "Test alert summary",
        "explanation": "Explanation referencing sig-002",
        "supporting_signal_ids": ["sig-002"],
        "required_approval_level": "incident_commander",
        "confidence_level": "high",
        "confidence_score": 0.9,
        "severity_level": "high",
        "assessment_id": "ha-inc002-spread-v1",
        "incident_scope_key": "live:inc-002",
        "tenant_id": "test-tenant",
    }
    defaults.update(overrides)
    return Recommendation(**defaults)


# ── source_agent is always "risk_assessment" ──────────────────────


def test_outbound_handoff_source_agent_is_risk_assessment() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation()
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None
    assert handoff.source_agent == "risk_assessment"


# ── target_agent routing ─────────────────────────────────────────


def test_communication_handoff_target_agent() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(type="public_alert", confidence_score=0.9)
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None
    assert handoff.target_agent == "communication"


def test_evacuation_handoff_target_agent() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="evacuation",
        severity_level="high",
        confidence_score=0.8,
    )
    handoff = agent.build_evacuation_handoff(rec)

    assert handoff is not None
    assert handoff.target_agent == "evacuation"


def test_resource_allocation_handoff_target_agent() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(type="resource_allocation")
    handoff = agent.build_resource_allocation_handoff(rec)

    assert handoff is not None
    assert handoff.target_agent == "resource_allocation"


# ── Payload required fields ──────────────────────────────────────


def test_handoff_payload_contains_recommendation_id_and_summary() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation()
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None
    assert "recommendationId" in handoff.payload
    assert "summary" in handoff.payload
    assert handoff.payload["recommendationId"] == rec.recommendation_id
    assert handoff.payload["summary"] == rec.summary


# ── tenant_id propagation ────────────────────────────────────────


def test_tenant_id_propagated_from_recommendation() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(tenant_id="tenant-abc")
    handoff = agent.build_communication_handoff(rec)

    assert handoff is not None
    assert handoff.tenant_id == "tenant-abc"


def test_tenant_id_propagated_for_evacuation_handoff() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="evacuation",
        severity_level="critical",
        confidence_score=0.8,
        tenant_id="tenant-xyz",
    )
    handoff = agent.build_evacuation_handoff(rec)

    assert handoff is not None
    assert handoff.tenant_id == "tenant-xyz"


def test_tenant_id_propagated_for_resource_allocation_handoff() -> None:
    agent = RiskAssessmentAgent()
    rec = _make_recommendation(
        type="resource_allocation",
        tenant_id="tenant-ops",
    )
    handoff = agent.build_resource_allocation_handoff(rec)

    assert handoff is not None
    assert handoff.tenant_id == "tenant-ops"
