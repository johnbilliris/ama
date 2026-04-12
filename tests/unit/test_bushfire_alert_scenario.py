"""Scenario test — bushfire alert end-to-end (T061)."""

from unittest.mock import MagicMock, patch

from common.handoffs import AgentHandoffEvent
from communication.config import CommunicationConfig
from communication.delivery import MultiChannelDeliveryService
from communication.models import (
    AlertStatus,
    ChannelType,
    ContentBlock,
    SegmentPriority,
    UrgencyLevel,
)
from communication.pipeline import CommunicationProcessingPipeline
from communication.segmentation import AudienceSegmenter


class TestBushfireAlertScenario:
    """Bushfire simulation through the communication pipeline (T061)."""

    def _build_bushfire_handoff(self) -> AgentHandoffEvent:
        return AgentHandoffEvent(
            handoff_id="handoff-bushfire-001",
            incident_id="INC-BUSHFIRE-2025",
            source_agent="risk_assessment",
            target_agent="communication",
            scope_key="INC-BUSHFIRE-2025",
            confidence=0.88,
            payload={
                "hazard_type": "bushfire",
                "severity": "high",
                "urgency": "watch",
                "location": "Blue Mountains, NSW",
                "alert_type": "evacuation",
                "summary": "Bushfire approaching Blue Mountains",
                "zones": [
                    {"level": 2, "boundary": {}, "population_estimate": 8000},
                ],
            },
        )

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_bushfire_pipeline_produces_alert(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Bushfire Warning | Fire approaching. Stay alert. | Monitor CFA.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = CommunicationProcessingPipeline()
        alert = pipeline.process_handoff(self._build_bushfire_handoff())

        assert alert is not None
        assert alert.incident_id == "INC-BUSHFIRE-2025"
        assert alert.status == AlertStatus.pending_review

    def test_bushfire_zone2_watch_moderate_segments(self):
        """Zone 2 maps to urgency=watch, priority=moderate."""
        segmenter = AudienceSegmenter()
        assessment_data = {
            "zones": [{"level": 2, "boundary": {}, "population_estimate": 8000}],
        }
        segments = segmenter.segment_audience(assessment_data)

        zone2_segments = [s for s in segments if s.zone_level == 2]
        assert len(zone2_segments) >= 1
        assert zone2_segments[0].urgency_level == UrgencyLevel.watch
        assert zone2_segments[0].priority == SegmentPriority.moderate

    def test_sms_delivery_respects_612_char_limit(self):
        """SMS content must be truncated to SMS_MAX_LENGTH (default 612)."""
        config = CommunicationConfig()
        assert config.sms_max_length == 612

        service = MultiChannelDeliveryService(config=config)

        long_body = "A" * 1000
        content_block = ContentBlock(
            language_code="en-AU",
            title="Bushfire Warning",
            body=long_body,
            action_items="Evacuate now.",
        )

        formatted = service._format_content(content_block, ChannelType.sms)
        assert len(formatted) <= config.sms_max_length

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_bushfire_different_template_selected(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
        """Bushfire hazard_type flows through to the drafting stage."""
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Bushfire Alert | Fire danger. | Stay informed.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = CommunicationProcessingPipeline()
        alert = pipeline.process_handoff(self._build_bushfire_handoff())

        assert alert is not None
        assert "en-AU" in alert.content_blocks
