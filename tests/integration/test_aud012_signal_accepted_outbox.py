from __future__ import annotations

import pytest
from app.services import state_store
from app.services.operational_store import OperationalStore
from app.services.signal_accepted_workflow import enqueue_signal_accepted, reset_signal_accepted_dedup
from app.services.state_store import reset_state

from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    reset_signal_accepted_dedup()
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_MONITORING", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RISK_ASSESSMENT", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_EVACUATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_COMMUNICATION", "maf")


def _event(*, correlation_id: str, validation_status: str = "validated") -> SignalAcceptedEvent:
    return SignalAcceptedEvent(
        tenant_id="live",
        scope="live",
        signal_id="sig-aud012-1",
        data_source_id="bom-aud012",
        jurisdiction_id="nsw",
        correlation_id=correlation_id,
        incident_id="incident-aud012",
        derived_source_kind="authoritative",
        derived_trust_tier="tier_1_authoritative_government",
        validation_status=validation_status,
        evaluated_confidence_score=0.93,
    )


def _workflow_doc(correlation_id: str) -> dict[str, object]:
    return {
        "id": "run-aud012",
        "workflow_outputs": {
            "correlation_id": correlation_id,
            "risk_assessment": {
                "decision_type": "recommendation_generated",
                "decision_rationale": "Issue warning",
                "hazard_type": "fire",
                "severity_level": "high",
                "confidence_adjusted": 0.91,
                "generation_method": "llm",
                "model_id": "aoai-risk-v1",
                "input_signal_ids": ["sig-aud012-1"],
                "inputs": {"payload": {"signal_id": "sig-aud012-1", "correlation_id": correlation_id}},
            },
            "communication": {
                "alert_id": "ca-incident-aud012-v1",
                "version": 1,
                "content_blocks": {
                    "en-AU": {
                        "title": "Emergency warning",
                        "body": "Leave immediately",
                        "action_items": "Move to safer location",
                        "generation_method": "llm",
                        "content_safety_result": "passed",
                    }
                },
                "audience_segments": ["affected-community"],
                "languages": ["en-AU"],
                "channel_set": ["sms"],
                "content_safety_result": "passed",
                "content_safety_details": {"en-AU": {"passed": True}},
                "generation_method": "llm",
                "model_deployment_id": "aoai-comm-v1",
            },
        },
    }


@pytest.mark.asyncio
async def test_aud012_enqueue_processes_and_persists_outbox_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _ok(event: SignalAcceptedEvent) -> dict[str, object]:
        return _workflow_doc(event.correlation_id)

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _ok)

    entry = await enqueue_signal_accepted(_event(correlation_id="corr-aud012-1"))

    assert entry["status"] == "completed"
    assert entry["attempt_count"] == 1
    assert entry["retry_count"] == 0
    assert len(OperationalStore("live").recommendations.values()) == 1
    assert len(OperationalStore("live").alerts.values()) == 1


@pytest.mark.asyncio
async def test_aud012_enqueue_is_idempotent_for_same_correlation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    async def _ok(event: SignalAcceptedEvent) -> dict[str, object]:
        calls["count"] += 1
        return _workflow_doc(event.correlation_id)

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _ok)

    first = await enqueue_signal_accepted(_event(correlation_id="corr-aud012-2"))
    second = await enqueue_signal_accepted(_event(correlation_id="corr-aud012-2"))

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert second["attempt_count"] == 1
    assert calls["count"] == 1
    assert len(state_store.SIGNAL_ACCEPTED_OUTBOX.bucket_for("live")) == 1


@pytest.mark.asyncio
async def test_aud012_monitoring_gate_block_persists_terminal_outbox_status(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _blocked(_event: SignalAcceptedEvent) -> bool:
        return False

    async def _ok(event: SignalAcceptedEvent) -> dict[str, object]:
        return _workflow_doc(event.correlation_id)

    monkeypatch.setattr("app.services.signal_accepted_workflow._passes_monitoring_gate", _blocked)
    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _ok)

    entry = await enqueue_signal_accepted(_event(correlation_id="corr-aud012-3", validation_status="validated"))

    assert entry["status"] == "blocked_by_monitoring_gate"
    assert entry["attempt_count"] == 1
    assert len(OperationalStore("live").recommendations.values()) == 0
