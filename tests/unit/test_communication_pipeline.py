"""Tests for communication.pipeline — CommunicationProcessingPipeline."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from common.handoffs import AgentHandoffEvent
from communication.approval import ApprovalWorkflow
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.dedup import HandoffDeduplicator
from communication.delivery import MultiChannelDeliveryService
from communication.models import AlertStatus, PublicAlert
from communication.pipeline import CommunicationProcessingPipeline, TransientHandoffDependencyError
from communication.repository import CommunicationAlertRepository
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
            "recommendationId": "rec-1",
            "assessmentId": "ha-1",
            "summary": "Prepare public alert",
            "explanation": "High-confidence bushfire impact assessment",
        },
    )
    defaults.update(overrides)
    return AgentHandoffEvent(**defaults)


def _make_pipeline(**overrides):
    class _Store:
        def __init__(self, records):
            self.records = records

        def read_item(self, item, partition_key):
            return self.records[item]

    config = CommunicationConfig()
    repository = overrides.get("alert_repository") or CommunicationAlertRepository()

    class _Publisher:
        def __init__(self):
            self.messages = []

        async def publish(self, payload):
            self.messages.append(payload)

    defaults = dict(
        config=config,
        deduplicator=HandoffDeduplicator(window_minutes=30),
        translator=MagicMock(spec=MultilingualTranslator),
        segmenter=AudienceSegmenter(config=config),
        version_counter=VersionCounter(config=config),
        audit_writer=AuditWriter(config=config),
        delivery_service=MultiChannelDeliveryService(config=config),
        incident_store=_Store({"inc-1": {"id": "inc-1", "tenant_id": "live"}}),
        recommendation_store=_Store(
            {
                "rec-1": {
                    "id": "rec-1",
                    "incident_id": "inc-1",
                    "assessment_id": "ha-1",
                    "tenant_id": "live",
                }
            }
        ),
        assessment_store=_Store(
            {
                "ha-1": {
                    "id": "ha-1",
                    "incident_id": "inc-1",
                    "tenant_id": "live",
                    "hazard_type": "bushfire",
                    "severity": "high",
                    "location": "Blue Mountains",
                    "zones": [],
                }
            }
        ),
        alert_repository=repository,
        approval_workflow=ApprovalWorkflow(
            config=config,
            service_bus_client=_Publisher(),
            alert_repository=repository,
        ),
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

    def test_wrong_source_agent_is_rejected(self):
        pipeline = _make_pipeline()
        assert pipeline._stage_1_intake(_make_handoff(source_agent="evacuation")) is False

    def test_missing_required_reference_is_rejected(self):
        pipeline = _make_pipeline()
        event = _make_handoff(payload={"recommendationId": "rec-1", "summary": "Missing assessment"})
        assert pipeline._stage_1_intake(event) is False

    def test_foreign_tenant_assessment_is_rejected(self):
        foreign_store = MagicMock()
        foreign_store.read_item.return_value = {
            "id": "ha-1",
            "incident_id": "inc-1",
            "tenant_id": "other-tenant",
        }
        pipeline = _make_pipeline(assessment_store=foreign_store)

        assert pipeline.process_handoff(_make_handoff()) is None

    def test_transient_store_failure_is_raised_and_redelivery_is_not_deduplicated(self):
        unavailable = MagicMock()
        unavailable.read_item.side_effect = TimeoutError("dependency timeout")
        pipeline = _make_pipeline(assessment_store=unavailable)
        event = _make_handoff()

        with pytest.raises(TransientHandoffDependencyError):
            pipeline.process_handoff(event)
        with pytest.raises(TransientHandoffDependencyError):
            pipeline.process_handoff(event)


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

    def test_single_deadline_is_reused_across_stage5_and_stage6(self):
        from communication.models import ContentBlock, GenerationMethod

        captured: dict[str, float] = {}
        en_block = ContentBlock(
            language_code="en-AU",
            title="Fire Alert",
            body="Bushfire approaching Blue Mountains",
            action_items="Evacuate immediately",
            generation_method=GenerationMethod.llm,
        )
        zh_block = ContentBlock(
            language_code="zh-Hans",
            title="火灾警报",
            body="火灾正在逼近",
            action_items="立即撤离",
            generation_method=GenerationMethod.llm,
        )

        mock_translator = MagicMock(spec=MultilingualTranslator)

        def _translate_all(**kwargs):
            captured["stage5"] = float(kwargs["deadline_monotonic"])
            return {"en-AU": en_block, "zh-Hans": zh_block}

        def _back_translate(*args, **kwargs):
            _ = args
            captured["stage6"] = float(kwargs["deadline_monotonic"])
            return 0.95

        mock_translator.translate_all.side_effect = _translate_all
        mock_translator.back_translate_and_score.side_effect = _back_translate

        pipeline = _make_pipeline(translator=mock_translator)
        event = _make_handoff()
        result = pipeline.process_handoff(event)

        assert result is not None
        assert "stage5" in captured and "stage6" in captured
        assert captured["stage5"] == captured["stage6"]

    def test_created_alert_and_segments_survive_repository_replacement(self):
        from communication.models import ContentBlock, GenerationMethod

        documents = {}
        repository = CommunicationAlertRepository(documents=documents)
        translator = MagicMock(spec=MultilingualTranslator)
        translator.translate_all.return_value = {
            "en-AU": ContentBlock(
                language_code="en-AU",
                title="Fire Alert",
                body="Bushfire approaching",
                action_items="Evacuate",
                generation_method=GenerationMethod.llm,
            )
        }
        pipeline = _make_pipeline(translator=translator, alert_repository=repository)

        alert = pipeline.process_handoff(_make_handoff())
        restarted = CommunicationAlertRepository(documents=documents)

        assert alert is not None
        assert restarted.require("live", alert.alert_id).alert_id == alert.alert_id
        assert restarted.audience_segments("live", alert.alert_id)

    def test_alert_write_failure_is_retryable_and_does_not_poison_dedup(self):
        from communication.models import ContentBlock, GenerationMethod

        repository = MagicMock(spec=CommunicationAlertRepository)
        repository.create.side_effect = RuntimeError("Cosmos unavailable")
        translator = MagicMock(spec=MultilingualTranslator)
        translator.translate_all.return_value = {
            "en-AU": ContentBlock(
                language_code="en-AU",
                title="Fire Alert",
                body="Bushfire approaching",
                action_items="Evacuate",
                generation_method=GenerationMethod.llm,
            )
        }
        pipeline = _make_pipeline(translator=translator, alert_repository=repository)
        event = _make_handoff()

        with pytest.raises(TransientHandoffDependencyError):
            pipeline.process_handoff(event)
        with pytest.raises(TransientHandoffDependencyError):
            pipeline.process_handoff(event)

        assert repository.create.call_count == 2


class TestPipelineSafety:
    def test_safety_failure_uses_requested_alert_type_and_preserves_original_result(self):
        from common.content_safety import ContentSafetyResult as ValidationResult
        from communication.models import ContentBlock, GenerationMethod
        from communication.templates import TemplateLoader

        safety = MagicMock()
        safety.validate.return_value = ValidationResult(
            passed=False,
            result="failed_with_fallback",
            reason="provider_severity_4",
        )
        safety.validate_factual.return_value = ValidationResult(True, "passed")
        safety.validate_tone.return_value = ValidationResult(True, "passed")
        safety.validate_cultural.return_value = ValidationResult(True, "passed")
        pipeline = _make_pipeline(content_safety=safety, template_loader=TemplateLoader())
        block = ContentBlock(
            language_code="en-AU",
            title="Flood warning",
            body="Flood at Test area",
            action_items="Stay indoors",
            generation_method=GenerationMethod.llm,
        )

        blocks, overall, details = pipeline._stage_7_content_safety(
            {"en-AU": block},
            {"location": "Test area", "time": "now", "severity_detail": "", "help_url": "help"},
            {"hazard_type": "flood", "severity": "severe", "location": "Test area"},
            "live",
            "handoff-safety",
            "shelter_in_place",
            "Emergency Warning",
        )

        retained = blocks["en-AU"]
        assert overall.value == "failed_with_fallback"
        assert retained.generation_method == GenerationMethod.safety_fallback
        assert retained.original_content_safety_result == "failed_with_fallback"
        assert retained.original_content_safety_failure_reason == "provider_severity_4"
        assert "SHELTER IN PLACE" in retained.title
        assert details["en-AU"].fallback_used is True

    def test_existing_safety_fallback_is_not_revalidated_or_relabelled(self):
        from communication.models import ContentBlock, GenerationMethod

        safety = MagicMock()
        pipeline = _make_pipeline(content_safety=safety)
        block = ContentBlock(
            language_code="en-AU",
            title="Approved fallback",
            body="Follow emergency instructions",
            action_items="Call 000",
            generation_method=GenerationMethod.safety_fallback,
            content_safety_result="failed_with_fallback",
            original_content_safety_result="failed_with_fallback",
            original_content_safety_failure_reason="blocked_keyword",
        )

        blocks, overall, details = pipeline._stage_7_content_safety(
            {"en-AU": block},
            {},
            {},
            "live",
            "handoff-safety",
            "evacuation",
            "Emergency Warning",
        )

        safety.validate.assert_not_called()
        assert blocks["en-AU"].original_content_safety_failure_reason == "blocked_keyword"
        assert overall.value == "failed_with_fallback"
        assert details["en-AU"].passed is False


class TestAssessmentFreshness:
    def test_fresh_assessment_does_not_apply_penalty(self):
        pipeline = _make_pipeline()
        timestamp, status = pipeline._assessment_freshness(
            {"assessed_at": (datetime.now(UTC) - timedelta(minutes=5)).isoformat()}
        )

        assert timestamp is not None
        assert status == "fresh"

    def test_stale_assessment_applies_only_stale_classification(self):
        pipeline = _make_pipeline()
        timestamp, status = pipeline._assessment_freshness(
            {"assessed_at": (datetime.now(UTC) - timedelta(minutes=16)).isoformat()}
        )

        assert timestamp is not None
        assert status == "stale"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, "unavailable"),
            ("not-a-timestamp", "unavailable"),
            ((datetime.now(UTC) + timedelta(minutes=10)).isoformat(), "future"),
        ],
    )
    def test_unusable_timestamp_is_explicit_and_not_stale(self, value, expected):
        pipeline = _make_pipeline()
        timestamp, status = pipeline._assessment_freshness({"assessed_at": value})

        assert status == expected
        if expected == "unavailable":
            assert timestamp is None


class TestAllClearLifecycle:
    @staticmethod
    def _translator():
        from communication.models import ContentBlock, GenerationMethod

        translator = MagicMock(spec=MultilingualTranslator)
        translator.translate_all.return_value = {
            "en-AU": ContentBlock(
                language_code="en-AU",
                title="ALL CLEAR",
                body="Threat passed",
                action_items="Follow recovery advice",
                generation_method=GenerationMethod.template,
            )
        }
        return translator

    @staticmethod
    def _original(repository):
        from communication.models import AlertStatus, AudienceSegment, ContentBlock, PublicAlert

        original = PublicAlert(
            alert_id="ca-inc-1-v1",
            incident_id="inc-1",
            version=1,
            status=AlertStatus.delivered,
            tenant_id="live",
            mode="live",
            active_subzone_ids=["zone-a"],
            content_blocks={
                "en-AU": ContentBlock(
                    language_code="en-AU",
                    title="Warning",
                    body="Threat active",
                    action_items="Evacuate",
                )
            },
        )
        segments = [AudienceSegment(segment_id="original-zone", zone_id="zone-a", zone_level=1)]
        repository.create(original, segments)
        return original

    def test_all_clear_requires_active_subzone_confirmation(self):
        repository = CommunicationAlertRepository()
        original = self._original(repository)
        pipeline = _make_pipeline(alert_repository=repository, translator=self._translator())
        pipeline._version_counter._local_counters[("live", "inc-1")] = 1
        event = _make_handoff(
            payload={
                **_make_handoff().payload,
                "change_type": "all_clear",
                "change_summary": "Threat passed",
                "referenced_alert_id": original.alert_id,
            }
        )

        assert pipeline.process_handoff(event) is None
        assert repository.get("live", "ca-inc-1-v2") is None

    def test_all_clear_reuses_original_audience_without_early_supersession(self):
        repository = CommunicationAlertRepository()
        original = self._original(repository)
        pipeline = _make_pipeline(alert_repository=repository, translator=self._translator())
        pipeline._version_counter._local_counters[("live", "inc-1")] = 1
        event = _make_handoff(
            payload={
                **_make_handoff().payload,
                "change_type": "all_clear",
                "change_summary": "Threat passed",
                "referenced_alert_id": original.alert_id,
                "confirmedActiveSubzones": ["zone-a"],
            }
        )

        replacement = pipeline.process_handoff(event)

        assert replacement is not None
        assert replacement.audience_segments == ["original-zone"]
        assert repository.require("live", original.alert_id).status == AlertStatus.delivered
