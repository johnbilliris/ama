import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.services.event_bus import EventBus, EventEnvelope
from app.services.signal_accepted_workflow import publish_signal_accepted, reset_signal_accepted_dedup
from app.services.state_store import HANDOFF_EVENTS, TIMELINE_EVENTS, reset_state

from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent


def _event(correlation_id: str) -> SignalAcceptedEvent:
    return SignalAcceptedEvent(
        tenant_id="live",
        scope="live",
        signal_id="sig-chain-1",
        data_source_id="bom-warnings",
        correlation_id=correlation_id,
        incident_id="incident-chain-1",
        derived_source_kind="authoritative",
        derived_trust_tier="tier_1_authoritative_government",
        validation_status="validated",
        evaluated_confidence_score=0.92,
    )


@pytest.mark.asyncio
async def test_handoff_chain_records_two_logical_edges_from_signal_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    reset_signal_accepted_dedup()
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_MONITORING", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RISK_ASSESSMENT", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_EVACUATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_COMMUNICATION", "maf")

    async def _workflow(_event: SignalAcceptedEvent) -> dict[str, object]:
        return {
            "id": "run-chain",
            "workflow_outputs": {
                "correlation_id": _event.correlation_id,
                "risk_assessment": {
                    "decision_rationale": "Escalate to public warning",
                    "confidence_adjusted": 0.91,
                    "generation_method": "llm",
                    "input_signal_ids": ["sig-chain-1"],
                },
                "communication": {
                    "content_blocks": {
                        "en-AU": {
                            "title": "Emergency warning",
                            "body": "Leave now.",
                            "action_items": "Move now.",
                            "generation_method": "llm",
                            "content_safety_result": "passed",
                        }
                    },
                    "languages": ["en-AU"],
                    "audience_segments": ["affected-community"],
                    "channel_set": ["sms"],
                    "content_safety_result": "passed",
                    "generation_method": "llm",
                },
            },
        }

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _workflow)
    rec = await publish_signal_accepted(_event("corr-chain-1"))

    assert rec is not None
    records = HANDOFF_EVENTS.get("incident-chain-1")
    assert records is not None
    assert len(records) == 2
    assert {record["sourceAgent"] for record in records} == {"monitoring", "risk_assessment"}
    assert {record["targetAgent"] for record in records} == {"risk_assessment", "communication"}
    timeline = TIMELINE_EVENTS["incident-chain-1"]
    handoff_events = [event for event in timeline if event.event_type == "handoff"]
    llm_events = [event for event in timeline if event.event_type == "llm_call"]
    assert len(handoff_events) == 2
    # A generation label without observed inference evidence must not invent model-call events.
    assert not llm_events
    assert {record["timelineEventId"] for record in records} == {event.event_id for event in handoff_events}


@pytest.mark.asyncio
async def test_handoff_chain_idempotent_for_duplicate_correlation(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    reset_signal_accepted_dedup()
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_MONITORING", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RISK_ASSESSMENT", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_EVACUATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RESOURCE_ALLOCATION", "maf")
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_COMMUNICATION", "maf")

    async def _workflow(_event: SignalAcceptedEvent) -> dict[str, object]:
        return {
            "id": "run-chain",
            "workflow_outputs": {
                "correlation_id": _event.correlation_id,
                "risk_assessment": {
                    "decision_rationale": "Escalate to public warning",
                    "confidence_adjusted": 0.91,
                    "generation_method": "llm",
                    "input_signal_ids": ["sig-chain-1"],
                },
                "communication": {
                    "content_blocks": {
                        "en-AU": {
                            "title": "Emergency warning",
                            "body": "Leave now.",
                            "action_items": "Move now.",
                            "generation_method": "llm",
                            "content_safety_result": "passed",
                        }
                    },
                    "languages": ["en-AU"],
                    "audience_segments": ["affected-community"],
                    "channel_set": ["sms"],
                    "content_safety_result": "passed",
                    "generation_method": "llm",
                },
            },
        }

    monkeypatch.setattr("app.services.signal_accepted_workflow._run_workflow", _workflow)
    first = await publish_signal_accepted(_event("corr-chain-idem"))
    second = await publish_signal_accepted(_event("corr-chain-idem"))

    assert first is not None
    assert second is not None
    assert first.recommendation_id == second.recommendation_id
    records = HANDOFF_EVENTS.get("incident-chain-1")
    assert records is not None
    assert len(records) == 2


def test_handoff_failure_visible_and_payload_redacted() -> None:
    reset_state()
    bus = EventBus()

    def _boom(_: EventEnvelope) -> None:
        raise RuntimeError("subscriber failed")

    bus.subscribe("handoff.monitoring.risk", _boom)
    bus.publish(
        EventEnvelope(
            channel="handoff.monitoring.risk",
            scope_key="live",
            payload={
                "handoffId": "handoff-fail-1",
                "incidentId": "incident-fail-1",
                "sourceAgent": "monitoring",
                "targetAgent": "risk_assessment",
                "confidence": 0.8,
                "correlationId": "corr-secret-1",
                "signalIds": ["sig-1"],
                "apiKey": "SECRET-MUST-NOT-LEAK",
            },
        )
    )

    records = HANDOFF_EVENTS.get("incident-fail-1")
    assert records is not None
    assert len(records) == 1
    record = records[0]
    assert record["status"] == "failed"
    assert record["deadLetterEntryId"]
    assert record["timelineEventId"]
    assert "SECRET-MUST-NOT-LEAK" not in str(record.get("payloadSummary", ""))
    assert "apiKey" not in str(record.get("payload", {}))


def test_handoff_records_tenant_scoped() -> None:
    reset_state()
    bus = EventBus()

    def _ok(_: EventEnvelope) -> None:
        return None

    bus.subscribe("handoff.risk.communication", _ok)

    live_token = set_current_tenant(
        TenantContext(
            agency_id="ses-nsw",
            jurisdiction_ids=("nsw",),
            persona_id="persona-live",
            tenant_id="live",
        )
    )
    try:
        bus.publish(
            EventEnvelope(
                channel="handoff.risk.communication",
                scope_key="live",
                payload={
                    "handoffId": "handoff-live-1",
                    "incidentId": "incident-tenant-1",
                    "sourceAgent": "risk_assessment",
                    "targetAgent": "communication",
                    "confidence": 0.9,
                },
            )
        )
    finally:
        reset_current_tenant(live_token)

    sim_token = set_current_tenant(
        TenantContext(
            agency_id="ses-qld",
            jurisdiction_ids=("qld",),
            persona_id="persona-sim",
            tenant_id="sim-tenant",
        )
    )
    try:
        bus.publish(
            EventEnvelope(
                channel="handoff.risk.communication",
                scope_key="sim-tenant",
                payload={
                    "handoffId": "handoff-sim-1",
                    "incidentId": "incident-tenant-1",
                    "sourceAgent": "risk_assessment",
                    "targetAgent": "communication",
                    "confidence": 0.7,
                },
            )
        )
        records = HANDOFF_EVENTS.get("incident-tenant-1")
        assert records is not None
        assert len(records) == 1
        assert records[0]["handoffId"] == "handoff-sim-1"
    finally:
        reset_current_tenant(sim_token)
