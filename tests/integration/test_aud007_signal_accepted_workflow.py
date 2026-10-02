from __future__ import annotations

import pytest
from app.api.routes import signals as signals_route
from app.main import create_app
from app.services.operational_store import OperationalStore
from app.services.signal_accepted_workflow import publish_signal_accepted, reset_signal_accepted_dedup
from app.services.state_store import DEAD_LETTERS, HANDOFF_EVENTS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    reset_signal_accepted_dedup()
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_MONITORING", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RISK_ASSESSMENT", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_EVACUATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_COMMUNICATION", "maf")


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _event(
    *,
    correlation_id: str,
    trust_tier: str = "tier_1_authoritative_government",
    incident_id: str | None = "incident-007",
    confidence: float = 0.9,
) -> SignalAcceptedEvent:
    return SignalAcceptedEvent(
        tenant_id="live",
        scope="live",
        signal_id="sig-007",
        data_source_id="bom-warnings",
        correlation_id=correlation_id,
        incident_id=incident_id,
        derived_source_kind="authoritative",
        derived_trust_tier=trust_tier,
        validation_status="validated",
        evaluated_confidence_score=confidence,
    )


def _workflow_doc(correlation_id: str) -> dict[str, object]:
    blocks = {
        "en-AU": {
            "title": "Emergency warning",
            "body": "Leave immediately if you are in the affected zone.",
            "action_items": "Move to a safer location now.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        },
        "zh-Hans": {
            "title": "紧急警告",
            "body": "如果您在受影响区域，请立即撤离。",
            "action_items": "立刻前往安全地点。",
            "generation_method": "llm",
            "content_safety_result": "passed",
        },
        "ar": {
            "title": "تحذير طارئ",
            "body": "غادر فورًا إذا كنت داخل المنطقة المتأثرة.",
            "action_items": "انتقل الآن إلى مكان أكثر أمانًا.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        },
        "vi": {
            "title": "Cảnh báo khẩn cấp",
            "body": "Rời đi ngay nếu bạn đang ở khu vực bị ảnh hưởng.",
            "action_items": "Di chuyển đến nơi an toàn ngay bây giờ.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        },
        "el": {
            "title": "Έκτακτη προειδοποίηση",
            "body": "Απομακρυνθείτε άμεσα αν βρίσκεστε στην πληγείσα ζώνη.",
            "action_items": "Μετακινηθείτε τώρα σε ασφαλέστερη τοποθεσία.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        },
        "it": {
            "title": "Allerta di emergenza",
            "body": "Evacuare immediatamente se ti trovi nell'area interessata.",
            "action_items": "Raggiungi subito una posizione più sicura.",
            "generation_method": "llm",
            "content_safety_result": "passed",
        },
    }
    return {
        "id": "run-aud007",
        "workflow_outputs": {
            "correlation_id": correlation_id,
            "risk_assessment": {
                "decision_type": "recommendation_generated",
                "decision_rationale": "Issue public alert for affected communities",
                "hazard_type": "fire",
                "severity_level": "high",
                "confidence_adjusted": 0.91,
                "generation_method": "llm",
                "model_id": "aoai-risk-v1",
                "input_signal_ids": ["sig-007"],
                "inputs": {
                    "payload": {
                        "signal_id": "sig-007",
                        "correlation_id": correlation_id,
                    }
                },
            },
            "communication": {
                "alert_id": "ca-incident-007-v1",
                "version": 1,
                "content_blocks": blocks,
                "audience_segments": ["affected-community"],
                "languages": ["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
                "channel_set": ["sms", "push", "emergency_broadcast"],
                "content_safety_result": "passed",
                "content_safety_details": {language: {"passed": True} for language in blocks},
                "generation_method": "llm",
                "model_deployment_id": "aoai-comm-v1",
            },
        },
    }


@pytest.mark.asyncio
async def test_aud007_signal_post_persists_risk_recommendation_and_draft(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    async def _ok(event: SignalAcceptedEvent) -> dict[str, object]:
        return _workflow_doc(event.correlation_id)

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _ok)

    signals_route._governance_registry.register_source(
        DataSource(
            data_source_id="bom-aud007",
            name="BoM Official Feed",
            kind="authoritative",
            trust_tier="tier_1_authoritative_government",
        ),
        actor_id="test-suite",
    )

    response = client.post(
        "/api/signals",
        json={
            "source": {"dataSourceId": "bom-aud007", "name": "BoM", "kind": "authoritative"},
            "incidentId": "incident-007",
            "category": "weather",
            "occurredAt": "2026-03-09T00:00:00Z",
            "receivedAt": "2026-03-09T00:05:00Z",
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
            "payload": {"warning": "Major fire weather warning"},
            "confidenceScore": 0.95,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
            "provenance": {
                "sourceUri": "https://example.gov.au",
                "collectionMethod": "api",
            },
        },
    )

    assert response.status_code == 202

    store = OperationalStore("live")
    recommendations = store.recommendations.values()
    alerts = store.alerts.values()

    assert len(recommendations) == 1
    assert recommendations[0].summary == "Issue public alert for affected communities"
    assert "sig-007" in recommendations[0].supporting_signal_ids
    assert recommendations[0].supporting_signal_ids
    assert "correlation=" in recommendations[0].explanation

    assert len(alerts) == 1
    assert alerts[0].status == "draft"
    assert set(alerts[0].languages) == {"en-AU", "zh-Hans", "ar", "vi", "el", "it"}
    assert alerts[0].content_safety_result == "passed"
    assert alerts[0].content_blocks["workflowCorrelationId"]
    assert alerts[0].content_blocks["contentVersion"]

    chain = HANDOFF_EVENTS.get("incident-007")
    assert chain is not None
    assert len(chain) == 2
    assert {entry["targetAgent"] for entry in chain} == {"risk_assessment", "communication"}


@pytest.mark.asyncio
async def test_aud007_low_trust_or_no_association_creates_no_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _ok(event: SignalAcceptedEvent) -> dict[str, object]:
        return _workflow_doc(event.correlation_id)

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _ok)

    low_trust = await publish_signal_accepted(
        _event(correlation_id="corr-007-2", trust_tier="tier_6_social_unverified")
    )
    no_association = await publish_signal_accepted(_event(correlation_id="corr-007-3", incident_id=None))

    assert low_trust is None
    assert no_association is None
    assert OperationalStore("live").recommendations.values() == []


@pytest.mark.asyncio
async def test_aud007_duplicate_correlation_id_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    async def _ok(event: SignalAcceptedEvent) -> dict[str, object]:
        calls["count"] += 1
        return _workflow_doc(event.correlation_id)

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _ok)

    first = await publish_signal_accepted(_event(correlation_id="corr-007-4"))
    second = await publish_signal_accepted(_event(correlation_id="corr-007-4"))

    assert first is not None
    assert second is not None
    assert second.recommendation_id == first.recommendation_id
    assert calls["count"] == 1
    store = OperationalStore("live")
    assert len(store.recommendations.values()) == 1
    assert len(store.alerts.values()) == 1


@pytest.mark.asyncio
async def test_aud007_executor_failure_dead_letters_without_partial_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _boom(_event: SignalAcceptedEvent) -> dict[str, object]:
        raise RuntimeError("workflow failed")

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _boom)

    rec = await publish_signal_accepted(_event(correlation_id="corr-007-5"))

    assert rec is None
    assert OperationalStore("live").recommendations.values() == []
    assert OperationalStore("live").alerts.values() == []
    assert any(entry.correlation_id == "corr-007-5" for entry in DEAD_LETTERS.values())


@pytest.mark.asyncio
async def test_aud007_disabled_maf_runtime_dead_letters_with_explicit_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_MONITORING", "legacy")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RISK_ASSESSMENT", "legacy")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_EVACUATION", "legacy")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION", "legacy")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_COMMUNICATION", "legacy")

    rec = await publish_signal_accepted(_event(correlation_id="corr-007-disabled"))

    assert rec is None
    assert any(
        entry.correlation_id == "corr-007-disabled" and entry.failure_code == "MAF_RUNTIME_DISABLED"
        for entry in DEAD_LETTERS.values()
    )
