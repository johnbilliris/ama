"""Scenario test — cyclone alert end-to-end (T060)."""

from unittest.mock import MagicMock, patch

from common.handoffs import AgentHandoffEvent
from communication.approval import ApprovalWorkflow
from communication.config import CommunicationConfig
from communication.models import (
    AlertStatus,
    SegmentPriority,
    UrgencyLevel,
)
from communication.pipeline import CommunicationProcessingPipeline
from communication.repository import CommunicationAlertRepository


class TestCycloneAlertScenario:
    """Full cyclone simulation through the communication pipeline."""

    def _build_cyclone_handoff(self) -> AgentHandoffEvent:
        return AgentHandoffEvent(
            handoff_id="handoff-cyclone-001",
            incident_id="INC-CYCLONE-2025",
            source_agent="risk_assessment",
            target_agent="communication",
            scope_key="INC-CYCLONE-2025",
            confidence=0.95,
            payload={
                "recommendationId": "rec-cyclone",
                "assessmentId": "assess-cyclone",
                "explanation": "Category 5 cyclone requires public warning",
                "hazard_type": "cyclone",
                "severity": "extreme",
                "urgency": "immediate",
                "location": "Cairns, QLD",
                "alert_type": "evacuation",
                "summary": "Category 5 cyclone approaching Cairns",
                "zones": [
                    {"level": 1, "boundary": {}, "population_estimate": 5000},
                    {"level": 2, "boundary": {}, "population_estimate": 15000},
                ],
            },
        )

    def _pipeline(self, config: CommunicationConfig | None = None) -> CommunicationProcessingPipeline:
        runtime_config = config or CommunicationConfig()
        repository = CommunicationAlertRepository()

        class _Store:
            def __init__(self, record):
                self.record = record

            def read_item(self, item, partition_key):
                return self.record

        class _Publisher:
            async def publish(self, payload):
                return None

        approval = ApprovalWorkflow(
            config=runtime_config,
            service_bus_client=_Publisher(),
            alert_repository=repository,
        )
        return CommunicationProcessingPipeline(
            config=runtime_config,
            incident_store=_Store({"id": "INC-CYCLONE-2025", "tenant_id": "live", "commander_chain": ["ic-1"]}),
            recommendation_store=_Store({"id": "rec-cyclone", "incident_id": "INC-CYCLONE-2025", "tenant_id": "live"}),
            assessment_store=_Store(
                {
                    "id": "assess-cyclone",
                    "incident_id": "INC-CYCLONE-2025",
                    "tenant_id": "live",
                    "hazard_type": "cyclone",
                    "severity": "extreme",
                    "location": "Cairns, QLD",
                    "zones": [
                        {"id": "zone-1", "level": 1, "boundary": {}, "population_estimate": 5000},
                        {"id": "zone-2", "level": 2, "boundary": {}, "population_estimate": 15000},
                    ],
                }
            ),
            alert_repository=repository,
            approval_workflow=approval,
        )

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_pipeline_produces_alert(self, mock_metrics, mock_emitter, mock_span, mock_llm):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Cyclone Warning | Cat 5 cyclone approaching. Evacuate. | Call 000.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        config = CommunicationConfig()
        pipeline = self._pipeline(config)

        event = self._build_cyclone_handoff()
        alert = pipeline.process_handoff(event)

        assert alert is not None
        assert alert.incident_id == "INC-CYCLONE-2025"
        assert alert.version >= 1
        assert alert.status == AlertStatus.pending_review

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_alert_has_en_au_content(self, mock_metrics, mock_emitter, mock_span, mock_llm):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Cyclone Warning | Severe cyclone inbound. | Evacuate now.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = self._pipeline()
        alert = pipeline.process_handoff(self._build_cyclone_handoff())

        assert alert is not None
        assert "en-AU" in alert.content_blocks

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_multiple_languages_requested(self, mock_metrics, mock_emitter, mock_span, mock_llm):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Alert Title | Alert Body. | Action items.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        config = CommunicationConfig()
        pipeline = self._pipeline(config)
        alert = pipeline.process_handoff(self._build_cyclone_handoff())

        assert alert is not None
        assert len(alert.content_blocks) == len(config.supported_languages)

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_zone1_immediate_high_priority(self, mock_metrics, mock_emitter, mock_span, mock_llm):
        """Zone 1 maps to urgency=immediate, priority=high."""
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Title | Body | Actions",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        from communication.segmentation import AudienceSegmenter

        segmenter = AudienceSegmenter()
        assessment_data = {
            "zones": [{"level": 1, "boundary": {}, "population_estimate": 5000}],
        }
        segments = segmenter.segment_audience(assessment_data)

        zone1_segments = [s for s in segments if s.zone_level == 1]
        assert len(zone1_segments) >= 1
        assert zone1_segments[0].urgency_level == UrgencyLevel.immediate
        assert zone1_segments[0].priority == SegmentPriority.high

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_approval_workflow_engaged(self, mock_metrics, mock_emitter, mock_span, mock_llm):
        """After pipeline processing, alert status is pending_review (approval engaged)."""
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Title | Body | Actions",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = self._pipeline()
        alert = pipeline.process_handoff(self._build_cyclone_handoff())

        assert alert is not None
        assert alert.status == AlertStatus.pending_review
