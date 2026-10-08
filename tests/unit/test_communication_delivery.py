"""Tests for communication.delivery — MultiChannelDeliveryService."""

import math
from types import SimpleNamespace

import pytest
from communication.config import CommunicationConfig
from communication.delivery import ApprovalRequiredError, MultiChannelDeliveryService
from communication.models import (
    AlertStatus,
    ApprovalMode,
    AudienceSegment,
    ChannelType,
    ContentBlock,
    DeliveryStatus,
    PublicAlert,
    SegmentPriority,
    UrgencyLevel,
)


class _SpyClient:
    def __init__(self, sms_result=None, push_result=None):
        self.calls = 0
        self.sms_result = sms_result or [
            SimpleNamespace(successful=True, message_id="sms-receipt-1", error_message=None)
        ]
        self.push_result = push_result or {"accepted": True, "receipt_id": "push-receipt-1"}
        self.sms_kwargs = None
        self.sms_calls = []
        self.push_payload = None
        self.push_target = None

    def send(self, **kwargs):
        self.calls += 1
        self.sms_kwargs = kwargs
        self.sms_calls.append(kwargs)
        return self.sms_result

    def send_notification(self, payload, *, target):
        self.calls += 1
        self.push_payload = payload
        self.push_target = target
        return self.push_result


class _BroadcastClient:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or {"accepted": True, "receipt_id": "eas-receipt-1"}

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.result


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
        tenant_id="live",
        status=AlertStatus.approved,
        approval_mode=ApprovalMode.human_approved,
        approved_by_user_id="commander-1",
        approved_by_role="ic",
        approved_at="2026-09-17T00:00:00Z",
        content_blocks={"en-AU": en_block},
    )
    defaults.update(overrides)
    return PublicAlert(**defaults)


def _service_for(alert: PublicAlert, **kwargs) -> MultiChannelDeliveryService:
    config = kwargs.pop(
        "config",
        CommunicationConfig(delivery_max_retries=0, sms_sender_identity="+61400000000"),
    )
    return MultiChannelDeliveryService(
        config=config,
        approval_resolver=lambda _tenant_id, _alert_id, _version: alert,
        **kwargs,
    )


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
    @pytest.mark.asyncio
    async def test_segment_count_short_message(self):
        alert = _make_alert()
        service = _service_for(alert)
        segment = _make_segment()
        records = await service.deliver_alert(alert, [segment])
        sms_records = [r for r in records if r.channel == ChannelType.sms]
        assert len(sms_records) >= 1
        content_len = len(sms_records[0].content_payload)
        expected = math.ceil(min(content_len, 612) / 153) if content_len > 0 else 1
        assert sms_records[0].segment_count == expected

    @pytest.mark.asyncio
    async def test_sms_max_length_enforced(self):
        long_body = "x" * 1200
        en_block = ContentBlock(
            language_code="en-AU",
            title="t",
            body=long_body,
            action_items="a",
        )
        alert = _make_alert(content_blocks={"en-AU": en_block})
        segment = _make_segment()
        service = _service_for(alert)
        records = await service.deliver_alert(alert, [segment])
        sms_records = [r for r in records if r.channel == ChannelType.sms]
        assert len(sms_records[0].content_payload) <= 612

    @pytest.mark.asyncio
    async def test_unicode_sms_uses_ucs2_segmentation_and_preserves_action(self):
        block = ContentBlock(
            language_code="zh-Hans",
            title="紧急警报",
            body="洪水正在接近。" * 40,
            action_items="立即撤离。访问 https://alerts.example/a",
        )
        alert = _make_alert(content_blocks={"en-AU": block, "zh-Hans": block})
        sms_spy = _SpyClient()
        service = _service_for(alert, sms_client=sms_spy)
        segment = _make_segment(preferred_language="zh-Hans", recipient_ids=["recipient-a"])

        records = await service.deliver_alert(alert, [segment])

        assert records[0].segment_count == math.ceil(len(records[0].content_payload) / 67)
        assert len(records[0].content_payload) <= 268
        assert "立即撤离" in records[0].content_payload
        assert "https://alerts.example/a" in records[0].content_payload

    @pytest.mark.asyncio
    async def test_push_includes_action_items(self):
        alert = _make_alert()
        push_spy = _SpyClient()
        service = _service_for(alert, push_client=push_spy)

        await service.deliver_alert(
            alert,
            [_make_segment(recipient_ids=["recipient-a"], delivery_channels=[ChannelType.push])],
        )

        assert "Call 000 for emergencies." in push_spy.push_payload["body"]


# ---------------------------------------------------------------------------
# Emergency broadcast
# ---------------------------------------------------------------------------


class TestEmergencyBroadcast:
    @pytest.mark.asyncio
    async def test_non_english_segment_receives_approved_en_au_broadcast(self):
        alert = _make_alert()
        broadcast = _BroadcastClient()
        config = CommunicationConfig(
            delivery_max_retries=0,
            sms_sender_identity="+61400000000",
            eas_endpoint_url="https://eas.example.test/alerts",
            eas_auth_token="test-token",
        )
        service = _service_for(alert, config=config, broadcast_client=broadcast)
        segment = _make_segment(
            preferred_language="zh-Hans",
            delivery_channels=[ChannelType.emergency_broadcast],
        )

        records = await service.deliver_alert(alert, [segment])

        assert records[0].delivery_status == DeliveryStatus.accepted
        assert records[0].language_used == "en-AU"
        assert records[0].provider_receipt_ids == ["eas-receipt-1"]
        url, request = broadcast.calls[0]
        assert url == "https://eas.example.test/alerts"
        assert request["headers"]["Authorization"] == "Bearer test-token"
        assert request["json"]["audience_segment_id"] == "seg-1"
        assert request["json"]["language"] == "en-AU"
        assert "Fire Alert" in request["json"]["message"]

    @pytest.mark.asyncio
    async def test_missing_eas_auth_is_unconfigured_without_client_call(self):
        alert = _make_alert()
        broadcast = _BroadcastClient()
        config = CommunicationConfig(
            delivery_max_retries=0,
            eas_endpoint_url="https://eas.example.test/alerts",
            eas_auth_token="",
        )
        service = _service_for(alert, config=config, broadcast_client=broadcast)

        records = await service.deliver_alert(
            alert,
            [_make_segment(delivery_channels=[ChannelType.emergency_broadcast])],
        )

        assert records[0].delivery_status == DeliveryStatus.unconfigured
        assert broadcast.calls == []


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------


class TestPriorityOrdering:
    @pytest.mark.asyncio
    async def test_critical_delivered_before_moderate(self):
        alert = _make_alert()
        service = _service_for(alert)

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

        records = await service.deliver_alert(alert, [seg_moderate, seg_critical])
        seg_ids = [r.audience_segment_id for r in records]
        # Critical should appear before moderate
        crit_idx = seg_ids.index("seg-crit")
        mod_idx = seg_ids.index("seg-mod")
        assert crit_idx < mod_idx


# ---------------------------------------------------------------------------
# Dedup at delivery
# ---------------------------------------------------------------------------


class TestDeliveryDedup:
    @pytest.mark.asyncio
    async def test_partial_overlap_preserves_nonoverlapping_recipients(self):
        alert = _make_alert()
        sms_spy = _SpyClient()
        service = _service_for(alert, sms_client=sms_spy)
        high = _make_segment(
            segment_id="seg-high",
            priority=SegmentPriority.critical,
            vulnerability_categories=["hospital"],
            recipient_ids=["shared", "hospital-only"],
        )
        general = _make_segment(
            segment_id="seg-general",
            priority=SegmentPriority.high,
            recipient_ids=["shared", "general-only"],
        )

        records = await service.deliver_alert(alert, [general, high])

        assert sms_spy.sms_calls[0]["to"] == ["shared", "hospital-only"]
        assert sms_spy.sms_calls[1]["to"] == ["general-only"]
        general_record = next(record for record in records if record.audience_segment_id == "seg-general")
        assert general_record.delivery_status == DeliveryStatus.accepted
        assert general_record.targeted_recipient_count == 1
        assert general_record.deduplicated_recipient_count == 1
        assert general_record.deduplicated_by_segment_id == "seg-high"

    @pytest.mark.asyncio
    async def test_disjoint_same_level_segments_are_both_delivered(self):
        alert = _make_alert()
        sms_spy = _SpyClient()
        service = _service_for(alert, sms_client=sms_spy)
        first = _make_segment(segment_id="seg-a", zone_boundary={"id": "zone-a"})
        second = _make_segment(segment_id="seg-b", zone_boundary={"id": "zone-b"})

        records = await service.deliver_alert(alert, [first, second])

        assert sms_spy.calls == 2
        assert all(not record.is_deduplicated for record in records)

    @pytest.mark.asyncio
    async def test_exact_geometry_duplicate_is_suppressed_without_membership_data(self):
        alert = _make_alert()
        sms_spy = _SpyClient()
        service = _service_for(alert, sms_client=sms_spy)
        boundary = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 0]]]}
        first = _make_segment(segment_id="seg-a", zone_boundary=boundary)
        duplicate = _make_segment(segment_id="seg-b", zone_boundary=boundary)

        records = await service.deliver_alert(alert, [first, duplicate])

        assert sms_spy.calls == 1
        suppressed = next(record for record in records if record.audience_segment_id == "seg-b")
        assert suppressed.delivery_status == DeliveryStatus.skipped
        assert suppressed.deduplicated_by_segment_id == "seg-a"

    @pytest.mark.asyncio
    async def test_same_recipient_is_independent_between_channels(self):
        alert = _make_alert()
        sms_spy = _SpyClient()
        push_spy = _SpyClient()
        service = _service_for(alert, sms_client=sms_spy, push_client=push_spy)
        segment = _make_segment(
            recipient_ids=["recipient-a"],
            delivery_channels=[ChannelType.sms, ChannelType.push],
        )

        records = await service.deliver_alert(alert, [segment])

        assert sms_spy.calls == 1
        assert push_spy.calls == 1
        assert all(record.targeted_recipient_count == 1 for record in records)


# ---------------------------------------------------------------------------
# Simulation alerts
# ---------------------------------------------------------------------------


class TestSimulationDelivery:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("tenant_id", ["sim-abc123", "simulation-test", "", "unknown-tenant"])
    async def test_non_live_tenants_always_skip_real_delivery(self, tenant_id: str):
        sms_spy = _SpyClient()
        push_spy = _SpyClient()
        broadcast_spy = _BroadcastClient()
        alert = _make_alert(
            tenant_id=tenant_id,
            mode="rehearsal",
            channel_set=[ChannelType.sms, ChannelType.push],
        )
        service = _service_for(
            alert,
            sms_client=sms_spy,
            push_client=push_spy,
            broadcast_client=broadcast_spy,
        )
        segment = _make_segment(delivery_channels=[ChannelType.sms, ChannelType.push, ChannelType.emergency_broadcast])
        records = await service.deliver_alert(alert, [segment])
        assert sms_spy.calls == 0
        assert push_spy.calls == 0
        assert broadcast_spy.calls == []
        assert all(r.delivery_status == DeliveryStatus.skipped for r in records)
        assert all(r.content_payload == "[SIMULATION]" for r in records)

    @pytest.mark.asyncio
    async def test_mode_switching_live_tenant_rehearsal_mode_still_skips_real_delivery(self):
        sms_spy = _SpyClient()
        alert = _make_alert(tenant_id="sim-tenant", mode="rehearsal", channel_set=[ChannelType.sms])
        service = _service_for(alert, sms_client=sms_spy)
        segment = _make_segment()
        records = await service.deliver_alert(alert, [segment])
        assert sms_spy.calls == 0
        assert all(r.delivery_status == DeliveryStatus.skipped for r in records)
        assert all(r.content_payload == "[SIMULATION]" for r in records)

    @pytest.mark.asyncio
    async def test_live_tenant_attempts_real_delivery(self):
        sms_spy = _SpyClient()
        alert = _make_alert(tenant_id="live", mode="live", channel_set=[ChannelType.sms])
        service = _service_for(alert, sms_client=sms_spy)
        segment = _make_segment(delivery_channels=[ChannelType.sms])
        records = await service.deliver_alert(alert, [segment])
        assert sms_spy.calls == 1
        assert all(r.content_payload != "[SIMULATION]" for r in records)


# ---------------------------------------------------------------------------
# Channel health
# ---------------------------------------------------------------------------


class TestChannelHealth:
    def test_initial_health_all_true(self):
        alert = _make_alert()
        service = _service_for(alert)
        health = service.get_channel_health()
        assert health["sms"] is True
        assert health["push"] is True
        assert health["emergency_broadcast"] is True


class TestFailureAndMultilingualBehavior:
    @pytest.mark.asyncio
    async def test_missing_sms_client_results_in_unconfigured_record(self):
        alert = _make_alert(tenant_id="live", mode="live", channel_set=[ChannelType.sms])
        service = _service_for(alert, sms_client=None)
        segment = _make_segment(delivery_channels=[ChannelType.sms])

        records = await service.deliver_alert(alert, [segment])

        assert records[0].delivery_status == DeliveryStatus.unconfigured

    @pytest.mark.asyncio
    async def test_sms_accepted_result_uses_configured_sender_and_preserves_receipt(self):
        alert = _make_alert()
        sms_spy = _SpyClient()
        config = CommunicationConfig(delivery_max_retries=0, sms_sender_identity="+61412345678")
        service = _service_for(alert, config=config, sms_client=sms_spy)

        records = await service.deliver_alert(alert, [_make_segment(segment_id="+61498765432")])

        assert records[0].delivery_status == DeliveryStatus.accepted
        assert records[0].provider_receipt_ids == ["sms-receipt-1"]
        assert sms_spy.sms_kwargs["from_"] == "+61412345678"
        assert sms_spy.sms_kwargs["to"] == ["+61498765432"]
        assert sms_spy.sms_kwargs["enable_delivery_report"] is True

    @pytest.mark.asyncio
    async def test_partial_sms_result_is_failed_and_preserves_receipts(self):
        alert = _make_alert()
        sms_spy = _SpyClient(
            sms_result=[
                SimpleNamespace(successful=True, message_id="accepted-id", error_message=None),
                SimpleNamespace(successful=False, message_id="rejected-id", error_message="invalid recipient"),
            ]
        )
        service = _service_for(alert, sms_client=sms_spy)

        records = await service.deliver_alert(alert, [_make_segment()])

        assert records[0].delivery_status == DeliveryStatus.failed
        assert records[0].provider_status == "partially_accepted"
        assert records[0].provider_receipt_ids == ["accepted-id", "rejected-id"]
        assert "accepted 1/2" in records[0].failure_reason

    @pytest.mark.asyncio
    async def test_missing_sender_identity_is_unconfigured_without_sms_call(self):
        alert = _make_alert()
        sms_spy = _SpyClient()
        config = CommunicationConfig(delivery_max_retries=0, sms_sender_identity="")
        service = _service_for(alert, config=config, sms_client=sms_spy)

        records = await service.deliver_alert(alert, [_make_segment()])

        assert records[0].delivery_status == DeliveryStatus.unconfigured
        assert sms_spy.calls == 0

    @pytest.mark.asyncio
    async def test_missing_push_client_is_unconfigured(self):
        alert = _make_alert()
        service = _service_for(alert, push_client=None)

        records = await service.deliver_alert(
            alert,
            [_make_segment(delivery_channels=[ChannelType.push])],
        )

        assert records[0].delivery_status == DeliveryStatus.unconfigured
        assert records[0].attempt_count == 1

    @pytest.mark.asyncio
    async def test_rejected_push_result_without_exception_is_failed_and_targeted(self):
        alert = _make_alert()
        push_spy = _SpyClient(push_result={"accepted": False, "status": "rejected", "reason": "bad target"})
        service = _service_for(alert, push_client=push_spy)

        records = await service.deliver_alert(
            alert,
            [_make_segment(segment_id="audience-tag-7", delivery_channels=[ChannelType.push])],
        )

        assert records[0].delivery_status == DeliveryStatus.failed
        assert records[0].provider_status == "rejected"
        assert records[0].failure_reason == "bad target"
        assert push_spy.push_target == "audience-tag-7"

    @pytest.mark.asyncio
    async def test_accepted_push_result_targets_audience_segment(self):
        alert = _make_alert()
        push_spy = _SpyClient()
        service = _service_for(alert, push_client=push_spy)

        records = await service.deliver_alert(
            alert,
            [_make_segment(segment_id="audience-tag-8", delivery_channels=[ChannelType.push])],
        )

        assert records[0].delivery_status == DeliveryStatus.accepted
        assert records[0].provider_receipt_ids == ["push-receipt-1"]
        assert push_spy.push_target == "audience-tag-8"

    @pytest.mark.asyncio
    async def test_two_language_groups_are_retained(self):
        sms_spy = _SpyClient()
        alert = _make_alert(tenant_id="live", mode="live", channel_set=[ChannelType.sms])
        service = _service_for(alert, sms_client=sms_spy)
        en = _make_segment(segment_id="recipient-a", preferred_language="en-AU", delivery_channels=[ChannelType.sms])
        zh = _make_segment(segment_id="recipient-a", preferred_language="zh-Hans", delivery_channels=[ChannelType.sms])

        records = await service.deliver_alert(alert, [en, zh])

        assert len(records) == 2
        assert {r.language_used for r in records} == {"en-AU", "zh-Hans"}


class TestPersistedApprovalBoundary:
    @pytest.mark.asyncio
    async def test_missing_approval_store_blocks_provider_call(self):
        sms_spy = _SpyClient()
        alert = _make_alert()
        service = MultiChannelDeliveryService(sms_client=sms_spy)

        with pytest.raises(ApprovalRequiredError, match="not configured"):
            await service.deliver_alert(alert, [_make_segment()])

        assert sms_spy.calls == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "persisted",
        [
            _make_alert(status=AlertStatus.pending_review, approval_mode=None, approved_at=None),
            _make_alert(version=2, alert_id="ca-inc1-v2"),
            _make_alert(approved_by_user_id=None),
        ],
    )
    async def test_invalid_persisted_approval_blocks_provider_call(self, persisted):
        sms_spy = _SpyClient()
        requested = _make_alert()
        service = _service_for(persisted, sms_client=sms_spy)

        with pytest.raises(ApprovalRequiredError, match="this alert version"):
            await service.deliver_alert(requested, [_make_segment()])

        assert sms_spy.calls == 0

    @pytest.mark.asyncio
    async def test_delivery_uses_persisted_approved_content(self):
        class _CapturingSmsClient(_SpyClient):
            def __init__(self):
                super().__init__()
                self.messages = []

            def send(self, **kwargs):
                super().send(**kwargs)
                self.messages.append(kwargs["message"])

        sms_spy = _CapturingSmsClient()
        persisted = _make_alert()
        forged = _make_alert(
            content_blocks={
                "en-AU": ContentBlock(
                    language_code="en-AU",
                    title="FORGED",
                    body="FORGED",
                    action_items="FORGED",
                )
            }
        )
        service = _service_for(persisted, sms_client=sms_spy)

        await service.deliver_alert(forged, [_make_segment()])

        assert sms_spy.calls == 1
        assert all("FORGED" not in message for message in sms_spy.messages)


class TestDeliveryScheduling:
    @pytest.mark.asyncio
    async def test_slow_sms_retry_does_not_block_push(self, monkeypatch):
        push_started = __import__("asyncio").Event()

        class _SlowSms:
            async def send(self, **_kwargs):
                await push_started.wait()
                return [SimpleNamespace(successful=True, message_id="sms-1", error_message=None)]

        class _FastPush:
            async def send_notification(self, _payload, *, target):
                push_started.set()
                return {"accepted": True, "receipt_id": f"push-{target}"}

        alert = _make_alert()
        service = _service_for(alert, sms_client=_SlowSms(), push_client=_FastPush())
        segment = _make_segment(delivery_channels=[ChannelType.sms, ChannelType.push])

        records = await __import__("asyncio").wait_for(service.deliver_alert(alert, [segment]), timeout=1)

        assert {record.delivery_status for record in records} == {DeliveryStatus.accepted}

    @pytest.mark.asyncio
    async def test_delivery_operation_identity_is_stable_across_redelivery(self):
        alert = _make_alert()
        service = _service_for(alert, sms_client=_SpyClient())
        segment = _make_segment(recipient_ids=["recipient-b", "recipient-a"])

        first = await service.deliver_alert(alert, [segment])
        second = await service.deliver_alert(alert, [segment])

        assert first[0].delivery_id == second[0].delivery_id
