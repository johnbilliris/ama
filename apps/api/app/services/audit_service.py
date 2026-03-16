from packages.domain.src.domain.models.timeline_event import TimelineEvent


class AuditService:
    def build_event(
        self, *, incident_id: str, event_type: str, summary: str, actor: str
    ) -> TimelineEvent:
        return TimelineEvent(
            event_id=f"evt-{incident_id}-{event_type}",
            incident_id=incident_id,
            event_type=event_type,
            summary=summary,
            actor=actor,
        )
