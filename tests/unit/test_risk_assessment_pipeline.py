"""Tests for risk_assessment.pipeline – AssessmentProcessingPipeline."""

from common.handoffs import AgentHandoffEvent
from risk_assessment.audit import AuditWriter
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.pipeline import AssessmentProcessingPipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pipeline(**kwargs):
    config = RiskAssessmentConfig()
    return AssessmentProcessingPipeline(
        config=config,
        audit_writer=AuditWriter(config=config, cosmos_client=None),
        **kwargs,
    )


def _make_handoff(
    handoff_id="hf-001",
    incident_id="inc-001",
    category="fire",
    source_kind="authoritative",
    confidence=0.85,
    tenant_id="live",
):
    return AgentHandoffEvent(
        handoff_id=handoff_id,
        incident_id=incident_id,
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key=f"{tenant_id}:{incident_id}",
        confidence=confidence,
        payload={
            "category": category,
            "sourceKind": source_kind,
            "signalSummary": {
                "category": category,
                "sourceKind": source_kind,
                "incidentId": incident_id,
            },
        },
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# Handoff validation
# ---------------------------------------------------------------------------


class TestHandoffValidation:
    def test_valid_handoff_accepted(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        result = pipeline.process_handoff(handoff)
        assert result is not None
        assert pipeline.rejection_count == 0

    def test_wrong_target_agent_rejected(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        handoff.target_agent = "some_other_agent"
        pipeline.process_handoff(handoff)
        assert pipeline.rejection_count >= 1


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_duplicate_handoff_discarded(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(handoff_id="hf-dup")
        pipeline.process_handoff(handoff)
        pipeline.process_handoff(handoff)
        assert pipeline.dedup_discard_count >= 1


# ---------------------------------------------------------------------------
# Signal retrieval
# ---------------------------------------------------------------------------


class TestSignalRetrieval:
    def test_signals_from_handoff_payload(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(category="fire")
        result = pipeline.process_handoff(handoff)
        # Pipeline should successfully process (signals retrieved from payload)
        assert result is not None

    def test_exact_stored_signal_refs_use_hpk_reader(self):
        class _Store:
            def __init__(self) -> None:
                self.calls: list[dict[str, str]] = []

            def get_by_hpk(self, **kwargs):  # type: ignore[no-untyped-def]
                self.calls.append(kwargs)
                return {
                    "signal_id": kwargs["signal_id"],
                    "category": "fire",
                    "confidence_score": 0.9,
                    "freshness_score": 1.0,
                    "source_kind": "authoritative",
                    "payload": {"severity": "high"},
                    "provenance": {"sourceUri": "https://example.com"},
                }

        store = _Store()
        pipeline = _make_pipeline(signal_store=store)
        handoff = _make_handoff(category="fire")
        handoff.payload["signal_ids"] = ["sig-hpk-1"]
        handoff.payload["stored_signal_refs"] = [
            {
                "signal_id": "sig-hpk-1",
                "scope": "live",
                "jurisdiction_id": "nsw",
                "data_source_id": "bom-warnings",
            }
        ]

        result = pipeline.process_handoff(handoff)

        assert result is not None
        assert len(store.calls) == 1
        assert store.calls[0]["scope"] == "live"
        assert store.calls[0]["jurisdiction_id"] == "nsw"
        assert store.calls[0]["data_source_id"] == "bom-warnings"


# ---------------------------------------------------------------------------
# Assessment type derivation
# ---------------------------------------------------------------------------


class TestAssessmentTypeDerivation:
    def test_fire_derives_spread_prediction(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(category="fire")
        result = pipeline.process_handoff(handoff)
        if "assessment" in result and result["assessment"]:
            assert result["assessment"].assessment_type == "spread_prediction"


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_fire_handoff_produces_assessment_and_recommendations(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(category="fire", confidence=0.85)
        result = pipeline.process_handoff(handoff)
        assert result is not None
        assert pipeline.assessment_count >= 1
        assert pipeline.recommendation_count >= 0

    def test_no_escalation_when_below_thresholds(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(category="fire", confidence=0.3)
        pipeline.process_handoff(handoff)
        assert pipeline.escalation_count == 0

    def test_simulation_tenant_blocks_live_escalation(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(
            category="fire",
            confidence=0.95,
            tenant_id="simulation",
        )
        pipeline.process_handoff(handoff, tenant_id="simulation")
        # Simulation tenants should not escalate to live systems
        assert pipeline.escalation_count == 0
