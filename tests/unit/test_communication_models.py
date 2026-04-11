"""Tests for communication.models — enums, Pydantic v2 models, and validation rules."""

from datetime import UTC, datetime

import pytest

from communication.models import (
    AlertStatus,
    ApprovalMode,
    AudienceSegment,
    AuditBufferEntry,
    ChangeType,
    ChannelType,
    CommunicationDecisionRecord,
    CommunicationDecisionType,
    ContentBlock,
    ContentSafetyResult,
    DeliveryRecord,
    DeliveryStatus,
    GenerationMethod,
    PublicAlert,
    SegmentPriority,
    UrgencyLevel,
    VALID_STATUS_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# AlertStatus enum
# ---------------------------------------------------------------------------


class TestAlertStatus:
    def test_has_exactly_ten_values(self):
        assert len(AlertStatus) == 10

    def test_all_expected_values_present(self):
        expected = {
            "drafting",
            "pending_review",
            "approved",
            "rejected",
            "delivering",
            "delivered",
            "partially_delivered",
            "superseded",
            "expired",
            "cancelled",
        }
        assert {e.value for e in AlertStatus} == expected


# ---------------------------------------------------------------------------
# ChangeType enum
# ---------------------------------------------------------------------------


class TestChangeType:
    def test_has_exactly_four_values(self):
        assert len(ChangeType) == 4

    def test_all_expected_values_present(self):
        expected = {"initial", "update", "correction", "all_clear"}
        assert {e.value for e in ChangeType} == expected


# ---------------------------------------------------------------------------
# ChannelType enum
# ---------------------------------------------------------------------------


class TestChannelType:
    def test_has_exactly_three_values(self):
        assert len(ChannelType) == 3

    def test_all_expected_values_present(self):
        expected = {"sms", "push", "emergency_broadcast"}
        assert {e.value for e in ChannelType} == expected


# ---------------------------------------------------------------------------
# DeliveryStatus enum
# ---------------------------------------------------------------------------


class TestDeliveryStatus:
    def test_has_exactly_five_values(self):
        assert len(DeliveryStatus) == 5

    def test_all_expected_values_present(self):
        expected = {"pending", "in_progress", "delivered", "failed", "retrying"}
        assert {e.value for e in DeliveryStatus} == expected


# ---------------------------------------------------------------------------
# GenerationMethod enum
# ---------------------------------------------------------------------------


class TestGenerationMethod:
    def test_has_exactly_four_values(self):
        assert len(GenerationMethod) == 4

    def test_all_expected_values_present(self):
        expected = {"llm", "template", "template_fallback", "safety_fallback"}
        assert {e.value for e in GenerationMethod} == expected


# ---------------------------------------------------------------------------
# ContentSafetyResult enum
# ---------------------------------------------------------------------------


class TestContentSafetyResult:
    def test_has_exactly_three_values(self):
        assert len(ContentSafetyResult) == 3

    def test_all_expected_values_present(self):
        expected = {"passed", "failed_with_fallback", "not_checked"}
        assert {e.value for e in ContentSafetyResult} == expected


# ---------------------------------------------------------------------------
# ApprovalMode enum
# ---------------------------------------------------------------------------


class TestApprovalMode:
    def test_has_exactly_two_values(self):
        assert len(ApprovalMode) == 2

    def test_all_expected_values_present(self):
        expected = {"human_approved", "escalated"}
        assert {e.value for e in ApprovalMode} == expected


# ---------------------------------------------------------------------------
# UrgencyLevel enum
# ---------------------------------------------------------------------------


class TestUrgencyLevel:
    def test_has_exactly_three_values(self):
        assert len(UrgencyLevel) == 3

    def test_all_expected_values_present(self):
        expected = {"immediate", "watch", "advisory"}
        assert {e.value for e in UrgencyLevel} == expected


# ---------------------------------------------------------------------------
# SegmentPriority enum
# ---------------------------------------------------------------------------


class TestSegmentPriority:
    def test_has_exactly_three_values(self):
        assert len(SegmentPriority) == 3

    def test_all_expected_values_present(self):
        expected = {"critical", "high", "moderate"}
        assert {e.value for e in SegmentPriority} == expected


# ---------------------------------------------------------------------------
# CommunicationDecisionType enum
# ---------------------------------------------------------------------------


class TestCommunicationDecisionType:
    def test_has_exactly_eighteen_values(self):
        assert len(CommunicationDecisionType) == 18

    def test_all_expected_values_present(self):
        expected = {
            "handoff_received",
            "handoff_rejected",
            "duplicate_discarded",
            "alert_drafted",
            "content_safety_evaluated",
            "back_translation_below_threshold",
            "alert_versioned",
            "approval_requested",
            "approval_action",
            "escalation_triggered",
            "delivery_initiated",
            "delivery_succeeded",
            "delivery_failed",
            "audience_segmented",
            "degradation_detected",
            "content_safety_failure",
            "health_status_changed",
            "template_fallback",
        }
        assert {e.value for e in CommunicationDecisionType} == expected


# ---------------------------------------------------------------------------
# AlertStatus state machine transitions
# ---------------------------------------------------------------------------


class TestAlertStatusTransitions:
    def test_drafting_transitions(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.drafting] == {
            AlertStatus.pending_review,
            AlertStatus.cancelled,
        }

    def test_pending_review_transitions(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.pending_review] == {
            AlertStatus.approved,
            AlertStatus.rejected,
            AlertStatus.cancelled,
        }

    def test_approved_transitions(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.approved] == {
            AlertStatus.delivering,
            AlertStatus.cancelled,
        }

    def test_rejected_is_terminal(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.rejected] == set()

    def test_delivering_transitions(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.delivering] == {
            AlertStatus.delivered,
            AlertStatus.partially_delivered,
        }

    def test_delivered_transitions(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.delivered] == {
            AlertStatus.superseded,
            AlertStatus.expired,
        }

    def test_cancelled_is_terminal(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.cancelled] == set()

    def test_superseded_is_terminal(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.superseded] == set()

    def test_expired_is_terminal(self):
        assert VALID_STATUS_TRANSITIONS[AlertStatus.expired] == set()


# ---------------------------------------------------------------------------
# ContentBlock model
# ---------------------------------------------------------------------------


class TestContentBlock:
    def test_valid_construction(self):
        block = ContentBlock(
            language_code="en-AU",
            title="Test Title",
            body="Test Body",
            action_items="Call 000",
        )
        assert block.language_code == "en-AU"
        assert block.generation_method == GenerationMethod.llm

    def test_title_max_length_200(self):
        with pytest.raises(Exception):
            ContentBlock(
                language_code="en-AU",
                title="x" * 201,
                body="body",
                action_items="items",
            )

    def test_body_max_length_1200(self):
        with pytest.raises(Exception):
            ContentBlock(
                language_code="en-AU",
                title="title",
                body="x" * 1201,
                action_items="items",
            )

    def test_action_items_max_length_500(self):
        with pytest.raises(Exception):
            ContentBlock(
                language_code="en-AU",
                title="title",
                body="body",
                action_items="x" * 501,
            )

    def test_title_at_max_length_ok(self):
        block = ContentBlock(
            language_code="en-AU",
            title="x" * 200,
            body="body",
            action_items="items",
        )
        assert len(block.title) == 200

    def test_default_safety_result_is_passed(self):
        block = ContentBlock(
            language_code="en-AU",
            title="t",
            body="b",
            action_items="a",
        )
        assert block.content_safety_result == "passed"
        assert block.back_translation_score is None
        assert block.back_translation_flagged is False


# ---------------------------------------------------------------------------
# AudienceSegment model
# ---------------------------------------------------------------------------


class TestAudienceSegment:
    def test_valid_construction(self):
        seg = AudienceSegment(zone_level=1)
        assert seg.zone_level == 1
        assert seg.preferred_language == "en-AU"
        assert seg.priority == SegmentPriority.moderate

    def test_zone_level_must_be_1_2_or_3(self):
        with pytest.raises(Exception):
            AudienceSegment(zone_level=0)
        with pytest.raises(Exception):
            AudienceSegment(zone_level=4)

    def test_vulnerability_must_be_critical_priority(self):
        with pytest.raises(Exception):
            AudienceSegment(
                zone_level=1,
                vulnerability_categories=["aged_care"],
                priority=SegmentPriority.high,
            )

    def test_vulnerability_with_critical_priority_ok(self):
        seg = AudienceSegment(
            zone_level=1,
            vulnerability_categories=["hospital"],
            priority=SegmentPriority.critical,
        )
        assert seg.vulnerability_categories == ["hospital"]

    def test_invalid_vulnerability_category_raises(self):
        with pytest.raises(Exception):
            AudienceSegment(
                zone_level=1,
                vulnerability_categories=["invalid_cat"],
                priority=SegmentPriority.critical,
            )

    def test_allowed_vulnerability_categories(self):
        for cat in ("aged_care", "hospital", "school", "disability_services"):
            seg = AudienceSegment(
                zone_level=1,
                vulnerability_categories=[cat],
                priority=SegmentPriority.critical,
            )
            assert seg.vulnerability_categories == [cat]

    def test_empty_vulnerability_no_critical_required(self):
        seg = AudienceSegment(zone_level=2, priority=SegmentPriority.moderate)
        assert seg.vulnerability_categories == []


# ---------------------------------------------------------------------------
# DeliveryRecord model
# ---------------------------------------------------------------------------


class TestDeliveryRecord:
    def test_default_retry_backoff_intervals(self):
        record = DeliveryRecord(
            alert_id="ca-inc1-v1",
            alert_version=1,
            channel=ChannelType.sms,
            audience_segment_id="seg-1",
        )
        assert record.retry_backoff_intervals == [1.0, 2.0, 4.0]

    def test_default_delivery_status_is_pending(self):
        record = DeliveryRecord(
            alert_id="ca-inc1-v1",
            alert_version=1,
            channel=ChannelType.push,
            audience_segment_id="seg-1",
        )
        assert record.delivery_status == DeliveryStatus.pending

    def test_alert_version_must_be_ge_1(self):
        with pytest.raises(Exception):
            DeliveryRecord(
                alert_id="ca-inc1-v1",
                alert_version=0,
                channel=ChannelType.sms,
                audience_segment_id="seg-1",
            )


# ---------------------------------------------------------------------------
# PublicAlert model
# ---------------------------------------------------------------------------


class TestPublicAlert:
    def _minimal(self, **overrides):
        defaults = dict(
            alert_id="ca-inc1-v1",
            incident_id="inc1",
            version=1,
        )
        defaults.update(overrides)
        return PublicAlert(**defaults)

    def test_valid_construction(self):
        alert = self._minimal()
        assert alert.alert_id == "ca-inc1-v1"
        assert alert.status == AlertStatus.drafting

    def test_alert_id_regex_valid_patterns(self):
        for aid in ("ca-inc1-v1", "ca-my_incident-v99", "ca-a-b-c-v2"):
            alert = self._minimal(alert_id=aid)
            assert alert.alert_id == aid

    def test_alert_id_regex_rejects_invalid(self):
        for bad_id in ("inc1-v1", "ca-v1", "ca--v1", "ca-inc1-v", "ca-inc 1-v1"):
            with pytest.raises(Exception):
                self._minimal(alert_id=bad_id)

    def test_version_must_be_ge_1(self):
        with pytest.raises(Exception):
            self._minimal(version=0)

    def test_confidence_in_range(self):
        alert = self._minimal(confidence=0.75)
        assert 0.0 <= alert.confidence <= 1.0

    def test_content_blocks_must_include_en_au(self):
        block = ContentBlock(
            language_code="zh-Hans",
            title="t",
            body="b",
            action_items="a",
        )
        with pytest.raises(Exception):
            self._minimal(content_blocks={"zh-Hans": block})

    def test_content_blocks_with_en_au_ok(self):
        en_block = ContentBlock(
            language_code="en-AU",
            title="t",
            body="b",
            action_items="a",
        )
        alert = self._minimal(content_blocks={"en-AU": en_block})
        assert "en-AU" in alert.content_blocks

    def test_empty_content_blocks_ok(self):
        alert = self._minimal(content_blocks={})
        assert alert.content_blocks == {}

    def test_change_summary_required_for_update(self):
        with pytest.raises(Exception):
            self._minimal(change_type=ChangeType.update, change_summary=None)

    def test_change_summary_required_for_correction(self):
        with pytest.raises(Exception):
            self._minimal(
                change_type=ChangeType.correction,
                change_summary=None,
            )

    def test_change_summary_not_required_for_initial(self):
        alert = self._minimal(change_type=ChangeType.initial)
        assert alert.change_summary is None

    def test_referenced_alert_id_required_for_correction(self):
        with pytest.raises(Exception):
            self._minimal(
                change_type=ChangeType.correction,
                change_summary="Fixing error",
                referenced_alert_id=None,
            )

    def test_referenced_alert_id_required_for_all_clear(self):
        with pytest.raises(Exception):
            self._minimal(
                change_type=ChangeType.all_clear,
                change_summary="All clear now",
                referenced_alert_id=None,
            )

    def test_correction_with_ref_ok(self):
        alert = self._minimal(
            change_type=ChangeType.correction,
            change_summary="Fixed location",
            referenced_alert_id="ca-inc1-v1",
        )
        assert alert.referenced_alert_id == "ca-inc1-v1"

    def test_approval_justification_required_on_reject(self):
        with pytest.raises(Exception):
            self._minimal(
                approval_action="reject",
                approval_justification=None,
            )

    def test_approval_justification_on_reject_ok(self):
        alert = self._minimal(
            approval_action="reject",
            approval_justification="Not accurate",
        )
        assert alert.approval_justification == "Not accurate"

    def test_default_values(self):
        alert = self._minimal()
        assert alert.change_type == ChangeType.initial
        assert alert.generation_method == GenerationMethod.llm
        assert alert.confidence == 1.0
        assert alert.escalation_level == 0
        assert alert.tenant_id == "live"


# ---------------------------------------------------------------------------
# CommunicationDecisionRecord model
# ---------------------------------------------------------------------------


class TestCommunicationDecisionRecord:
    def test_required_fields(self):
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.handoff_received,
        )
        assert record.decision_type == CommunicationDecisionType.handoff_received
        assert record.id is not None

    def test_confidence_clamped_above_one(self):
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.alert_drafted,
            confidence=1.5,
        )
        assert record.confidence == 1.0

    def test_confidence_clamped_below_zero(self):
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.alert_drafted,
            confidence=-0.5,
        )
        assert record.confidence == 0.0

    def test_confidence_none_stays_none(self):
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.handoff_received,
        )
        assert record.confidence is None

    def test_default_values(self):
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.handoff_received,
        )
        assert record.agent_version == "0.1.0"
        assert record.tenant_id == "live"
        assert record.timestamp is not None

    def test_missing_decision_type_raises(self):
        with pytest.raises(Exception):
            CommunicationDecisionRecord()


# ---------------------------------------------------------------------------
# AuditBufferEntry model
# ---------------------------------------------------------------------------


class TestAuditBufferEntry:
    def test_wraps_record(self):
        record = CommunicationDecisionRecord(
            decision_type=CommunicationDecisionType.handoff_received,
        )
        entry = AuditBufferEntry(record=record)
        assert entry.record.decision_type == CommunicationDecisionType.handoff_received
        assert entry.retry_count == 0
        assert entry.last_retry_at is None
        assert entry.buffered_at is not None
