"""Plan activation logic — linking emergency plans to incidents during response.

Handles plan activation during incidents and recovery transition with
edge case handling for activation during plan revision.

FRs: FR-007, FR-029 | Research: R-008
"""

from datetime import UTC, datetime


def resolve_activatable_plan(
    plan_doc: dict,
    *,
    fallback_to_last_endorsed: bool = True,
) -> dict | None:
    """Resolve which version of a plan should be activated.

    If the plan is under revision (draft/in_consultation/under_review),
    falls back to the last endorsed version if available.
    Returns None if no activatable version exists.
    """
    activatable_states = {"endorsed"}
    if plan_doc.get("lifecycle_state") in activatable_states:
        return plan_doc
    if fallback_to_last_endorsed and plan_doc.get("_last_endorsed_version"):
        return plan_doc["_last_endorsed_version"]
    return None


def build_activation_record(
    *,
    incident_id: str,
    activated_by: str,
) -> dict:
    """Build a PlanActivationRecord dict for embedding in an EmergencyPlan."""
    return {
        "incident_id": incident_id,
        "activated_at": datetime.now(UTC).isoformat(),
        "activated_by": activated_by,
        "deactivated_at": None,
        "deactivation_reason": None,
    }


def build_deactivation_update(
    activation_record: dict,
    *,
    reason: str,
) -> dict:
    """Add deactivation information to an existing activation record."""
    return {
        **activation_record,
        "deactivated_at": datetime.now(UTC).isoformat(),
        "deactivation_reason": reason,
    }


def should_trigger_me_framework(plan_doc: dict) -> bool:
    """Check if plan activation should trigger M&E framework initialisation.

    Returns True if the plan has recovery_arrangements section with content.
    """
    sections = plan_doc.get("plan_sections", {})
    recovery_section = sections.get("recovery_arrangements")
    if recovery_section and recovery_section.get("content", "").strip():
        return True
    return False
