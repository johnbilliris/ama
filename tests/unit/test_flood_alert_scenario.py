"""Scenario test — flood alert end-to-end (T062)."""

from unittest.mock import MagicMock, patch

import pytest
from common.handoffs import AgentHandoffEvent
from communication.approval import ApprovalWorkflow
from communication.config import CommunicationConfig
from communication.delivery import MultiChannelDeliveryService
from communication.models import (
    AlertStatus,
    AudienceSegment,
    ChannelType,
    ContentBlock,
    DeliveryStatus,
    PublicAlert,
    SegmentPriority,
    UrgencyLevel,
)
from communication.pipeline import CommunicationProcessingPipeline
from communication.repository import CommunicationAlertRepository
from communication.segmentation import AudienceSegmenter


class TestFloodAlertScenario:
    """Flood simulation through the communication pipeline (T062)."""

    def _build_flood_handoff(self) -> AgentHandoffEvent:
        return AgentHandoffEvent(
            handoff_id="handoff-flood-001",
            incident_id="INC-FLOOD-2025",
            source_agent="risk_assessment",
            target_agent="communication",
            scope_key="INC-FLOOD-2025",
            confidence=0.85,
            payload={
                "recommendationId": "rec-flood",
                "assessmentId": "assess-flood",
                "explanation": "Flood impact requires public warning",
                "hazard_type": "flood",
                "severity": "moderate",
                "urgency": "advisory",
                "location": "Lismore, NSW",
                "alert_type": "evacuation",
                "summary": "Flood waters rising in Lismore area",
                "zones": [
                    {"level": 3, "boundary": {}, "population_estimate": 12000},
                ],
            },
        )

    def _pipeline(self) -> CommunicationProcessingPipeline:
        repository = CommunicationAlertRepository()

        class _Store:
            def __init__(self, record):
                self.record = record

            def read_item(self, item, partition_key):
                return self.record

        class _Publisher:
            async def publish(self, payload):
                return None

        approval = ApprovalWorkflow(service_bus_client=_Publisher(), alert_repository=repository)
        return CommunicationProcessingPipeline(
            incident_store=_Store({"id": "INC-FLOOD-2025", "tenant_id": "live", "commander_chain": ["ic-1"]}),
            recommendation_store=_Store({"id": "rec-flood", "incident_id": "INC-FLOOD-2025", "tenant_id": "live"}),
            assessment_store=_Store(
                {
                    "id": "assess-flood",
                    "incident_id": "INC-FLOOD-2025",
                    "tenant_id": "live",
                    "hazard_type": "flood",
                    "severity": "moderate",
                    "location": "Lismore, NSW",
                    "zones": [{"id": "zone-3", "level": 3, "boundary": {}, "population_estimate": 12000}],
                }
            ),
            alert_repository=repository,
            approval_workflow=approval,
        )

    @patch("communication.translator.MultilingualTranslator._generate_with_fallback")
    @patch("communication.telemetry.pipeline_span")
    @patch("communication.telemetry.CustomEventEmitter")
    @patch("communication.telemetry.metrics")
    def test_flood_pipeline_produces_alert(self, mock_metrics, mock_emitter, mock_span, mock_llm):
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)

        mock_llm.return_value = {
            "text": "Flood Advisory | Rising waters in Lismore. | Avoid flood areas.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        }

        pipeline = self._pipeline()
        alert = pipeline.process_handoff(self._build_flood_handoff())

        assert alert is not None
        assert alert.incident_id == "INC-FLOOD-2025"
        assert alert.status == AlertStatus.pending_review

    def test_flood_zone3_advisory_moderate_segments(self):
        """Zone 3 maps to urgency=advisory, priority=moderate."""
        segmenter = AudienceSegmenter()
        assessment_data = {
            "zones": [{"level": 3, "boundary": {}, "population_estimate": 12000}],
        }
        segments = segmenter.segment_audience(assessment_data)

        zone3_segments = [s for s in segments if s.zone_level == 3]
        assert len(zone3_segments) >= 1
        assert zone3_segments[0].urgency_level == UrgencyLevel.advisory
        assert zone3_segments[0].priority == SegmentPriority.moderate

    @pytest.mark.asyncio
    async def test_flood_multiple_channels_sms_and_push(self):
        """Delivery service creates records for both SMS and push channels."""
        config = CommunicationConfig()
        sms_mock = MagicMock()
        push_mock = MagicMock()

        alert = PublicAlert(
            alert_id="ca-INC-FLOOD-2025-v1",
            incident_id="INC-FLOOD-2025",
            version=1,
            tenant_id="live",
            status=AlertStatus.approved,
            approval_mode="human_approved",
            approved_by_user_id="commander-1",
            approved_by_role="ic",
            approved_at="2026-09-17T00:00:00Z",
            content_blocks={
                "en-AU": ContentBlock(
                    language_code="en-AU",
                    title="Flood Advisory",
                    body="Flood waters rising.",
                    action_items="Monitor conditions.",
                ),
            },
            confidence=0.85,
        )
        service = MultiChannelDeliveryService(
            config=config,
            sms_client=sms_mock,
            push_client=push_mock,
            approval_resolver=lambda _tenant_id, _alert_id, _version: alert,
        )

        segments = [
            AudienceSegment(
                segment_id="seg-flood-z3",
                zone_level=3,
                urgency_level=UrgencyLevel.advisory,
                priority=SegmentPriority.moderate,
                preferred_language="en-AU",
                delivery_channels=[ChannelType.sms, ChannelType.push],
            ),
        ]

        records = await service.deliver_alert(alert, segments)

        channels_used = {r.channel for r in records}
        assert ChannelType.sms in channels_used
        assert ChannelType.push in channels_used

    @pytest.mark.asyncio
    async def test_flood_delivery_records_status(self):
        """Delivery records have a valid delivery status after delivery."""
        config = CommunicationConfig()
        sms_mock = MagicMock()
        push_mock = MagicMock()

        alert = PublicAlert(
            alert_id="ca-INC-FLOOD-2025-v1",
            incident_id="INC-FLOOD-2025",
            version=1,
            tenant_id="live",
            status=AlertStatus.approved,
            approval_mode="human_approved",
            approved_by_user_id="commander-1",
            approved_by_role="ic",
            approved_at="2026-09-17T00:00:00Z",
            content_blocks={
                "en-AU": ContentBlock(
                    language_code="en-AU",
                    title="Flood Advisory",
                    body="Rising waters in Lismore.",
                    action_items="Avoid flood areas.",
                ),
            },
            confidence=0.85,
        )
        service = MultiChannelDeliveryService(
            config=config,
            sms_client=sms_mock,
            push_client=push_mock,
            approval_resolver=lambda _tenant_id, _alert_id, _version: alert,
        )

        segments = [
            AudienceSegment(
                segment_id="seg-flood-check",
                zone_level=3,
                urgency_level=UrgencyLevel.advisory,
                priority=SegmentPriority.moderate,
                preferred_language="en-AU",
                delivery_channels=[ChannelType.sms],
            ),
        ]

        records = await service.deliver_alert(alert, segments)
        assert len(records) >= 1
        assert records[0].delivery_status in (
            DeliveryStatus.delivered,
            DeliveryStatus.accepted,
            DeliveryStatus.failed,
            DeliveryStatus.unconfigured,
            DeliveryStatus.retrying,
        )
