"""PPRR lifecycle management service.

Manages PPRR phase transitions for incidents and non-incident contexts
(regions, scenarios). Records phase transitions on the incident timeline.

FRs: FR-031, FR-050, FR-053 | Research: R-001
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.services.state_store import (
    INCIDENTS,
    PPRR_CONTEXTS,
    TIMELINE_EVENTS,
)

from apps.agents.common.pprr_lifecycle import (
    build_phase_transition_payload,
    can_run_concurrently,
    validate_phase_transition,
)
from packages.domain.src.domain.models.pprr_phase_context import PprrPhaseContext
from packages.domain.src.domain.models.timeline_event import TimelineEvent


class PprrService:
    """Manages PPRR phase transitions and non-incident phase contexts."""

    def transition_phase(
        self,
        incident_id: str,
        target_phase: str,
        rationale: str,
        authorising_user: str,
        overlap_active: bool = False,
        overlap_end_expected_at: str | None = None,
    ) -> dict:
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)

        incident = INCIDENTS[incident_id]
        current_phase = incident.pprr_phase or "prevention"

        is_valid, error = validate_phase_transition(current_phase, target_phase)
        if not is_valid:
            raise ValueError(error)

        if overlap_active and not can_run_concurrently(current_phase, target_phase):
            msg = (
                f"Phases '{current_phase}' and '{target_phase}' cannot "
                f"run concurrently"
            )
            raise ValueError(msg)

        previous_phase = current_phase
        incident.pprr_phase = target_phase  # type: ignore[assignment]

        payload = build_phase_transition_payload(
            source_phase=previous_phase,
            target_phase=target_phase,
            transition_rationale=rationale,
            authorising_user=authorising_user,
            overlap_active=overlap_active,
            overlap_end_expected_at=overlap_end_expected_at,
        )
        event = TimelineEvent(
            event_id=str(uuid4()),
            incident_id=incident_id,
            event_type="system",
            summary=f"PPRR phase transitioned from '{previous_phase}' to '{target_phase}'",
            actor=authorising_user,
            payload=payload,
        )
        TIMELINE_EVENTS.setdefault(incident_id, []).append(event)

        return {
            "incident_id": incident_id,
            "previous_phase": previous_phase,
            "current_phase": target_phase,
            "overlap_active": overlap_active,
            "event_id": event.event_id,
        }

    def get_phase_info(self, incident_id: str) -> dict:
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)

        incident = INCIDENTS[incident_id]
        timeline = TIMELINE_EVENTS.get(incident_id, [])
        phase_events = [
            e.model_dump(mode="json")
            for e in timeline
            if e.payload.get("action") == "pprr_phase_transition"
        ]
        return {
            "incident_id": incident_id,
            "current_phase": incident.pprr_phase,
            "phase_history": phase_events,
        }

    def create_context(
        self,
        context_type: str,
        context_reference_id: str,
        pprr_phase: str,
        activated_by: str,
        notes: str = "",
    ) -> PprrPhaseContext:
        context = PprrPhaseContext(
            context_id=str(uuid4()),
            context_type=context_type,  # type: ignore[arg-type]
            context_reference_id=context_reference_id,
            pprr_phase=pprr_phase,  # type: ignore[arg-type]
            activated_by=activated_by,
            notes=notes,
        )
        PPRR_CONTEXTS[context.context_id] = context
        return context

    def list_contexts(self, active_only: bool = True) -> list[PprrPhaseContext]:
        contexts = list(PPRR_CONTEXTS.values())
        if active_only:
            contexts = [c for c in contexts if c.deactivated_at is None]
        return contexts

    def transition_context_to_incident(
        self,
        context_id: str,
        incident_id: str,
    ) -> PprrPhaseContext:
        if context_id not in PPRR_CONTEXTS:
            msg = f"PPRR context '{context_id}' not found"
            raise KeyError(msg)
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)

        context = PPRR_CONTEXTS[context_id]
        if context.deactivated_at is not None:
            msg = f"Context '{context_id}' is already deactivated"
            raise ValueError(msg)

        updated = context.model_copy(
            update={
                "transitioned_to_incident_id": incident_id,
                "deactivated_at": datetime.now(UTC),
            },
        )
        PPRR_CONTEXTS[context_id] = updated
        return updated
