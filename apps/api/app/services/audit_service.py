from typing import Literal
from uuid import uuid4

from app.repositories.audit_repository import AuditRepository
from app.services.state_store import TIMELINE_EVENTS

from packages.domain.src.domain.models.timeline_event import TimelineEvent

TimelineEventType = Literal[
    "signal",
    "recommendation",
    "approval",
    "alert",
    "ingestion",
    "publication",
    "supersession",
    "delivery",
    "task_status",
    "task",
    "system",
    "handoff",
    "dead_letter",
    "llm_call",
]


class AuditService:
    def __init__(self, repository: AuditRepository | None = None) -> None:
        self._repository = repository or AuditRepository()

    def build_event(
        self, *, incident_id: str, event_type: TimelineEventType, summary: str, actor: str
    ) -> TimelineEvent:
        return TimelineEvent(
            event_id=f"evt-{uuid4().hex}",
            incident_id=incident_id,
            event_type=event_type,
            summary=summary,
            actor=actor,
        )

    def record_event(
        self,
        *,
        incident_id: str,
        event_type: TimelineEventType,
        summary: str,
        actor: str,
        tenant_id: str,
        mode: str,
        correlation_id: str,
        outcome: str,
        route: str,
        content_version: str | None = None,
        supporting_signal_ids: list[str] | None = None,
        rationale: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> TimelineEvent:
        event = TimelineEvent(
            event_id=f"evt-{uuid4().hex}",
            incident_id=incident_id,
            event_type=event_type,
            summary=summary,
            actor=actor,
            verified_actor=actor,
            tenant_id=tenant_id,
            mode="live" if mode == "live" else "rehearsal",
            content_version=content_version,
            supporting_signal_ids=list(supporting_signal_ids or []),
            rationale=rationale,
            correlation_id=correlation_id,
            payload=dict(payload or {}),
        )

        row = {
            "eventId": event.event_id,
            "incidentId": incident_id,
            "eventType": event.event_type,
            "summary": summary,
            "actor": actor,
            "verifiedActor": actor,
            "tenantId": tenant_id,
            "mode": event.mode,
            "contentVersion": content_version,
            "supportingSignalIds": list(supporting_signal_ids or []),
            "rationale": rationale,
            "route": route,
            "outcome": outcome,
            "correlationId": correlation_id,
            "payload": dict(payload or {}),
            "environment": tenant_id,
        }
        self._repository.append_sync(row, correlation_id=correlation_id)

        if tenant_id.startswith("sim-"):
            from app.services.simulation_audit_writer import get_simulation_audit_writer

            action = _simulation_audit_action(event_type, outcome)
            get_simulation_audit_writer().write_event_sync(
                tenant_id=tenant_id,
                action=action,
                actor_id=actor,
                resource_id=str(
                    (payload or {}).get("alertId")
                    or (payload or {}).get("recommendationId")
                    or (payload or {}).get("taskId")
                    or incident_id
                ),
                details={
                    "eventType": event_type,
                    "outcome": outcome,
                    "route": route,
                    "rationale": rationale,
                    "payload": dict(payload or {}),
                },
                correlation_id=correlation_id,
                timestamp=event.created_at,
            )

        timeline_for_tenant = TIMELINE_EVENTS.bucket_for(tenant_id)
        timeline_for_tenant.setdefault(incident_id, []).append(event)
        return event


def _simulation_audit_action(event_type: TimelineEventType, outcome: str) -> str:
    if outcome in {"rejected", "rejection"}:
        return "rejection"
    if outcome in {"escalated", "escalation"}:
        return "escalation"
    if event_type == "approval":
        return "approval"
    if event_type in {"publication", "delivery", "supersession", "alert"}:
        return "alert_publish"
    if event_type == "handoff":
        return "agent_handoff"
    if event_type in {"task", "task_status"}:
        return "task_change"
    if event_type == "recommendation":
        return "recommendation"
    return "signal_write"
