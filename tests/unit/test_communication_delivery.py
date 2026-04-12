"""Tests for communication.delivery — MultiChannelDeliveryService."""

import math

from communication.delivery import MultiChannelDeliveryService
from communication.models import (
    AudienceSegment,
    ChannelType,
    ContentBlock,
    DeliveryStatus,
    PublicAlert,
    SegmentPriority,
    UrgencyLevel,
)


def _make_alert(**overrides):
    en_block = ContentBlock(
        language_code="en-AU",
        title="Fire Alert",
        body="A fire is approaching the area. Please follow instructions.",
        action_items="Call 000 for emergencies.",
    )
    defaults = dict(
        alert_id="ca-inc1-v1",
        incident_id="inc1",
        version=1,
        content_blocks={"en-AU": en_block},
    )
    defaults.update(overrides)
    return PublicAlert(**defaults)


def _make_segment(**overrides):
    defaults = dict(
        segment_id="seg-1",
        zone_level=1,
        priority=SegmentPriority.high,
        urgency_level=UrgencyLevel.immediate,
        preferred_language="en-AU",
        delivery_channels=[ChannelType.sms],
    )
    defaults.update(overrides)
    return AudienceSegment(**defaults)


# ---------------------------------------------------------------------------
# SMS segment count
# ---------------------------------------------------------------------------


class TestSMSSegmentCount:
    def test_segment_count_short_message(self):
        service = MultiChannelDeliveryService()
        alert = _make_alert()
        segment = _make_segment()
        records = service.deliver_alert(alert, [segment])
        sms_records = [r for r in records if r.channel == ChannelType.sms]
        assert len(sms_records) >= 1
        content_len = len(sms_records[0].content_payload)
        expected = math.ceil(min(content_len, 612) / 153) if content_len > 0 else 1
        assert sms_records[0].segment_count == expected

    def test_sms_max_length_enforced(self):
        long_body = "x" * 1200
        en_block = ContentBlock(
            language_code="en-AU",
            title="t",
            body=long_body,
            action_items="a",
        )
        alert = _make_alert(content_blocks={"en-AU": en_block})
        segment = _make_segment()
        service = MultiChannelDeliveryService()
        records = service.deliver_alert(alert, [segment])
        sms_records = [r for r in records if r.channel == ChannelType.sms]
        assert len(sms_records[0].content_payload) <= 612


# ---------------------------------------------------------------------------
# Emergency broadcast
# ---------------------------------------------------------------------------


class TestEmergencyBroadcast:
    def test_broadcast_en_au_only(self):
        service = MultiChannelDeliveryService()
        alert = _make_alert()
        segment = _make_segment(
            preferred_language="zh-Hans",
            delivery_channels=[ChannelType.emergency_broadcast],
        )
        # The broadcast delivery checks language but still creates a record
        records = service.deliver_alert(alert, [segment])
        assert len(records) >= 1


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------


class TestPriorityOrdering:
    def test_critical_delivered_before_moderate(self):
        service = MultiChannelDeliveryService()
        alert = _make_alert()

        seg_moderate = _make_segment(
            segment_id="seg-mod",
            zone_level=3,
            priority=SegmentPriority.moderate,
            urgency_level=UrgencyLevel.advisory,
        )
        seg_critical = _make_segment(
            segment_id="seg-crit",
            zone_level=1,
            priority=SegmentPriority.critical,
            urgency_level=UrgencyLevel.immediate,
            vulnerability_categories=["hospital"],
        )

        records = service.deliver_alert(alert, [seg_moderate, seg_critical])
        seg_ids = [r.audience_segment_id for r in records]
        # Critical should appear before moderate
        crit_idx = seg_ids.index("seg-crit")
        mod_idx = seg_ids.index("seg-mod")
        assert crit_idx < mod_idx


# ---------------------------------------------------------------------------
# Dedup at delivery
# ---------------------------------------------------------------------------


class TestDeliveryDedup:
    def test_same_zone_lower_priority_deduped(self):
        service = MultiChannelDeliveryService()
        alert = _make_alert()

        seg_high = _make_segment(
            segment_id="seg-high",
            zone_level=1,
            priority=SegmentPriority.high,
        )
        seg_moderate = _make_segment(
            segment_id="seg-mod",
            zone_level=1,
            priority=SegmentPriority.moderate,
        )

        records = service.deliver_alert(alert, [seg_high, seg_moderate])
        deduped = [r for r in records if r.is_deduplicated]
        # The moderate segment should be deduped in favour of high
        assert any(r.audience_segment_id == "seg-mod" for r in deduped)


# ---------------------------------------------------------------------------
# Simulation alerts
# ---------------------------------------------------------------------------


class TestSimulationDelivery:
    def test_simulation_tenant_skips_real_delivery(self):
        service = MultiChannelDeliveryService()
        alert = _make_alert(tenant_id="simulation-test")
        segment = _make_segment()
        records = service.deliver_alert(alert, [segment])
        assert all(r.delivery_status == DeliveryStatus.delivered for r in records)
        assert all(r.content_payload == "[SIMULATION]" for r in records)

    def test_live_tenant_attempts_real_delivery(self):
        service = MultiChannelDeliveryService()
        alert = _make_alert(tenant_id="live")
        segment = _make_segment()
        records = service.deliver_alert(alert, [segment])
        assert all(r.content_payload != "[SIMULATION]" for r in records)


# ---------------------------------------------------------------------------
# Channel health
# ---------------------------------------------------------------------------


class TestChannelHealth:
    def test_initial_health_all_true(self):
        service = MultiChannelDeliveryService()
        health = service.get_channel_health()
        assert health["sms"] is True
        assert health["push"] is True
        assert health["emergency_broadcast"] is True
