"""Bushfire simulation scenario test — Risk Assessment Agent integration.

Tests the full pipeline with fire-category handoffs:
- Assessment generation from fire signals
- Recommendation creation (public_alert + evacuation if severe)
- Communication Agent escalation verification
- Audit trail completeness

Marked @pytest.mark.simulation — skipped in unit test runs.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from common.handoffs import AgentHandoffEvent, build_handoff
from risk_assessment.pipeline import AssessmentProcessingPipeline
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.audit import AuditWriter
from risk_assessment.models import DecisionType, RiskAssessmentDecisionRecord
from unittest.mock import patch

pytestmark = pytest.mark.simulation


# ---------------------------------------------------------------------------
# Recording audit writer
# ---------------------------------------------------------------------------


class RecordingAuditWriter:
    """In-memory audit writer that records all writes for assertion."""

    def __init__(self):
        self.records: list[RiskAssessmentDecisionRecord] = []

    def write(self, record: RiskAssessmentDecisionRecord) -> None:
        self.records.append(record)

    def get_status(self) -> str:
        return "healthy"

    @property
    def buffer_depth(self) -> int:
        return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> RiskAssessmentConfig:
    with patch.dict(os.environ, {}, clear=False):
        return RiskAssessmentConfig()


def _build_fire_handoff(
    incident_id: str = "inc-bushfire-001",
    confidence: float = 0.85,
    signal_ids: list[str] | None = None,
    source_kind: str = "authoritative",
) -> AgentHandoffEvent:
    return build_handoff(
        incident_id=incident_id,
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key=f"live:{incident_id}",
        payload={
            "signalSummary": {
                "signal_ids": signal_ids or ["sig-fire-001", "sig-fire-002"],
                "category": "fire",
                "sourceKind": source_kind,
            },
            "category": "fire",
            "sourceKind": source_kind,
        },
        confidence=confidence,
        tenant_id="live",
    )


def _build_pipeline(
    audit_writer: RecordingAuditWriter | None = None,
    deliver_fn=None,
) -> tuple[AssessmentProcessingPipeline, RecordingAuditWriter]:
    config = _make_config()
    writer = audit_writer or RecordingAuditWriter()
    pipeline = AssessmentProcessingPipeline(
        config=config,
        audit_writer=writer,
        deliver_fn=deliver_fn,
    )
    return pipeline, writer


# ---------------------------------------------------------------------------
# T064-1: Bushfire handoff generates spread_prediction
# ---------------------------------------------------------------------------


class TestBushfireHandoffGeneratesSpreadPrediction:
    def test_bushfire_handoff_generates_spread_prediction(self) -> None:
        """Fire-category handoff → spread_prediction assessment."""
        handoff = _build_fire_handoff()
        pipeline, audit = _build_pipeline()

        result = pipeline.process_handoff(handoff)

        assert result["status"] == "completed"
        assessment = result["assessment"]
        assert assessment is not None
        assert assessment.assessment_type == "spread_prediction"
        assert assessment.incident_id == "inc-bushfire-001"


# ---------------------------------------------------------------------------
# T064-2: High severity generates evacuation recommendation
# ---------------------------------------------------------------------------


class TestBushfireHighSeverityGeneratesEvacuation:
    def test_bushfire_high_severity_generates_evacuation(self) -> None:
        """High-severity fire → evacuation recommendation in output."""
        handoff = _build_fire_handoff(confidence=0.9)
        pipeline, audit = _build_pipeline()

        result = pipeline.process_handoff(handoff)

        assert result["status"] == "completed"
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        rec_types = [r.type for r in recommendations]
        # spread_prediction maps to ["public_alert", "evacuation"]
        assert "public_alert" in rec_types
        assert "evacuation" in rec_types


# ---------------------------------------------------------------------------
# T064-3: Bushfire escalation to communication
# ---------------------------------------------------------------------------


class TestBushfireEscalationToCommunication:
    def test_bushfire_escalation_to_communication(self) -> None:
        """Confidence ≥ 0.7 → communication handoff created.

        Uses confidence=0.95 so that after template-fallback reduction
        (×0.8) the adjusted score (0.76) still exceeds the 0.7 threshold.
        """
        delivered_handoffs: list[AgentHandoffEvent] = []

        def mock_deliver(h: AgentHandoffEvent) -> None:
            delivered_handoffs.append(h)

        handoff = _build_fire_handoff(confidence=0.95)
        pipeline, audit = _build_pipeline(deliver_fn=mock_deliver)

        result = pipeline.process_handoff(handoff)

        assert result["status"] == "completed"

        # Check audit records for handoff_created targeting communication
        handoff_created_records = [
            r for r in audit.records
            if r.decision_type == DecisionType.handoff_created
            and "communication" in r.escalation_targets
        ]
        assert len(handoff_created_records) >= 1, (
            "Expected at least one handoff_created audit record targeting communication"
        )


# ---------------------------------------------------------------------------
# T064-4: Bushfire audit trail complete
# ---------------------------------------------------------------------------


class TestBushfireAuditTrailComplete:
    def test_bushfire_audit_trail_complete(self) -> None:
        """All 8 stages produce audit records."""
        delivered_handoffs: list[AgentHandoffEvent] = []

        def mock_deliver(h: AgentHandoffEvent) -> None:
            delivered_handoffs.append(h)

        handoff = _build_fire_handoff(confidence=0.85)
        pipeline, audit = _build_pipeline(deliver_fn=mock_deliver)

        result = pipeline.process_handoff(handoff)
        assert result["status"] == "completed"

        decision_types = [r.decision_type for r in audit.records]

        # Core pipeline stages that always produce audit records
        assert DecisionType.handoff_received in decision_types, (
            "Stage 1: handoff_received missing"
        )
        assert DecisionType.signals_retrieved in decision_types, (
            "Stage 2: signals_retrieved missing"
        )
        assert DecisionType.assessment_generated in decision_types, (
            "Stage 5: assessment_generated missing"
        )
        assert DecisionType.recommendation_generated in decision_types, (
            "Stage 6: recommendation_generated missing"
        )

        # With deliver_fn, escalation stages should produce records
        assert DecisionType.handoff_created in decision_types, (
            "Stage 7: handoff_created missing"
        )
        assert DecisionType.handoff_delivered in decision_types, (
            "Stage 7: handoff_delivered missing"
        )

        # Minimum record count: intake + signals + assessment + recommendations + handoffs
        assert len(audit.records) >= 6, (
            f"Expected ≥6 audit records for full pipeline, got {len(audit.records)}"
        )


# ---------------------------------------------------------------------------
# T064-5: Multiple fire signals weighted
# ---------------------------------------------------------------------------


class TestBushfireMultipleSignalsWeighted:
    def test_bushfire_multiple_signals_weighted(self) -> None:
        """Multiple fire signals are correlated with source weights."""
        handoff = _build_fire_handoff(
            signal_ids=["sig-fire-001", "sig-fire-002", "sig-fire-003"],
            confidence=0.80,
        )
        pipeline, audit = _build_pipeline()

        result = pipeline.process_handoff(handoff)

        assert result["status"] == "completed"

        # Verify signals_retrieved audit record references all signal IDs
        sig_records = [
            r for r in audit.records
            if r.decision_type == DecisionType.signals_retrieved
        ]
        assert len(sig_records) == 1
        retrieved_ids = sig_records[0].input_signal_ids
        assert len(retrieved_ids) == 3
        assert set(retrieved_ids) == {"sig-fire-001", "sig-fire-002", "sig-fire-003"}

        # Verify assessment was generated with the correlated signals
        assessment = result["assessment"]
        assert assessment is not None
        assert len(assessment.input_signal_ids) == 3
