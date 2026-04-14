"""AIIMS structure management service.

Manages role assignments, incident level changes, and coverage
validation for the Australasian Inter-service Incident Management
System structure within an incident.

FRs: FR-013, FR-014, FR-049 | Research: R-005
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.services.state_store import (
    AIIMS_ASSIGNMENTS,
    INCIDENTS,
    TIMELINE_EVENTS,
)

from apps.agents.common.pprr_lifecycle import build_incident_level_change_payload
from packages.domain.src.domain.models.aiims_role_assignment import (
    ALL_AIIMS_FUNCTIONS,
    AiimsFunction,
    AiimsRoleAssignment,
)
from packages.domain.src.domain.models.timeline_event import TimelineEvent


class AiimsService:
    """Manages AIIMS role assignments and incident structure."""

    def assign_role(
        self,
        incident_id: str,
        agent_identifier: str,
        aiims_function: AiimsFunction,
        assigned_by: str,
    ) -> AiimsRoleAssignment:
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)

        # Enforce one-function-per-agent-per-incident
        for a in AIIMS_ASSIGNMENTS.values():
            if (
                a.incident_id == incident_id
                and a.agent_identifier == agent_identifier
                and a.is_active
            ):
                msg = (
                    f"Agent '{agent_identifier}' already assigned to "
                    f"'{a.aiims_function}' in incident '{incident_id}'"
                )
                raise ValueError(msg)

        assignment = AiimsRoleAssignment(
            assignment_id=str(uuid4()),
            incident_id=incident_id,
            agent_identifier=agent_identifier,
            aiims_function=aiims_function,
            assigned_by=assigned_by,
        )
        AIIMS_ASSIGNMENTS[assignment.assignment_id] = assignment
        return assignment

    def get_structure(self, incident_id: str) -> dict:
        """Return COP display: all active assignments + coverage for an incident."""
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)

        assignments = [
            a for a in AIIMS_ASSIGNMENTS.values()
            if a.incident_id == incident_id and a.is_active
        ]
        coverage_ratio, missing = self.get_coverage(incident_id)
        return {
            "incident_id": incident_id,
            "assignments": [a.model_dump(mode="json") for a in assignments],
            "coverage_ratio": coverage_ratio,
            "missing_functions": missing,
        }

    def update_assignment(
        self,
        assignment_id: str,
        *,
        aiims_function: AiimsFunction | None = None,
        is_active: bool | None = None,
    ) -> AiimsRoleAssignment:
        """Reassign to a different function or deactivate an assignment."""
        if assignment_id not in AIIMS_ASSIGNMENTS:
            msg = f"Assignment '{assignment_id}' not found"
            raise KeyError(msg)

        assignment = AIIMS_ASSIGNMENTS[assignment_id]

        if is_active is False:
            assignment.is_active = False
            assignment.unassigned_at = datetime.now(UTC)
            AIIMS_ASSIGNMENTS[assignment_id] = assignment
            return assignment

        if aiims_function is not None and aiims_function != assignment.aiims_function:
            assignment.aiims_function = aiims_function
            AIIMS_ASSIGNMENTS[assignment_id] = assignment

        return assignment

    def change_incident_level(
        self,
        incident_id: str,
        new_level: int,
        rationale: str,
        authorising_user: str,
    ) -> dict:
        """Change the incident level and record a TimelineEvent."""
        if incident_id not in INCIDENTS:
            msg = f"Incident '{incident_id}' not found"
            raise KeyError(msg)
        if new_level not in (1, 2, 3):
            msg = f"Invalid incident level: {new_level}. Must be 1, 2, or 3."
            raise ValueError(msg)

        incident = INCIDENTS[incident_id]
        previous_level = incident.incident_level

        if previous_level == new_level:
            msg = f"Incident is already at level {new_level}"
            raise ValueError(msg)

        incident.incident_level = new_level  # type: ignore[assignment]

        payload = build_incident_level_change_payload(
            previous_level=previous_level,
            new_level=new_level,
            rationale=rationale,
            authorising_user=authorising_user,
        )
        event = TimelineEvent(
            event_id=str(uuid4()),
            incident_id=incident_id,
            event_type="system",
            summary=f"Incident level changed from {previous_level} to {new_level}",
            actor=authorising_user,
            payload=payload,
        )
        TIMELINE_EVENTS.setdefault(incident_id, []).append(event)

        return {
            "incident_id": incident_id,
            "previous_level": previous_level,
            "new_level": new_level,
            "event_id": event.event_id,
        }

    def get_coverage(self, incident_id: str) -> tuple[float, list[str]]:
        """Return (coverage_ratio, list_of_missing_functions)."""
        active = [
            a for a in AIIMS_ASSIGNMENTS.values()
            if a.incident_id == incident_id and a.is_active
        ]
        covered = {a.aiims_function for a in active}
        missing = [f for f in ALL_AIIMS_FUNCTIONS if f not in covered]
        total = len(ALL_AIIMS_FUNCTIONS)
        ratio = (total - len(missing)) / total if total else 0.0
        return ratio, missing

    def validate_level3_coverage(self, incident_id: str) -> bool:
        """Return True if all 6 AIIMS functions are assigned (Level 3 requirement)."""
        _, missing = self.get_coverage(incident_id)
        return len(missing) == 0
