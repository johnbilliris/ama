from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.services import state_store
from app.services.dead_letter_service import DeadLetterService
from app.services.event_bus import EventBus, EventEnvelope
from app.services.operational_store import OperationalStore
from app.services.public_alert_service import stamp_alert_content_version

from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent
from packages.domain.src.domain.models.timeline_event import TimelineEvent
from packages.domain.src.domain.tenant_mode import is_live_tenant

# Ensure apps/agents is importable when API code invokes MAF runtime.
_AGENTS_PATH = Path(__file__).resolve().parents[3] / "agents"
if str(_AGENTS_PATH) not in sys.path:
    sys.path.insert(0, str(_AGENTS_PATH))

_TRUSTED_TIERS: frozenset[str] = frozenset(
    {
        "tier_1_authoritative_government",
        "tier_2_verified_institutional",
        "tier_3_operational_sensor",
    }
)

_RECOMMENDATION_METHODS: frozenset[str] = frozenset({"llm", "template", "template_fallback", "safety_fallback"})
_ALERT_SAFETY_RESULTS: frozenset[str] = frozenset({"passed", "failed_with_fallback", "not_checked"})
_OUTBOX_TERMINAL_STATUSES: frozenset[str] = frozenset(
    {
        "completed",
        "ignored",
        "blocked_by_monitoring_gate",
        "dead_lettered_disabled",
        "dead_lettered_failure",
    }
)


def _is_maf_runtime_enabled() -> bool:
    try:
        from maf_runtime.feature_flags import KNOWN_AGENTS, get_agent_mode

        return any(get_agent_mode(agent) in {"maf", "shadow"} for agent in KNOWN_AGENTS)
    except Exception:
        return False


async def _run_workflow(event: SignalAcceptedEvent) -> dict[str, Any]:
    from maf_runtime.workflow.builder import AmaWorkflow

    workflow = AmaWorkflow()
    return await workflow.run_incident(
        incident={
            "incident_id": event.incident_id,
            "category": "fire" if event.derived_source_kind in {"sensor", "iot"} else "weather",
            "confidenceScore": event.evaluated_confidence_score,
            "source_kind": event.derived_source_kind,
            "payload": {
                "signal_id": event.signal_id,
                "data_source_id": event.data_source_id,
                "correlation_id": event.correlation_id,
            },
        },
        tenant_id=event.tenant_id,
        created_by="signal-accepted-subscriber",
    )


def _should_create_recommendation(event: SignalAcceptedEvent) -> bool:
    return (
        event.incident_id is not None
        and event.derived_trust_tier in _TRUSTED_TIERS
        and event.evaluated_confidence_score >= 0.7
        and event.validation_status in {"validated", "pending", "contradicted"}
    )


def _correlation_suffix(event: SignalAcceptedEvent) -> str:
    seed = f"{event.tenant_id}|{event.correlation_id}|{event.signal_id}"
    return uuid5(NAMESPACE_URL, seed).hex[:12]


def _recommendation_id(event: SignalAcceptedEvent) -> str:
    return f"rec-sa-{_correlation_suffix(event)}"


def _alert_id(event: SignalAcceptedEvent) -> str:
    return f"alert-{_recommendation_id(event)}"


def _outcomes_bucket(event: SignalAcceptedEvent) -> dict[str, dict[str, object]]:
    return state_store.SIGNAL_ACCEPTED_OUTCOMES.bucket_for(event.tenant_id)


def _outbox_bucket(tenant_id: str) -> dict[str, dict[str, object]]:
    return state_store.SIGNAL_ACCEPTED_OUTBOX.bucket_for(tenant_id)


def _record_outcome(event: SignalAcceptedEvent, *, status: str, **extra: object) -> None:
    bucket = _outcomes_bucket(event)
    bucket[event.correlation_id] = {
        "status": status,
        "tenant_id": event.tenant_id,
        "incident_id": event.incident_id,
        "signal_id": event.signal_id,
        "correlation_id": event.correlation_id,
        "updated_at": datetime.now(UTC).isoformat(),
        **extra,
    }


def _record_outbox_result(
    event: SignalAcceptedEvent,
    *,
    attempt_count: int,
    retry_count: int,
) -> dict[str, object]:
    bucket = _outbox_bucket(event.tenant_id)
    now = datetime.now(UTC).isoformat()
    entry = bucket.setdefault(
        event.correlation_id,
        {
            "event_type": "SignalAccepted",
            "tenant_id": event.tenant_id,
            "scope": event.scope,
            "signal_id": event.signal_id,
            "correlation_id": event.correlation_id,
            "event": event.model_dump(mode="json"),
            "created_at": now,
        },
    )
    outcome = _outcomes_bucket(event).get(event.correlation_id, {})
    status = str(outcome.get("status") or "completed")
    entry["status"] = status
    entry["attempt_count"] = attempt_count
    entry["retry_count"] = retry_count
    entry["updated_at"] = now
    entry["last_outcome"] = outcome
    if status in _OUTBOX_TERMINAL_STATUSES:
        entry["completed_at"] = now
    dead_letter_id = outcome.get("dead_letter_entry_id") if isinstance(outcome, dict) else None
    if dead_letter_id:
        entry["dead_letter_entry_id"] = dead_letter_id
    return entry


async def enqueue_signal_accepted(event: SignalAcceptedEvent) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    bucket = _outbox_bucket(event.tenant_id)
    existing = bucket.get(event.correlation_id)
    if existing is None:
        bucket[event.correlation_id] = {
            "event_type": "SignalAccepted",
            "tenant_id": event.tenant_id,
            "scope": event.scope,
            "signal_id": event.signal_id,
            "correlation_id": event.correlation_id,
            "event": event.model_dump(mode="json"),
            "status": "pending",
            "attempt_count": 0,
            "retry_count": 0,
            "created_at": now,
            "updated_at": now,
        }
    await consume_signal_accepted_outbox(event.tenant_id, max_items=1)
    return _outbox_bucket(event.tenant_id)[event.correlation_id]


async def consume_signal_accepted_outbox(tenant_id: str, *, max_items: int = 50) -> int:
    bucket = _outbox_bucket(tenant_id)
    processed = 0
    for correlation_id, entry in list(bucket.items()):
        if processed >= max_items:
            break
        status = str(entry.get("status") or "pending")
        if status not in {"pending", "retrying", "processing"}:
            continue
        payload = entry.get("event") if isinstance(entry.get("event"), dict) else {}
        event = SignalAcceptedEvent.model_validate(payload)
        attempt_count = int(entry.get("attempt_count") or 0) + 1
        entry["status"] = "processing"
        entry["attempt_count"] = attempt_count
        entry["updated_at"] = datetime.now(UTC).isoformat()
        await publish_signal_accepted(event)
        _record_outbox_result(event, attempt_count=attempt_count, retry_count=int(entry.get("retry_count") or 0))
        if not _outcomes_bucket(event).get(correlation_id):
            _record_outcome(event, status="dead_lettered_failure")
            _record_outbox_result(event, attempt_count=attempt_count, retry_count=int(entry.get("retry_count") or 0))
        processed += 1
    return processed


async def _passes_monitoring_gate(event: SignalAcceptedEvent) -> bool:
    if event.validation_status != "escalated":
        return True

    from monitoring.audit import AuditWriter
    from monitoring.config import MonitoringConfig
    from monitoring.pipeline import SignalProcessingPipeline

    category = "fire" if event.derived_source_kind in {"sensor", "iot"} else "weather"
    raw_signal = {
        "source": {
            "dataSourceId": event.data_source_id,
            "name": event.data_source_id,
            "kind": event.derived_source_kind,
        },
        "incidentId": event.incident_id,
        "category": category,
        "occurredAt": datetime.now(UTC).isoformat(),
        "receivedAt": datetime.now(UTC).isoformat(),
        "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 10000},
        "payload": {
            "signal_id": event.signal_id,
            "data_source_id": event.data_source_id,
            "correlation_id": event.correlation_id,
        },
        "confidenceScore": event.evaluated_confidence_score,
        "freshnessScore": 1.0,
        "validationStatus": event.validation_status,
        "provenance": {
            "collectionMethod": "ingestion_event",
            "sourceUri": f"signal://{event.signal_id}",
        },
    }

    delivered: list[object] = []

    async def _deliver(handoff: object) -> None:
        delivered.append(handoff)

    config = MonitoringConfig()
    pipeline = SignalProcessingPipeline(
        config=config,
        audit_writer=AuditWriter(config=config, cosmos_client=None),
        deliver_fn=_deliver,
    )
    await pipeline.process_signal(raw_signal, event.signal_id, tenant_id=event.tenant_id)
    return len(delivered) > 0


def _lookup_existing_recommendation(event: SignalAcceptedEvent) -> Recommendation | None:
    outcome = _outcomes_bucket(event).get(event.correlation_id)
    if outcome is None:
        return None
    recommendation_id = str(outcome.get("recommendation_id") or "")
    if not recommendation_id:
        return None
    return OperationalStore(event.tenant_id).recommendations.get(recommendation_id)


def _extract_signal_ids(event: SignalAcceptedEvent, risk_output: dict[str, Any]) -> list[str]:
    raw_ids = risk_output.get("input_signal_ids") or risk_output.get("inputSignalIds") or []
    signal_ids: list[str] = [str(value) for value in raw_ids if str(value).strip()]
    inputs = risk_output.get("inputs") if isinstance(risk_output.get("inputs"), dict) else {}
    payload = inputs.get("payload") if isinstance(inputs.get("payload"), dict) else {}
    nested_signal_id = payload.get("signal_id") or payload.get("signalId")
    if nested_signal_id:
        signal_ids.append(str(nested_signal_id))
    signal_ids.append(event.signal_id)
    deduped = list(dict.fromkeys(sig for sig in signal_ids if sig))
    return deduped


def _build_recommendation(event: SignalAcceptedEvent, workflow_doc: dict[str, Any]) -> Recommendation:
    outputs = workflow_doc.get("workflow_outputs") if isinstance(workflow_doc.get("workflow_outputs"), dict) else {}
    risk_output = outputs.get("risk_assessment") if isinstance(outputs.get("risk_assessment"), dict) else {}

    signal_ids = _extract_signal_ids(event, risk_output)
    confidence_score = float(risk_output.get("confidence_adjusted") or event.evaluated_confidence_score)
    if confidence_score >= 0.85:
        level = "high"
    elif confidence_score >= 0.65:
        level = "medium"
    else:
        level = "low"

    generation_method = str(risk_output.get("generation_method") or "template")
    if generation_method not in _RECOMMENDATION_METHODS:
        generation_method = "template"

    evidence_payload = {
        "risk_decision_type": risk_output.get("decision_type"),
        "hazard_type": risk_output.get("hazard_type"),
        "severity_level": risk_output.get("severity_level"),
        "source_kind": event.derived_source_kind,
        "data_source_id": event.data_source_id,
        "correlation_id": event.correlation_id,
    }
    evidence_sha = sha256(json.dumps(evidence_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    summary = str(risk_output.get("decision_rationale") or "Risk assessment recommends public communication")
    explanation = (
        "Risk assessment output captured from AmaWorkflow and linked to accepted signal evidence. "
        f"correlation={event.correlation_id}; data_source={event.data_source_id}; "
        f"supporting_signals={','.join(signal_ids)}; evidence_sha={evidence_sha}."
    )

    return Recommendation(
        recommendation_id=_recommendation_id(event),
        incident_id=event.incident_id or "",
        type="public_alert",
        summary=summary,
        explanation=explanation,
        supporting_signal_ids=signal_ids,
        required_approval_level="incident_commander",
        confidence_level=level,
        confidence_score=confidence_score,
        proposed_by_agent="maf_runtime",
        generation_method=generation_method,
        model_deployment_id=(str(risk_output.get("model_id")) if risk_output.get("model_id") else None),
        token_usage=None,
        tenant_id=event.tenant_id,
        incident_scope_key=event.scope,
    )


def _build_draft_alert(
    event: SignalAcceptedEvent, workflow_doc: dict[str, Any], recommendation: Recommendation
) -> PublicAlert:
    outputs = workflow_doc.get("workflow_outputs") if isinstance(workflow_doc.get("workflow_outputs"), dict) else {}
    communication = outputs.get("communication") if isinstance(outputs.get("communication"), dict) else {}

    communication_blocks = (
        communication.get("content_blocks") if isinstance(communication.get("content_blocks"), dict) else {}
    )
    flattened_blocks: dict[str, str] = {}
    for language, block in communication_blocks.items():
        if isinstance(block, dict):
            flattened_blocks[str(language)] = json.dumps(
                {
                    "title": str(block.get("title", "")),
                    "body": str(block.get("body", "")),
                    "action_items": str(block.get("action_items", "")),
                    "generation_method": str(block.get("generation_method", "")),
                    "content_safety_result": str(block.get("content_safety_result", "")),
                },
                ensure_ascii=False,
                sort_keys=True,
            )

    en_au_block = communication_blocks.get("en-AU") if isinstance(communication_blocks.get("en-AU"), dict) else {}
    headline = str(en_au_block.get("title") or recommendation.summary)
    body = str(en_au_block.get("body") or recommendation.explanation)
    flattened_blocks["headline"] = headline
    flattened_blocks["body"] = body

    languages = communication.get("languages") if isinstance(communication.get("languages"), list) else []
    language_list = [str(language) for language in languages if str(language).strip()]
    if not language_list:
        language_list = [str(language) for language in communication_blocks.keys() if str(language).strip()]

    audience = (
        communication.get("audience_segments") if isinstance(communication.get("audience_segments"), list) else []
    )
    audience_segments = [str(segment) for segment in audience if str(segment).strip()]
    channels = communication.get("channel_set") if isinstance(communication.get("channel_set"), list) else []
    channel_set = [str(channel) for channel in channels if str(channel).strip()]

    content_safety_result = str(communication.get("content_safety_result") or "not_checked")
    if content_safety_result not in _ALERT_SAFETY_RESULTS:
        content_safety_result = "not_checked"

    generation_method = str(communication.get("generation_method") or recommendation.generation_method)
    if generation_method not in _RECOMMENDATION_METHODS:
        generation_method = recommendation.generation_method

    mode = "live" if is_live_tenant(event.tenant_id) else "rehearsal"

    flattened_blocks["recommendationId"] = recommendation.recommendation_id
    flattened_blocks["requiredApprovalLevel"] = recommendation.required_approval_level
    flattened_blocks["workflowCorrelationId"] = str(outputs.get("correlation_id") or event.correlation_id)
    flattened_blocks["workflowRunId"] = str(workflow_doc.get("id") or "")
    flattened_blocks["workflowCommunicationAlertId"] = str(communication.get("alert_id") or "")
    flattened_blocks["workflowCommunicationVersion"] = str(communication.get("version") or "")
    flattened_blocks["contentSafetyDetailsJson"] = json.dumps(
        communication.get("content_safety_details")
        if isinstance(communication.get("content_safety_details"), dict)
        else {},
        ensure_ascii=False,
        sort_keys=True,
    )

    alert = PublicAlert(
        alert_id=_alert_id(event),
        incident_id=event.incident_id or "",
        tenant_id=event.tenant_id,
        mode=mode,
        status="draft",
        audience_segments=audience_segments,
        languages=language_list,
        accessibility_attributes=["plain-language"],
        channel_set=channel_set,
        content_blocks=flattened_blocks,
        generation_method=generation_method,
        model_deployment_id=(
            str(communication.get("model_deployment_id")) if communication.get("model_deployment_id") else None
        ),
        content_safety_result=content_safety_result,
    )
    stamp_alert_content_version(alert)
    return alert


def _emit_chain_edges(event: SignalAcceptedEvent, recommendation: Recommendation) -> None:
    bus = EventBus()

    def _noop_handler(_: EventEnvelope) -> None:
        return None

    bus.subscribe("handoff.monitoring.risk", _noop_handler)
    bus.subscribe("handoff.risk.communication", _noop_handler)

    bus.publish(
        EventEnvelope(
            channel="handoff.monitoring.risk",
            scope_key=event.scope,
            payload={
                "handoffId": f"handoff-{event.correlation_id}-mr",
                "incidentId": event.incident_id or event.scope,
                "sourceAgent": "monitoring",
                "targetAgent": "risk_assessment",
                "confidence": event.evaluated_confidence_score,
                "signalIds": recommendation.supporting_signal_ids,
                "correlationId": event.correlation_id,
            },
        )
    )
    bus.publish(
        EventEnvelope(
            channel="handoff.risk.communication",
            scope_key=event.scope,
            payload={
                "handoffId": f"handoff-{event.correlation_id}-rc",
                "incidentId": event.incident_id or event.scope,
                "sourceAgent": "risk_assessment",
                "targetAgent": "communication",
                "confidence": recommendation.confidence_score,
                "recommendationId": recommendation.recommendation_id,
                "correlationId": event.correlation_id,
            },
        )
    )


def _emit_llm_call_timeline_events(
    event: SignalAcceptedEvent,
    recommendation: Recommendation,
    draft_alert: PublicAlert,
) -> None:
    timeline_bucket = state_store.TIMELINE_EVENTS.bucket_for(event.tenant_id)
    incident_key = event.incident_id or event.scope

    if recommendation.generation_method == "llm":
        timeline_bucket.setdefault(incident_key, []).append(
            TimelineEvent(
                event_id=f"evt-{uuid4().hex}",
                incident_id=incident_key,
                event_type="llm_call",
                summary="Risk recommendation generated via llm",
                actor="signal_accepted_workflow",
                tenant_id=event.tenant_id,
                correlation_id=event.correlation_id,
                payload={
                    "source_agent": "risk_assessment",
                    "target_agent": "communication",
                    "model_deployment_id": recommendation.model_deployment_id,
                    "generation_method": recommendation.generation_method,
                },
            )
        )

    if draft_alert.generation_method == "llm":
        timeline_bucket.setdefault(incident_key, []).append(
            TimelineEvent(
                event_id=f"evt-{uuid4().hex}",
                incident_id=incident_key,
                event_type="llm_call",
                summary="Communication draft generated via llm",
                actor="signal_accepted_workflow",
                tenant_id=event.tenant_id,
                correlation_id=event.correlation_id,
                payload={
                    "source_agent": "communication",
                    "target_agent": "public_alert_draft",
                    "model_deployment_id": draft_alert.model_deployment_id,
                    "generation_method": draft_alert.generation_method,
                },
            )
        )


async def publish_signal_accepted(event: SignalAcceptedEvent) -> Recommendation | None:
    existing_recommendation = _lookup_existing_recommendation(event)
    if existing_recommendation is not None:
        return existing_recommendation
    if event.correlation_id in _outcomes_bucket(event):
        return None

    if not _should_create_recommendation(event):
        _record_outcome(event, status="ignored")
        return None

    if not await _passes_monitoring_gate(event):
        _record_outcome(event, status="blocked_by_monitoring_gate")
        return None

    if not _is_maf_runtime_enabled():
        dead_letter = DeadLetterService().create_entry(
            entry_type="event_delivery_failure",
            correlation_id=event.correlation_id,
            original_payload=event.model_dump(mode="json"),
            failure_reason="MAF runtime disabled for signal accepted workflow",
            failure_code="MAF_RUNTIME_DISABLED",
            source_service="signal_accepted_subscriber",
            target_service="maf_runtime",
            tenant_scope_key=event.scope,
            incident_id=event.incident_id,
        )
        _record_outcome(
            event,
            status="dead_lettered_disabled",
            dead_letter_entry_id=dead_letter.entry_id,
        )
        return None

    try:
        workflow_doc = await _run_workflow(event)
        recommendation = _build_recommendation(event, workflow_doc)
        draft_alert = _build_draft_alert(event, workflow_doc, recommendation)

        governor = None
        recommendation_reserved = False
        if event.tenant_id.startswith("sim-"):
            from app.api.dependencies.simulation_composition import get_resource_governor

            governor = get_resource_governor()
            recommendation_reserved = await governor.reserve_write(event.tenant_id, "recommendation")
            if not recommendation_reserved:
                raise RuntimeError("Simulation recommendation budget or throttle limit reached")

        store = OperationalStore(event.tenant_id)
        try:
            store.recommendations.put(recommendation.recommendation_id, recommendation)
            store.alerts.put(draft_alert.alert_id, draft_alert)
        except Exception:
            state_store.RECOMMENDATIONS.bucket_for(event.tenant_id).pop(recommendation.recommendation_id, None)
            if recommendation_reserved and governor is not None:
                await governor.release_write(event.tenant_id, "recommendation")
            raise

        _emit_llm_call_timeline_events(event, recommendation, draft_alert)
        _emit_chain_edges(event, recommendation)
        _record_outcome(
            event,
            status="completed",
            recommendation_id=recommendation.recommendation_id,
            alert_id=draft_alert.alert_id,
        )
        return recommendation
    except Exception as exc:
        dead_letter = DeadLetterService().create_entry(
            entry_type="event_delivery_failure",
            correlation_id=event.correlation_id,
            original_payload=event.model_dump(mode="json"),
            failure_reason=str(exc),
            failure_code="WORKFLOW_EXECUTION_FAILED",
            source_service="signal_accepted_subscriber",
            target_service="maf_runtime",
            tenant_scope_key=event.scope,
            incident_id=event.incident_id,
        )
        _record_outcome(
            event,
            status="dead_lettered_failure",
            dead_letter_entry_id=dead_letter.entry_id,
        )
        return None


def reset_signal_accepted_dedup() -> None:
    state_store.SIGNAL_ACCEPTED_OUTCOMES.clear_all_tenants()
    state_store.SIGNAL_ACCEPTED_OUTBOX.clear_all_tenants()
