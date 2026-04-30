from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.services.dead_letter_service import DeadLetterService
from app.services.state_store import HANDOFF_EVENTS, TIMELINE_EVENTS

from packages.domain.src.domain.models.timeline_event import TimelineEvent


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
    error: str | None = None


class EventBus:
    def __init__(self, dead_letter_service: DeadLetterService | None = None) -> None:
        self._subscribers: dict[str, list[Callable[[EventEnvelope], None]]] = {}
        self._dead_letter_service = dead_letter_service or DeadLetterService()

    def subscribe(self, channel: str, handler: Callable[[EventEnvelope], None]) -> None:
        subscribers = self._subscribers.setdefault(channel, [])
        subscribers.append(handler)

    def publish(self, envelope: EventEnvelope) -> list[DeliveryStatus]:
        subscribers = self._subscribers.get(envelope.channel, [])
        if not subscribers:
            return []

        statuses: list[DeliveryStatus] = []
        for handler in subscribers:
            handler_name = getattr(handler, "__name__", handler.__class__.__name__)
            try:
                handler(envelope)
                incident_id = str(envelope.payload.get("incidentId") or envelope.scope_key)
                HANDOFF_EVENTS.setdefault(incident_id, []).append(
                    {
                        "handoffId": str(envelope.payload.get("handoffId") or f"handoff-{uuid4().hex}"),
                        "incidentId": incident_id,
                        "sourceAgent": envelope.payload.get("sourceAgent"),
                        "targetAgent": envelope.payload.get("targetAgent"),
                        "scopeKey": envelope.scope_key,
                        "status": "delivered",
                        "retryCount": int(envelope.payload.get("retryCount", 0) or 0),
                        "createdAt": datetime.now(UTC).isoformat(),
                    }
                )
                TIMELINE_EVENTS.setdefault(incident_id, []).append(
                    TimelineEvent(
                        event_id=f"evt-{uuid4().hex}",
                        incident_id=incident_id,
                        event_type="handoff",
                        summary=(
                            f"{envelope.payload.get('sourceAgent', 'unknown')}"
                            f" → {envelope.payload.get('targetAgent', 'unknown')}"
                        ),
                        actor="event_bus",
                        payload={
                            "source_agent": envelope.payload.get("sourceAgent"),
                            "target_agent": envelope.payload.get("targetAgent"),
                            "scope_key": envelope.scope_key,
                            "confidence": envelope.payload.get("confidence"),
                            "handoff_status": "delivered",
                            "payload_summary": str(envelope.payload)[:180],
                        },
                    )
                )
                statuses.append(
                    DeliveryStatus(
                        channel=envelope.channel,
                        scope_key=envelope.scope_key,
                        subscriber=handler_name,
                        success=True,
                    )
                )
            except Exception as error:
                statuses.append(
                    DeliveryStatus(
                        channel=envelope.channel,
                        scope_key=envelope.scope_key,
                        subscriber=handler_name,
                        success=False,
                        error=str(error),
                    )
                )
                self._dead_letter_service.create_entry(
                    entry_type="event_delivery_failure",
                    correlation_id=f"event-{envelope.scope_key}",
                    original_payload=envelope.payload,
                    failure_reason=str(error),
                    failure_code="DELIVERY_FAILED",
                    source_service="event_bus",
                    target_service=handler_name,
                    tenant_scope_key=envelope.scope_key,
                )
                incident_id = str(envelope.payload.get("incidentId") or envelope.scope_key)
                TIMELINE_EVENTS.setdefault(incident_id, []).append(
                    TimelineEvent(
                        event_id=f"evt-{uuid4().hex}",
                        incident_id=incident_id,
                        event_type="dead_letter",
                        summary="Event delivery failed and was dead-lettered",
                        actor="event_bus",
                        payload={
                            "source_agent": envelope.payload.get("sourceAgent"),
                            "target_agent": envelope.payload.get("targetAgent"),
                            "scope_key": envelope.scope_key,
                            "confidence": envelope.payload.get("confidence"),
                            "handoff_status": "dead_lettered",
                            "payload_summary": str(envelope.payload)[:180],
                        },
                    )
                )

        return statuses
