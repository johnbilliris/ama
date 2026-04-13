"""Planning decision audit record helpers.

Generates audit records for state transitions, section edits, and endorsements.

FRs: FR-006 | Constitution §IV
"""
from datetime import UTC, datetime


def build_transition_audit(
    *, plan_id: str, from_state: str, to_state: str, user_id: str, user_role: str, reason: str = "",
) -> dict:
    return {
        "audit_type": "plan_transition",
        "plan_id": plan_id,
        "from_state": from_state,
        "to_state": to_state,
        "user_id": user_id,
        "user_role": user_role,
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def build_section_edit_audit(
    *, plan_id: str, section_slug: str, user_id: str,
) -> dict:
    return {
        "audit_type": "section_edit",
        "plan_id": plan_id,
        "section_slug": section_slug,
        "user_id": user_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def build_endorsement_audit(
    *, plan_id: str, authority_name: str, authority_role: str, approved: bool,
) -> dict:
    return {
        "audit_type": "endorsement_decision",
        "plan_id": plan_id,
        "authority_name": authority_name,
        "authority_role": authority_role,
        "approved": approved,
        "timestamp": datetime.now(UTC).isoformat(),
    }
