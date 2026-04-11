"""Scenario test — cyclone alert end-to-end (T060)."""

from unittest.mock import MagicMock, patch

import pytest

from common.handoffs import AgentHandoffEvent
from communication.config import CommunicationConfig
from communication.models import (
    AlertStatus,
    ContentBlock,
    GenerationMethod,
    SegmentPriority,
    UrgencyLevel,
)
from communication.pipeline import CommunicationProcessingPipeline


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

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_pipeline_produces_alert(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Cyclone Warning | Cat 5 cyclone approaching. Evacuate. | Call 000.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        config = CommunicationConfig()
        pipeline = CommunicationProcessingPipeline(config=config)

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
    def test_cyclone_alert_has_en_au_content(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Cyclone Warning | Severe cyclone inbound. | Evacuate now.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = CommunicationProcessingPipeline()
        alert = pipeline.process_handoff(self._build_cyclone_handoff())

        assert alert is not None
        assert "en-AU" in alert.content_blocks

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_multiple_languages_requested(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Alert Title | Alert Body. | Action items.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        config = CommunicationConfig()
        pipeline = CommunicationProcessingPipeline(config=config)
        alert = pipeline.process_handoff(self._build_cyclone_handoff())

        assert alert is not None
        assert len(alert.content_blocks) == len(config.supported_languages)

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_cyclone_zone1_immediate_high_priority(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
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
    def test_cyclone_approval_workflow_engaged(
        self, mock_metrics, mock_emitter, mock_span, mock_llm
    ):
        """After pipeline processing, alert status is pending_review (approval engaged)."""
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Title | Body | Actions",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = CommunicationProcessingPipeline()
        alert = pipeline.process_handoff(self._build_cyclone_handoff())

        assert alert is not None
        assert alert.status == AlertStatus.pending_review
