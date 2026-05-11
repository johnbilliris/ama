"""T226 — F-A9 AIIMS escalation chain (FR-RAG-COORD-02; Pass 1 Q-P1-03).

Asserts:

1. Initial assignment goes to Ops Officer.
2. 5-min unack timer expires → escalation to IC.
3. AIIMS unreachable + connectivity degraded → Field Coordinator queue.
4. Field Coordinators MUST NOT auto-resolve cross-agent conflicts.
5. IC adjudication transitions to ``resolved`` with full audit trail.

Proves: T230.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from apps.api.app.services.aiims_escalation import (
    OPS_OFFICER_UNACK_TIMEOUT,
    acknowledge,
    assign_initial_owner,
    escalate_on_unack,
    queue_for_field_coordinator,
)
from apps.api.app.services.conflict_detection import (
    AgentRecommendation,
    ConflictDetection,
)


def _now() -> datetime:
    return datetime(2026, 5, 15, 3, 42, 30, tzinfo=UTC)


def _make_detection() -> ConflictDetection:
    return ConflictDetection(
        conflict_group_id="01910f6c-4a23-72e3-9e1f-0aa11ac6f8b0",
        detected_at=_now(),
        conflict_class="spatial",
        agent_recommendations=[
            AgentRecommendation(
                agent_name="EvacuationAgent",
                audit_call_id="11111111-1111-1111-1111-111111111111",
                recommendation_summary="Evacuate.",
            ),
            AgentRecommendation(
                agent_name="RiskAssessmentAgent",
                audit_call_id="22222222-2222-2222-2222-222222222222",
                recommendation_summary="Shelter-in-place.",
            ),
        ],
    )


def test_initial_assignment_goes_to_ops_officer() -> None:
    detection = _make_detection()
    assign_initial_owner(detection, ops_officer_id="ops-officer-nsw-1@ama.local")
    assert detection.escalation_state == "awaiting_ops_officer"
    assert detection.current_owner == "ops-officer-nsw-1@ama.local"


def test_initial_assignment_requires_ops_officer_id() -> None:
    detection = _make_detection()
    with pytest.raises(ValueError, match="ops_officer_id required"):
        assign_initial_owner(detection, ops_officer_id="")


def test_no_escalation_before_5min_timeout() -> None:
    detection = _make_detection()
    assign_initial_owner(detection, ops_officer_id="ops-1@ama.local")
    audit: list[dict[str, Any]] = []
    # Only 2min after detection — under the timeout.
    transition = escalate_on_unack(
        detection,
        incident_commander_id="ic-nsw@ama.local",
        audit_sink=audit.append,
        now_fn=lambda: _now() + timedelta(minutes=2),
    )
    assert transition is False
    assert detection.escalation_state == "awaiting_ops_officer"
    assert audit == []


def test_5min_unack_escalates_to_ic() -> None:
    detection = _make_detection()
    assign_initial_owner(detection, ops_officer_id="ops-1@ama.local")
    audit: list[dict[str, Any]] = []
    transition = escalate_on_unack(
        detection,
        incident_commander_id="ic-nsw@ama.local",
        audit_sink=audit.append,
        now_fn=lambda: _now() + OPS_OFFICER_UNACK_TIMEOUT + timedelta(seconds=1),
    )
    assert transition is True
    assert detection.escalation_state == "escalated_to_ic"
    assert detection.current_owner == "ic-nsw@ama.local"
    assert any(e["event_type"] == "conflict_escalation_unack_timeout" for e in audit)


def test_field_coordinator_queue_requires_both_unreachable_and_degraded() -> None:
    detection = _make_detection()
    assign_initial_owner(detection, ops_officer_id="ops-1@ama.local")
    # Only one of the two conditions met → no transition.
    transition = queue_for_field_coordinator(
        detection,
        field_coordinator_id="fc-bega@ama.local",
        aiims_unreachable=True,
        connectivity_degraded=False,
    )
    assert transition is False
    assert detection.escalation_state == "awaiting_ops_officer"


def test_field_coordinator_queue_when_both_conditions_met() -> None:
    detection = _make_detection()
    assign_initial_owner(detection, ops_officer_id="ops-1@ama.local")
    audit: list[dict[str, Any]] = []
    transition = queue_for_field_coordinator(
        detection,
        field_coordinator_id="fc-bega@ama.local",
        aiims_unreachable=True,
        connectivity_degraded=True,
        audit_sink=audit.append,
        now_fn=_now,
    )
    assert transition is True
    assert detection.escalation_state == "field_coordinator_queued"
    assert detection.current_owner is None  # null when queued for offline review
    assert detection.extras["field_coordinator_offline_queue"]["reconnect_required_for_resolution"] is True
    assert any(e["event_type"] == "conflict_field_coordinator_queued" for e in audit)


def test_field_coordinator_must_not_auto_resolve() -> None:
    detection = _make_detection()
    queue_for_field_coordinator(
        detection,
        field_coordinator_id="field-coordinator-bega-1@ama.local",
        aiims_unreachable=True,
        connectivity_degraded=True,
    )
    # Field Coordinator attempts to resolve while still queued.
    with pytest.raises(PermissionError, match="MUST NOT auto-resolve"):
        acknowledge(
            detection,
            actor_id="field-coordinator-bega-1@ama.local",
            accepted_audit_call_id=None,
        )


def test_ic_adjudication_resolves_with_full_audit() -> None:
    detection = _make_detection()
    assign_initial_owner(detection, ops_officer_id="ops-1@ama.local")
    escalate_on_unack(
        detection,
        incident_commander_id="ic-nsw@ama.local",
        now_fn=lambda: _now() + OPS_OFFICER_UNACK_TIMEOUT + timedelta(seconds=1),
    )
    audit: list[dict[str, Any]] = []
    acknowledge(
        detection,
        actor_id="ic-nsw@ama.local",
        accepted_audit_call_id="11111111-1111-1111-1111-111111111111",
        rejected_audit_call_ids=["22222222-2222-2222-2222-222222222222"],
        resolution_note="Evacuation order accepted; shelter-in-place is unsafe given road compromise.",
        audit_sink=audit.append,
        now_fn=lambda: _now() + timedelta(minutes=10),
    )
    assert detection.escalation_state == "resolved"
    assert detection.extras["resolution"]["resolver_id"] == "ic-nsw@ama.local"
    assert any(e["event_type"] == "conflict_resolved" for e in audit)
