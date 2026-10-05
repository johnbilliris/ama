"""Plan activation logic — linking emergency plans to incidents during response.

Handles plan activation during incidents and recovery transition with
edge case handling for activation during plan revision.

FRs: FR-007, FR-029 | Research: R-008
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TypedDict


class RecoverySection(TypedDict, total=False):
    content: str


class EmergencyPlanDocument(TypedDict, total=False):
    lifecycle_state: str
    _last_endorsed_version: EmergencyPlanDocument
    plan_sections: dict[str, RecoverySection]


class PlanActivationRecord(TypedDict):
    incident_id: str
    activated_at: str
    activated_by: str
    deactivated_at: str | None
    deactivation_reason: str | None


class StakeholderEngagementLink(TypedDict):
    planning_stakeholders: int
    recovery_community: str
    continuity_status: str


def resolve_activatable_plan(
    plan_doc: EmergencyPlanDocument,
    *,
    fallback_to_last_endorsed: bool = True,
) -> EmergencyPlanDocument | None:
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
) -> PlanActivationRecord:
    """Build a PlanActivationRecord dict for embedding in an EmergencyPlan."""
    return {
        "incident_id": incident_id,
        "activated_at": datetime.now(UTC).isoformat(),
        "activated_by": activated_by,
        "deactivated_at": None,
        "deactivation_reason": None,
    }


def build_deactivation_update(
    activation_record: PlanActivationRecord,
    *,
    reason: str,
) -> PlanActivationRecord:
    """Add deactivation information to an existing activation record."""
    return {
        **activation_record,
        "deactivated_at": datetime.now(UTC).isoformat(),
        "deactivation_reason": reason,
    }


def link_stakeholder_engagement(
    planning_engagement_log: Sequence[object],
    recovery_community_definition: str,
) -> StakeholderEngagementLink:
    """Link planning stakeholder engagement to recovery community-led approach."""
    return {
        "planning_stakeholders": len(planning_engagement_log),
        "recovery_community": recovery_community_definition,
        "continuity_status": "linked" if planning_engagement_log else "no_planning_data",
    }


def should_trigger_me_framework(plan_doc: EmergencyPlanDocument) -> bool:
    """Check if plan activation should trigger M&E framework initialisation.

    Returns True if the plan has recovery_arrangements section with content.
    """
    sections = plan_doc.get("plan_sections", {})
    recovery_section = sections.get("recovery_arrangements")
    if recovery_section and recovery_section.get("content", "").strip():
        return True
    return False
