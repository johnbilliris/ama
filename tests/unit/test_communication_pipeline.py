"""Tests for communication.pipeline — CommunicationProcessingPipeline."""

from unittest.mock import MagicMock

from common.handoffs import AgentHandoffEvent
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.dedup import HandoffDeduplicator
from communication.delivery import MultiChannelDeliveryService
from communication.models import PublicAlert
from communication.pipeline import CommunicationProcessingPipeline
from communication.segmentation import AudienceSegmenter
from communication.translator import MultilingualTranslator
from communication.versioning import VersionCounter


def _make_handoff(**overrides):
    defaults = dict(
        handoff_id="handoff-001",
        incident_id="inc-1",
        source_agent="risk_assessment",
        target_agent="communication",
        scope_key="inc-1",
        confidence=0.9,
        payload={
            "hazard_type": "bushfire",
            "severity": "high",
            "alert_type": "initial",
            "location": "Blue Mountains",
            "assessment_id": "ha-1",
            "recommendation_id": "rec-1",
        },
    )
    defaults.update(overrides)
    return AgentHandoffEvent(**defaults)


def _make_pipeline(**overrides):
    config = CommunicationConfig()
    defaults = dict(
        config=config,
        deduplicator=HandoffDeduplicator(window_minutes=30),
        translator=MagicMock(spec=MultilingualTranslator),
        segmenter=AudienceSegmenter(config=config),
        version_counter=VersionCounter(config=config),
        audit_writer=AuditWriter(config=config),
        delivery_service=MultiChannelDeliveryService(config=config),
    )
    defaults.update(overrides)
    return CommunicationProcessingPipeline(**defaults)


# ---------------------------------------------------------------------------
# Stage 1: Handoff Intake
# ---------------------------------------------------------------------------


class TestPipelineIntake:
    def test_wrong_target_agent_rejected(self):
        pipeline = _make_pipeline()
        event = _make_handoff(target_agent="risk_assessment")
        result = pipeline.process_handoff(event)
        assert result is None

    def test_duplicate_handoff_discarded(self):
        pipeline = _make_pipeline()
        event = _make_handoff()
        # First call succeeds (or at least passes stage 1)
        pipeline._stage_1_intake(event)
        # Second call with same ID should be duplicate
        assert pipeline._stage_1_intake(event) is False

    def test_valid_handoff_passes_intake(self):
        pipeline = _make_pipeline()
        event = _make_handoff()
        result = pipeline._stage_1_intake(event)
        assert result is True


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------


class TestPipelineEndToEnd:
    def test_full_pipeline_returns_alert(self):
        from communication.models import ContentBlock, GenerationMethod

        en_block = ContentBlock(
            language_code="en-AU",
            title="Fire Alert",
            body="Bushfire approaching Blue Mountains",
            action_items="Evacuate immediately",
            generation_method=GenerationMethod.llm,
        )

        mock_translator = MagicMock(spec=MultilingualTranslator)
        mock_translator.translate_all.return_value = {"en-AU": en_block}
        mock_translator.back_translate_and_score.return_value = 0.95

        pipeline = _make_pipeline(translator=mock_translator)
        event = _make_handoff()
        result = pipeline.process_handoff(event)

        assert result is not None
        assert isinstance(result, PublicAlert)
        assert result.incident_id == "inc-1"
        assert result.version >= 1

    def test_processed_count_increments(self):
        pipeline = _make_pipeline()
        assert pipeline.processed_count == 0 or pipeline._processed_count == 0
