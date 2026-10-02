from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.services.dead_letter_service import DeadLetterService
from app.services.state_store import HANDOFF_EVENTS, TIMELINE_EVENTS

from packages.domain.src.domain.models.timeline_event import TimelineEvent

_PAYLOAD_ALLOWLIST: frozenset[str] = frozenset(
    {
        "incidentId",
        "sourceAgent",
        "targetAgent",
        "category",
        "sourceKind",
        "recommendationId",
        "correlationId",
    }
)


def _mask(value: object, max_chars: int = 36) -> str:
    text = str(value)
    if len(text) <= max_chars:
        return text
    return f"{text[:12]}...{text[-8:]}"


def _safe_payload(payload: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key in _PAYLOAD_ALLOWLIST:
        if key in payload:
            safe[key] = _mask(payload[key])
    signal_ids = payload.get("signalIds")
    if isinstance(signal_ids, list):
        safe["signalIdCount"] = len(signal_ids)
    elif payload.get("signal_ids") and isinstance(payload.get("signal_ids"), list):
        safe["signalIdCount"] = len(payload["signal_ids"])
    return safe


def _payload_summary(payload: dict[str, object], max_chars: int = 180) -> str:
    safe = _safe_payload(payload)
    rendered = ";".join(f"{key}={value}" for key, value in sorted(safe.items()))
    unknown_count = max(0, len(payload.keys()) - len(safe.keys()))
    if unknown_count:
        rendered = f"{rendered};redactedFields={unknown_count}" if rendered else f"redactedFields={unknown_count}"
    return rendered[:max_chars]


def _to_float_confidence(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def _to_int(raw: object, default: int) -> int:
    try:
        return int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _resolve_tenant_scope(scope_key: str, payload: dict[str, object]) -> str:
    explicit = str(payload.get("tenantScopeKey") or payload.get("tenantId") or "").strip()
    if explicit:
        return explicit
    if ":" in scope_key:
        return scope_key.split(":", 1)[0] or "live"
    return scope_key or "live"


@dataclass(frozen=True)
class EventEnvelope:
    channel: str
    scope_key: str
    payload: dict[str, object]


@dataclass(frozen=True)
class DeliveryStatus:
    channel: str
    scope_key: str
    subscriber: str
    success: bool
    outcome: str = "delivered"
    error: str | None = None


class EventBus:
    def __init__(self, dead_letter_service: DeadLetterService | None = None) -> None:
        self._subscribers: dict[str, list[Callable[[EventEnvelope], None]]] = {}
        self._dead_letter_service = dead_letter_service or DeadLetterService()

    def subscribe(self, channel: str, handler: Callable[[EventEnvelope], None]) -> None:
        subscribers = self._subscribers.setdefault(channel, [])
        subscribers.append(handler)

    def _record_handoff(
        self,
        *,
        incident_id: str,
        handoff_id: str,
        source_agent: object,
        target_agent: object,
        scope_key: str,
        tenant_scope_key: str,
        correlation_id: str,
        confidence: float,
        payload: dict[str, object],
        status: str,
        attempt_count: int,
        retry_count: int,
        max_attempts: int,
        max_retries: int,
        retry_window_seconds: int,
        timeline_event_id: str,
        dead_letter_entry_id: str | None,
        failure_reason: str | None,
    ) -> None:
        now_iso = datetime.now(UTC).isoformat()
        HANDOFF_EVENTS.bucket_for(tenant_scope_key).setdefault(incident_id, []).append(
            {
                "handoffId": handoff_id,
                "incidentId": incident_id,
                "sourceAgent": source_agent,
                "targetAgent": target_agent,
                "scopeKey": scope_key,
                "tenantScopeKey": tenant_scope_key,
                "correlationId": correlation_id,
                "confidence": confidence,
                "payload": _safe_payload(payload),
                "payloadSummary": _payload_summary(payload),
                "status": status,
                "attemptCount": attempt_count,
                "retryCount": retry_count,
                "maxAttempts": max_attempts,
                "maxRetries": max_retries,
                "retryWindowSeconds": retry_window_seconds,
                "nextRetryAt": None,
                "timelineEventId": timeline_event_id,
                "deadLetterEntryId": dead_letter_entry_id,
                "createdAt": now_iso,
                "deliveredAt": now_iso if status == "delivered" else None,
                "failedAt": now_iso if status in {"failed", "dead_lettered"} else None,
                "failureReason": failure_reason,
            }
        )

    def publish(self, envelope: EventEnvelope) -> list[DeliveryStatus]:
        subscribers = self._subscribers.get(envelope.channel, [])
        tenant_scope_key = _resolve_tenant_scope(envelope.scope_key, envelope.payload)
        incident_id = str(envelope.payload.get("incidentId") or envelope.scope_key)
        handoff_id = str(envelope.payload.get("handoffId") or f"handoff-{uuid4().hex}")
        confidence = _to_float_confidence(envelope.payload.get("confidence"))
        summary = _payload_summary(envelope.payload)
        correlation_id = str(envelope.payload.get("correlationId") or f"event-{uuid4().hex}")
        attempt_count = max(1, min(3, _to_int(envelope.payload.get("attemptCount"), 1)))
        retry_count = max(0, min(2, _to_int(envelope.payload.get("retryCount"), attempt_count - 1)))
        max_attempts = max(1, min(3, _to_int(envelope.payload.get("maxAttempts"), 3)))
        max_retries = max(0, min(2, _to_int(envelope.payload.get("maxRetries"), max_attempts - 1)))
        retry_window_seconds = _to_int(envelope.payload.get("retryWindowSeconds"), 300)

        if not subscribers:
            timeline_event = TimelineEvent(
                event_id=f"evt-{uuid4().hex}",
                incident_id=incident_id,
                event_type="handoff",
                summary=(
                    f"{envelope.payload.get('sourceAgent', 'unknown')}"
                    f" → {envelope.payload.get('targetAgent', 'unknown')}"
                ),
                actor="event_bus",
                tenant_id=tenant_scope_key,
                correlation_id=correlation_id,
                payload={
                    "source_agent": envelope.payload.get("sourceAgent"),
                    "target_agent": envelope.payload.get("targetAgent"),
                    "scope_key": envelope.scope_key,
                    "confidence": confidence,
                    "handoff_status": "failed",
                    "payload_summary": summary,
                },
            )
            self._record_handoff(
                incident_id=incident_id,
                handoff_id=handoff_id,
                source_agent=envelope.payload.get("sourceAgent"),
                target_agent=envelope.payload.get("targetAgent"),
                scope_key=envelope.scope_key,
                tenant_scope_key=tenant_scope_key,
                correlation_id=correlation_id,
                confidence=confidence,
                payload=envelope.payload,
                status="failed",
                attempt_count=attempt_count,
                retry_count=retry_count,
                max_attempts=max_attempts,
                max_retries=max_retries,
                retry_window_seconds=retry_window_seconds,
                timeline_event_id=timeline_event.event_id,
                dead_letter_entry_id=None,
                failure_reason="No subscribers registered for channel",
            )
            TIMELINE_EVENTS.bucket_for(tenant_scope_key).setdefault(incident_id, []).append(timeline_event)
            return [
                DeliveryStatus(
                    channel=envelope.channel,
                    scope_key=envelope.scope_key,
                    subscriber="__none__",
                    success=False,
                    outcome="failed",
                    error="No subscribers registered for channel",
                )
            ]

        statuses: list[DeliveryStatus] = []
        for handler in subscribers:
            handler_name = getattr(handler, "__name__", handler.__class__.__name__)
            try:
                handler(envelope)
                timeline_event = TimelineEvent(
                    event_id=f"evt-{uuid4().hex}",
                    incident_id=incident_id,
                    event_type="handoff",
                    summary=(
                        f"{envelope.payload.get('sourceAgent', 'unknown')}"
                        f" → {envelope.payload.get('targetAgent', 'unknown')}"
                    ),
                    actor="event_bus",
                    tenant_id=tenant_scope_key,
                    correlation_id=correlation_id,
                    payload={
                        "source_agent": envelope.payload.get("sourceAgent"),
                        "target_agent": envelope.payload.get("targetAgent"),
                        "scope_key": envelope.scope_key,
                        "confidence": confidence,
                        "handoff_status": "delivered",
                        "payload_summary": summary,
                    },
                )
                self._record_handoff(
                    incident_id=incident_id,
                    handoff_id=handoff_id,
                    source_agent=envelope.payload.get("sourceAgent"),
                    target_agent=envelope.payload.get("targetAgent"),
                    scope_key=envelope.scope_key,
                    tenant_scope_key=tenant_scope_key,
                    correlation_id=correlation_id,
                    confidence=confidence,
                    payload=envelope.payload,
                    status="delivered",
                    attempt_count=attempt_count,
                    retry_count=retry_count,
                    max_attempts=max_attempts,
                    max_retries=max_retries,
                    retry_window_seconds=retry_window_seconds,
                    timeline_event_id=timeline_event.event_id,
                    dead_letter_entry_id=None,
                    failure_reason=None,
                )
                TIMELINE_EVENTS.bucket_for(tenant_scope_key).setdefault(incident_id, []).append(timeline_event)
                statuses.append(
                    DeliveryStatus(
                        channel=envelope.channel,
                        scope_key=envelope.scope_key,
                        subscriber=handler_name,
                        success=True,
                        outcome="delivered",
                    )
                )
            except Exception as error:
                dead_letter = self._dead_letter_service.create_entry(
                    entry_type="event_delivery_failure",
                    correlation_id=f"event-{envelope.scope_key}",
                    original_payload=envelope.payload,
                    failure_reason=str(error),
                    failure_code="DELIVERY_FAILED",
                    source_service="event_bus",
                    target_service=handler_name,
                    tenant_scope_key=tenant_scope_key,
                    incident_id=incident_id,
                    retry_count=retry_count,
                    attempt_count=attempt_count,
                )
                timeline_event = TimelineEvent(
                    event_id=f"evt-{uuid4().hex}",
                    incident_id=incident_id,
                    event_type="dead_letter",
                    summary="Event delivery failed and was dead-lettered",
                    actor="event_bus",
                    tenant_id=tenant_scope_key,
                    correlation_id=correlation_id,
                    payload={
                        "source_agent": envelope.payload.get("sourceAgent"),
                        "target_agent": envelope.payload.get("targetAgent"),
                        "scope_key": envelope.scope_key,
                        "confidence": confidence,
                        "handoff_status": "failed",
                        "payload_summary": summary,
                    },
                )
                self._record_handoff(
                    incident_id=incident_id,
                    handoff_id=handoff_id,
                    source_agent=envelope.payload.get("sourceAgent"),
                    target_agent=envelope.payload.get("targetAgent"),
                    scope_key=envelope.scope_key,
                    tenant_scope_key=tenant_scope_key,
                    correlation_id=correlation_id,
                    confidence=confidence,
                    payload=envelope.payload,
                    status="failed",
                    attempt_count=attempt_count,
                    retry_count=retry_count,
                    max_attempts=max_attempts,
                    max_retries=max_retries,
                    retry_window_seconds=retry_window_seconds,
                    timeline_event_id=timeline_event.event_id,
                    dead_letter_entry_id=dead_letter.entry_id,
                    failure_reason=str(error),
                )
                TIMELINE_EVENTS.bucket_for(tenant_scope_key).setdefault(incident_id, []).append(timeline_event)
                statuses.append(
                    DeliveryStatus(
                        channel=envelope.channel,
                        scope_key=envelope.scope_key,
                        subscriber=handler_name,
                        success=False,
                        outcome="failed",
                        error=str(error),
                    )
                )

        return statuses
