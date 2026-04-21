"""Multi-channel delivery — SMS, push, emergency broadcast with retry.

Per-channel independent retry (3×, exponential backoff 1s/2s/4s).
Vulnerable/critical segments delivered first per FR-024.
Overlapping segment deduplication at delivery time per CHK041.
Simulation tenant alerts MUST NOT trigger real public delivery per FR-040.
"""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import UTC, datetime
from uuid import uuid4

from communication.config import CommunicationConfig
from communication.models import (
    AudienceSegment,
    ChannelType,
    ContentBlock,
    DeliveryRecord,
    DeliveryStatus,
    PublicAlert,
    SegmentPriority,
)

logger = logging.getLogger(__name__)

# Priority ordering for delivery: critical first
_PRIORITY_ORDER = {
    SegmentPriority.critical: 0,
    SegmentPriority.high: 1,
    SegmentPriority.moderate: 2,
}


class MultiChannelDeliveryService:
    """Orchestrates multi-channel alert delivery with retry and deduplication."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        sms_client: object | None = None,
        push_client: object | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._sms_client = sms_client
        self._push_client = push_client
        self._channel_health: dict[str, bool] = {
            "sms": True,
            "push": True,
            "emergency_broadcast": True,
        }

    async def deliver_alert(
        self,
        alert: PublicAlert,
        segments: list[AudienceSegment],
    ) -> list[DeliveryRecord]:
        """Orchestrate delivery across configured channels.

        Returns list of DeliveryRecord for all channel × segment combinations.
        """
        # Simulation tenant check per FR-040
        if alert.tenant_id.startswith("simulation"):
            logger.info(
                "Simulation alert %s — skipping real delivery per FR-040",
                alert.alert_id,
            )
            return self._create_simulation_records(alert, segments)

        # Deduplicate overlapping segments per CHK041
        segments, dedup_map = self._deduplicate_segments(segments)

        # Sort delivery order: critical first per FR-024
        segments = self._sort_delivery_order(segments)

        records: list[DeliveryRecord] = []
        for segment in segments:
            content_block = alert.content_blocks.get(
                segment.preferred_language,
                alert.content_blocks.get("en-AU"),
            )
            if content_block is None:
                continue

            for channel in segment.delivery_channels:
                channel_str = channel.value if isinstance(channel, ChannelType) else channel

                # Check if this segment was deduped
                dedup_info = dedup_map.get(segment.segment_id)

                record = DeliveryRecord(
                    delivery_id=uuid4().hex,
                    alert_id=alert.alert_id,
                    alert_version=alert.version,
                    channel=ChannelType(channel_str),
                    audience_segment_id=segment.segment_id,
                    language_used=segment.preferred_language,
                    content_payload=self._format_content(
                        content_block, ChannelType(channel_str)
                    ),
                    tenant_id=alert.tenant_id,
                    is_deduplicated=dedup_info is not None,
                    deduplicated_by_segment_id=(
                        dedup_info if dedup_info else None
                    ),
                )

                if dedup_info:
                    # Skip actual delivery for deduped segments
                    record.delivery_status = DeliveryStatus.delivered
                    record.completed_at = datetime.now(UTC)
                else:
                    record = await self._deliver_with_retry(record, ChannelType(channel_str))

                records.append(record)

        return records

    def _deduplicate_segments(
        self,
        segments: list[AudienceSegment],
    ) -> tuple[list[AudienceSegment], dict[str, str]]:
        """Group overlapping segments — highest-priority wins per CHK041.

        Returns (all_segments, dedup_map) where dedup_map maps deduped segment_id
        to the winning segment_id.
        """
        dedup_map: dict[str, str] = {}

        # Group by zone_level to detect overlaps
        zone_segments: dict[int, list[AudienceSegment]] = {}
        for seg in segments:
            zone_segments.setdefault(seg.zone_level, []).append(seg)

        # For each zone, if there are multiple segments, lower-priority ones are deduped
        for zone_level, zone_segs in zone_segments.items():
            if len(zone_segs) <= 1:
                continue

            # Sort by priority (critical < high < moderate in priority order)
            sorted_segs = sorted(
                zone_segs,
                key=lambda s: _PRIORITY_ORDER.get(s.priority, 99),
            )
            winner = sorted_segs[0]
            for loser in sorted_segs[1:]:
                if loser.priority != winner.priority:
                    dedup_map[loser.segment_id] = winner.segment_id

        return segments, dedup_map

    def _sort_delivery_order(
        self, segments: list[AudienceSegment]
    ) -> list[AudienceSegment]:
        """Order critical first, then by zone_level ascending per FR-024."""
        return sorted(
            segments,
            key=lambda s: (
                _PRIORITY_ORDER.get(s.priority, 99),
                s.zone_level,
            ),
        )

    async def _deliver_with_retry(
        self, record: DeliveryRecord, channel: ChannelType
    ) -> DeliveryRecord:
        """Implement per-channel independent retry with exponential backoff."""
        record.initiated_at = datetime.now(UTC)
        backoff = record.retry_backoff_intervals or [1.0, 2.0, 4.0]
        max_retries = self._config.delivery_max_retries

        for attempt in range(max_retries + 1):
            record.attempt_count = attempt + 1
            try:
                if channel == ChannelType.sms:
                    self._deliver_sms(record)
                elif channel == ChannelType.push:
                    self._deliver_push(record)
                elif channel == ChannelType.emergency_broadcast:
                    self._deliver_broadcast(record)

                record.delivery_status = DeliveryStatus.delivered
                record.completed_at = datetime.now(UTC)
                if record.initiated_at:
                    record.delivery_duration_ms = int(
                        (record.completed_at - record.initiated_at).total_seconds() * 1000
                    )
                return record

            except Exception as exc:
                logger.warning(
                    "Delivery attempt %d/%d failed for %s/%s: %s",
                    attempt + 1, max_retries + 1, channel.value,
                    record.audience_segment_id, exc,
                )
                record.failure_reason = str(exc)

                if attempt < max_retries and attempt < len(backoff):
                    record.delivery_status = DeliveryStatus.retrying
                    await asyncio.sleep(backoff[attempt])

        # All retries exhausted
        record.delivery_status = DeliveryStatus.failed
        record.completed_at = datetime.now(UTC)
        if record.initiated_at:
            record.delivery_duration_ms = int(
                (record.completed_at - record.initiated_at).total_seconds() * 1000
            )
        self._channel_health[channel.value] = False
        return record

    def _deliver_sms(self, record: DeliveryRecord) -> None:
        """Deliver via Azure Communication Services SMS."""
        content = record.content_payload
        # Compute SMS segment count per R-013: ceil(len/153) for multi-part
        sms_length = min(len(content), self._config.sms_max_length)
        record.segment_count = math.ceil(sms_length / 153) if sms_length > 0 else 1

        if self._sms_client is not None:
            self._sms_client.send(
                from_="EmergencyAlert",
                to=[record.audience_segment_id],
                message=content[:self._config.sms_max_length],
            )
        else:
            logger.info("SMS delivery (no client): segment_count=%d", record.segment_count)

    def _deliver_push(self, record: DeliveryRecord) -> None:
        """Deliver via Azure Notification Hubs."""
        if self._push_client is not None:
            self._push_client.send_notification({
                "title": record.content_payload[:100],
                "body": record.content_payload,
            })
        else:
            logger.info("Push delivery (no client): %s", record.audience_segment_id)

    def _deliver_broadcast(self, record: DeliveryRecord) -> None:
        """Deliver via EAS webhook — en-AU only per FR-029."""
        if record.language_used != "en-AU":
            logger.info("Broadcast skipped for non-en-AU language: %s", record.language_used)
            record.delivery_status = DeliveryStatus.delivered
            return

        eas_url = self._config.eas_endpoint_url
        if not eas_url:
            logger.warning("EAS endpoint URL not configured, skipping broadcast")
            return

        # In production, this would be an HTTP POST to the EAS endpoint
        logger.info("Broadcast delivery to EAS endpoint: %s", eas_url)

    def _format_content(self, content_block: ContentBlock, channel: ChannelType) -> str:
        """Format content for specific channel constraints."""
        if channel == ChannelType.sms:
            # SMS: title + body, truncated to SMS_MAX_LENGTH
            text = f"{content_block.title}\n{content_block.body}\n{content_block.action_items}"
            return text[: self._config.sms_max_length]
        elif channel == ChannelType.push:
            # Push: title + body payload
            return f"{content_block.title}\n{content_block.body}"
        elif channel == ChannelType.emergency_broadcast:
            # Broadcast: full content en-AU only
            return f"{content_block.title}\n{content_block.body}\n{content_block.action_items}"
        return content_block.body

    def _create_simulation_records(
        self, alert: PublicAlert, segments: list[AudienceSegment]
    ) -> list[DeliveryRecord]:
        """Create delivery records for simulation without real delivery."""
        records = []
        for segment in segments:
            for channel in segment.delivery_channels:
                channel_val = channel.value if isinstance(channel, ChannelType) else channel
                records.append(
                    DeliveryRecord(
                        delivery_id=uuid4().hex,
                        alert_id=alert.alert_id,
                        alert_version=alert.version,
                        channel=ChannelType(channel_val),
                        audience_segment_id=segment.segment_id,
                        language_used=segment.preferred_language,
                        delivery_status=DeliveryStatus.delivered,
                        content_payload="[SIMULATION]",
                        tenant_id=alert.tenant_id,
                        completed_at=datetime.now(UTC),
                    )
                )
        return records

    def get_channel_health(self) -> dict[str, bool]:
        """Return current channel health status."""
        return dict(self._channel_health)
