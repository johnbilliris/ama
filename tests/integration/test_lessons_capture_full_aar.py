"""Spec-036 Wave 4 — T-S08 lessons-capture full-AAR integration test.

Synthesises a 30-minute simulated session by feeding `build_draft` a
representative audit log + sub-agent invocation set, then asserts:

1. All 6 named sections are present (timeline, sub_agent_responses,
   ic_decisions, identified_gaps, lessons_identified, plus the wrapped
   ExerciseOutcomeRecord).
2. Two consecutive runs produce byte-identical sections (deterministic
   ordering invariant — T-S07).
3. AIIMS attributions are populated on every sub-agent response row.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from apps.api.app.services.simulation.lessons_capture import (
    LessonsDraft,
    build_draft,
)
from packages.domain.src.domain.models.sub_agent_invocation_record import (
    SubAgentInvocationRecord,
)
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
    AuditSource,
)

SIM_ID = "11111111-2222-3333-4444-bbbbbbbbbbbb"


def _audit_entry(
    entry_type: str,
    *,
    seq: int,
    sim_id: str = SIM_ID,
    ts: datetime,
    details: dict | None = None,
) -> AuditEnvelope:
    return AuditEnvelope(
        id=f"audit-{uuid4()}",
        _partitionKey=sim_id,
        simulation_id=sim_id,
        sequence_number=seq,
        entry_type=entry_type,
        timestamp=ts,
        source=AuditSource(component="lifecycle_endpoint"),
        details=details or _minimal_details(entry_type, ts),
    )


def _minimal_details(entry_type: str, ts: datetime) -> dict:
    """Return a minimal valid details payload for the entry types used in this test."""

    if entry_type in ("lifecycle.paused",):
        return {"attempted_action": "chat_turn", "coordinator_user_id": "coord-1"}
    if entry_type == "lifecycle.resumed":
        return {"coordinator_user_id": "coord-1", "previous_paused_duration_seconds": 300}
    if entry_type == "lifecycle.aborted":
        return {
            "coordinator_user_id": "coord-1",
            "cancelled_invocations": 0,
            "abort_timestamp": ts,
            "reason": "drill-end",
        }
    return {}


def _sub_agent_record(
    *,
    role: str,
    started_at: datetime,
    invocation_id: str | None = None,
) -> SubAgentInvocationRecord:
    return SubAgentInvocationRecord(
        invocation_id=invocation_id or str(uuid4()),
        simulation_id=SIM_ID,
        tenant_id="tenant-1",
        agent_role=role,
        started_at=started_at,
        ended_at=started_at + timedelta(seconds=2),
        latency_ms=2000,
        outcome="success",
        correlation_id=str(uuid4()),
        prompt_hash="0" * 64,
        model_deployment="gpt-4o",
    )


def _build_full_corpus() -> tuple[list[AuditEnvelope], list[SubAgentInvocationRecord]]:
    """Synthesise a 30-minute simulation log."""

    start = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    audits = [
        _audit_entry("lifecycle.paused", seq=1, ts=start + timedelta(minutes=5)),
        _audit_entry("lifecycle.resumed", seq=2, ts=start + timedelta(minutes=10)),
        _audit_entry(
            "cascade.degraded_to_annotation",
            seq=3,
            ts=start + timedelta(minutes=15),
            details={
                "trigger_signal_id": "sig-1",
                "annotation_host_thread_id": "thr-1",
                "affinity_step": 1,
            },
        ),
        _audit_entry(
            "thread.cap_exceeded",
            seq=4,
            ts=start + timedelta(minutes=18),
            details={
                "proposed_thread": {"trigger_signal_id": "sig-x", "category": "weather"},
                "current_thread_count": 5,
            },
        ),
        _audit_entry("lifecycle.aborted", seq=5, ts=start + timedelta(minutes=29)),
    ]
    invocations = [
        _sub_agent_record(role="risk-assessment", started_at=start + timedelta(minutes=2)),
        _sub_agent_record(role="evacuation", started_at=start + timedelta(minutes=12)),
        _sub_agent_record(role="resource-allocation", started_at=start + timedelta(minutes=20)),
    ]
    return audits, invocations


def test_full_aar_has_all_six_sections() -> None:
    audits, invs = _build_full_corpus()
    start = audits[0].timestamp - timedelta(minutes=5)
    end = audits[-1].timestamp

    draft = build_draft(
        simulation_id=SIM_ID,
        tenant_id="tenant-1",
        start_at=start,
        end_at=end,
        end_reason="aborted",
        audit_entries=audits,
        sub_agent_invocations=invs,
    )

    assert isinstance(draft, LessonsDraft)
    # Section presence — all 6 named sections + wrapped record.
    assert draft.record.simulation_id == SIM_ID
    assert draft.timeline, "timeline must not be empty"
    assert draft.sub_agent_responses, "sub_agent_responses must not be empty"
    assert draft.ic_decisions, "ic_decisions must not be empty"
    assert draft.identified_gaps, "identified_gaps must not be empty"
    assert draft.lessons_identified, "lessons_identified must not be empty"


def test_full_aar_deterministic_across_two_runs() -> None:
    """T-S07 — two consecutive runs MUST produce byte-identical sections."""

    audits, invs = _build_full_corpus()
    start = audits[0].timestamp - timedelta(minutes=5)
    end = audits[-1].timestamp

    def _run() -> LessonsDraft:
        return build_draft(
            simulation_id=SIM_ID,
            tenant_id="tenant-1",
            start_at=start,
            end_at=end,
            end_reason="aborted",
            audit_entries=audits,
            sub_agent_invocations=invs,
        )

    a = _run()
    b = _run()
    # Compare the deterministic sections — record.generated_at differs
    # by run timestamp, so we exclude it from the diff.
    assert a.timeline == b.timeline
    assert a.sub_agent_responses == b.sub_agent_responses
    assert a.ic_decisions == b.ic_decisions
    assert a.identified_gaps == b.identified_gaps
    assert a.lessons_identified == b.lessons_identified


def test_full_aar_aiims_attributions_populated() -> None:
    """Every sub-agent row MUST carry an aiims_function attribution
    (FR-061; needed by AIDR ordering and reporting)."""

    audits, invs = _build_full_corpus()
    start = audits[0].timestamp - timedelta(minutes=5)
    end = audits[-1].timestamp

    draft = build_draft(
        simulation_id=SIM_ID,
        tenant_id="tenant-1",
        start_at=start,
        end_at=end,
        end_reason="aborted",
        audit_entries=audits,
        sub_agent_invocations=invs,
    )

    assert draft.sub_agent_responses
    for row in draft.sub_agent_responses:
        assert row.get("aiims_function"), (
            f"row missing aiims_function: {row!r}"
        )


def test_aidr_section_ordering_invariant() -> None:
    """T-S09 — AIDR sections always emit in canonical order (T-S07).

    The canonical order is: timeline, sub_agent_responses, ic_decisions,
    identified_gaps, lessons_identified. We assert the LessonsDraft
    dataclass field order matches.
    """

    audits, invs = _build_full_corpus()
    start = audits[0].timestamp - timedelta(minutes=5)
    end = audits[-1].timestamp

    draft = build_draft(
        simulation_id=SIM_ID,
        tenant_id="tenant-1",
        start_at=start,
        end_at=end,
        end_reason="aborted",
        audit_entries=audits,
        sub_agent_invocations=invs,
    )

    # Use dataclasses.fields to assert canonical order.
    import dataclasses

    field_names = [f.name for f in dataclasses.fields(draft)]
    expected_order = [
        "record",
        "timeline",
        "sub_agent_responses",
        "ic_decisions",
        "identified_gaps",
        "lessons_identified",
    ]
    assert field_names == expected_order, (
        f"AIDR section ordering drift: expected {expected_order}, got {field_names}"
    )
