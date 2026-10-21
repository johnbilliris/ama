from unittest.mock import MagicMock

from common.handoffs import AgentHandoffEvent
from communication.approval import ApprovalWorkflow
from communication.models import ContentBlock, GenerationMethod
from communication.pipeline import CommunicationProcessingPipeline
from communication.repository import CommunicationAlertRepository
from communication.translator import MultilingualTranslator


def _make_handoff() -> AgentHandoffEvent:
    return AgentHandoffEvent(
        handoff_id="handoff-comm-001",
        incident_id="incident-comm-1",
        source_agent="risk_assessment",
        target_agent="communication",
        scope_key="incident-comm-1",
        confidence=0.9,
        payload={
            "assessmentId": "ha-comm-1",
            "recommendationId": "rec-comm-1",
            "summary": "Prepare public alert",
            "explanation": "Fire impact requires public warning",
        },
    )


def _pipeline(translator: MultilingualTranslator) -> CommunicationProcessingPipeline:
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
        translator=translator,
        incident_store=_Store({"id": "incident-comm-1", "tenant_id": "live", "commander_chain": ["ic-1"]}),
        recommendation_store=_Store({"id": "rec-comm-1", "incident_id": "incident-comm-1", "tenant_id": "live"}),
        assessment_store=_Store(
            {
                "id": "ha-comm-1",
                "incident_id": "incident-comm-1",
                "tenant_id": "live",
                "hazard_type": "bushfire",
                "severity": "high",
                "location": "Blue Mountains",
                "zones": [],
            }
        ),
        alert_repository=repository,
        approval_workflow=approval,
    )


def test_communication_pipeline_generates_all_supported_languages() -> None:
    translator = MagicMock(spec=MultilingualTranslator)
    translator.translate_all.return_value = {
        "en-AU": ContentBlock(
            language_code="en-AU",
            title="Emergency warning",
            body="Leave now.",
            action_items="Call 000.",
            generation_method=GenerationMethod.llm,
        ),
        "zh-Hans": ContentBlock(
            language_code="zh-Hans",
            title="紧急警告",
            body="立即撤离。",
            action_items="拨打000。",
            generation_method=GenerationMethod.llm,
        ),
        "ar": ContentBlock(
            language_code="ar",
            title="تحذير طارئ",
            body="غادر الآن.",
            action_items="اتصل على 000.",
            generation_method=GenerationMethod.llm,
        ),
        "vi": ContentBlock(
            language_code="vi",
            title="Cảnh báo khẩn cấp",
            body="Rời đi ngay.",
            action_items="Gọi 000.",
            generation_method=GenerationMethod.llm,
        ),
        "el": ContentBlock(
            language_code="el",
            title="Έκτακτη προειδοποίηση",
            body="Απομακρυνθείτε τώρα.",
            action_items="Καλέστε 000.",
            generation_method=GenerationMethod.llm,
        ),
        "it": ContentBlock(
            language_code="it",
            title="Allerta di emergenza",
            body="Evacuare subito.",
            action_items="Chiama 000.",
            generation_method=GenerationMethod.llm,
        ),
    }
    translator.back_translate_and_score.return_value = 0.95

    pipeline = _pipeline(translator)
    alert = pipeline.process_handoff(_make_handoff())

    assert alert is not None
    expected_languages = {"en-AU", "zh-Hans", "ar", "vi", "el", "it"}
    assert set(alert.languages) == expected_languages
    assert expected_languages.issubset(set(alert.content_blocks.keys()))
    assert alert.generation_method in {
        GenerationMethod.llm,
        GenerationMethod.template_fallback,
        GenerationMethod.safety_fallback,
    }


def test_stage7_preserves_safety_fallback_label() -> None:
    translator = MagicMock(spec=MultilingualTranslator)
    translator.translate_all.return_value = {
        "en-AU": ContentBlock(
            language_code="en-AU",
            title="Emergency warning",
            body="Leave now.",
            action_items="Call 000.",
            generation_method=GenerationMethod.llm,
        ),
        "zh-Hans": ContentBlock(
            language_code="zh-Hans",
            title="紧急警告",
            body="立即撤离。",
            action_items="拨打000。",
            generation_method=GenerationMethod.llm,
        ),
        "ar": ContentBlock(
            language_code="ar",
            title="تحذير",
            body="Emergency warning fallback text",
            action_items="اتصل على 000.",
            generation_method=GenerationMethod.safety_fallback,
            content_safety_result="failed_with_fallback",
        ),
        "vi": ContentBlock(
            language_code="vi",
            title="Cảnh báo",
            body="Rời đi ngay.",
            action_items="Gọi 000.",
            generation_method=GenerationMethod.llm,
        ),
        "el": ContentBlock(
            language_code="el",
            title="Προειδοποίηση",
            body="Απομακρυνθείτε τώρα.",
            action_items="Καλέστε 000.",
            generation_method=GenerationMethod.llm,
        ),
        "it": ContentBlock(
            language_code="it",
            title="Allerta",
            body="Evacuazione subito.",
            action_items="Chiama 000.",
            generation_method=GenerationMethod.llm,
        ),
    }
    translator.back_translate_and_score.return_value = 0.95

    pipeline = _pipeline(translator)
    alert = pipeline.process_handoff(_make_handoff())

    assert alert is not None
    assert alert.content_blocks["ar"].generation_method == GenerationMethod.safety_fallback
    assert alert.content_blocks["ar"].content_safety_result == "failed_with_fallback"
