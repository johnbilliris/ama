"""Spec 036 / Phase F (T230) — AIIMS escalation chain.

Per Pass 1 Q-P1-03 + FR-RAG-COORD-02 / Plan §F-A9.5:

1. ``conflict_detected`` events first route to **Ops Officer**
   (``escalation_state = awaiting_ops_officer``).
2. If the Ops Officer has not acknowledged within **5 minutes**, escalate
   to the **Incident Commander (IC)** (``escalated_to_ic``).
3. When **AIIMS leadership is unreachable** AND the connection is
   degraded, transition to **Field Coordinator queue** for IC review on
   reconnect. Field Coordinators MUST NOT auto-resolve cross-agent
   conflicts.

This module exposes the escalation primitives consumed by
``apps/api/app/services/conflict_detection.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from apps.api.app.services.conflict_detection import ConflictDetection

logger = logging.getLogger(__name__)

OPS_OFFICER_UNACK_TIMEOUT = timedelta(minutes=5)


def assign_initial_owner(
    detection: ConflictDetection,
    *,
    ops_officer_id: str,
) -> ConflictDetection:
    """Stamp the Ops Officer onto a fresh detection."""
    if not ops_officer_id:
        raise ValueError("ops_officer_id required for initial AIIMS assignment")
    detection.escalation_state = "awaiting_ops_officer"
    detection.current_owner = ops_officer_id
    return detection


def escalate_on_unack(
    detection: ConflictDetection,
    *,
    incident_commander_id: str,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> bool:
    """If the 5-min unack timer has expired, escalate to the IC.

    Returns ``True`` when the state actually transitions; ``False``
    otherwise (timer not yet expired or already escalated).
    """
    if detection.escalation_state != "awaiting_ops_officer":
        return False
    ts = (now_fn or (lambda: datetime.now(tz=UTC)))()
    elapsed = ts - detection.detected_at
    if elapsed < OPS_OFFICER_UNACK_TIMEOUT:
        return False
    detection.escalation_state = "escalated_to_ic"
    detection.current_owner = incident_commander_id
    detection.extras["escalated_to_ic_at"] = ts.isoformat()

    if audit_sink is not None:
        audit_sink(
            {
                "event_type": "conflict_escalation_unack_timeout",
                "conflict_group_id": detection.conflict_group_id,
                "from_owner": "ops_officer",
                "to_owner": incident_commander_id,
                "elapsed_seconds": elapsed.total_seconds(),
                "timestamp": ts.isoformat(),
            }
        )
    return True


def queue_for_field_coordinator(
    detection: ConflictDetection,
    *,
    field_coordinator_id: str,
    aiims_unreachable: bool,
    connectivity_degraded: bool,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> bool:
    """Queue the conflict for offline IC review on reconnect.

    ONLY transitions when BOTH ``aiims_unreachable`` and
    ``connectivity_degraded`` are true (Pass 1 Q-P1-03 invariant). The
    Field Coordinator MUST NOT auto-resolve — this is a queue marker, not
    a resolution.
    """
    if not (aiims_unreachable and connectivity_degraded):
        return False
    if detection.escalation_state in ("resolved", "stale_unresolved"):
        return False
    ts = (now_fn or (lambda: datetime.now(tz=UTC)))()
    detection.escalation_state = "field_coordinator_queued"
    detection.current_owner = None  # null when queued for offline review
    detection.extras["field_coordinator_offline_queue"] = {
        "queued_at": ts.isoformat(),
        "field_coordinator_id": field_coordinator_id,
        "reconnect_required_for_resolution": True,
    }

    if audit_sink is not None:
        audit_sink(
            {
                "event_type": "conflict_field_coordinator_queued",
                "conflict_group_id": detection.conflict_group_id,
                "field_coordinator_id": field_coordinator_id,
                "timestamp": ts.isoformat(),
            }
        )
    return True


def acknowledge(
    detection: ConflictDetection,
    *,
    actor_id: str,
    accepted_audit_call_id: str | None,
    rejected_audit_call_ids: list[str] | None = None,
    resolution_note: str = "",
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> ConflictDetection:
    """Mark the conflict resolved by ``actor_id``.

    The resolver MAY accept one of the conflicting recommendations OR
    issue an independent action (``accepted_audit_call_id=None``).
    """
    if detection.escalation_state == "field_coordinator_queued":
        # Field Coordinators MUST NOT auto-resolve.
        if actor_id.startswith("field-coordinator-"):
            raise PermissionError(
                "Field Coordinators MUST NOT auto-resolve cross-agent conflicts. "
                "Reconnect to AIIMS leadership and let the IC adjudicate."
            )
    ts = (now_fn or (lambda: datetime.now(tz=UTC)))()
    detection.escalation_state = "resolved"
    detection.extras["resolution"] = {
        "resolved_at": ts.isoformat(),
        "resolver_id": actor_id,
        "accepted_audit_call_id": accepted_audit_call_id,
        "rejected_audit_call_ids": rejected_audit_call_ids or [],
        "resolution_note": resolution_note or "",
    }

    if audit_sink is not None:
        audit_sink(
            {
                "event_type": "conflict_resolved",
                "conflict_group_id": detection.conflict_group_id,
                "resolver_id": actor_id,
                "accepted_audit_call_id": accepted_audit_call_id,
                "timestamp": ts.isoformat(),
            }
        )
    return detection


__all__ = [
    "OPS_OFFICER_UNACK_TIMEOUT",
    "acknowledge",
    "assign_initial_owner",
    "escalate_on_unack",
    "queue_for_field_coordinator",
]
