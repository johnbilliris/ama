"""Tests for spec-036 T-S01..S07 — AIDR section builders for lessons capture.

The orchestrator extends :mod:`apps.api.app.services.simulation.lessons_capture`
with six AIDR-aligned sections per audit-envelope.md §6 and the AIDR v2.1
template. The existing ``generate()`` flow is preserved unchanged; the new
``build_draft()`` API returns a :class:`LessonsDraft` that wraps the
existing :class:`ExerciseOutcomeRecord` plus the six rendered sections.

Section assignment (canonical, per tasks.md §17):
    1. timeline                  — T-S02
    2. sub_agent_responses       — T-S03
    3. ic_decisions              — T-S04
    4. identified_gaps           — T-S05
    5. lessons_identified        — T-S06
    6. (canonical sort helper)   — T-S07

Constitution invariants:
    - **AIIMS alignment** — every sub-agent invocation included in the
      draft carries an ``aiims_function`` attribution (constitution v1.2.0).
    - **Deterministic ordering** — ``_canonical_sort`` produces byte-stable
      output across runs so two AAR exports for the same session are
      bit-identical.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from apps.api.app.services.simulation.lessons_capture import (
    LessonsDraft,
    _canonical_sort,
    build_draft,
)
from packages.domain.src.domain.models.sub_agent_invocation_record import (
    SubAgentInvocationRecord,
)
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
)

# ---- Helpers ------------------------------------------------------------


def _audit(
    *,
    sim_id: str = "sim-S",
    seq: int = 1,
    entry_type: str = "injection.success",
    timestamp: datetime | None = None,
    details: dict | None = None,
    correlation_id: str | None = None,
) -> AuditEnvelope:
    base_details = {
        "injection_id": str(uuid4()),
        "watermark_text_id": "wm.bushfire.bom-fires.v1",
        "viewport_hint_match": True,
    }
    if entry_type == "injection.attempted":
        base_details = {
            "channel": "weather",
            "audience": "Risk",
            "rendered_chat_text": "[SIMULATION] hot wind warning",
            "viewport_hint_match": True,
        }
    elif entry_type == "lifecycle.paused":
        base_details = {"attempted_action": "chat_turn"}
    elif entry_type == "lifecycle.resumed":
        base_details = {"reason": "operator_resumed"}
    elif entry_type == "lifecycle.aborted":
        base_details = {"reason": "operator_aborted"}
    elif entry_type == "cascade.degraded_to_annotation":
        base_details = {
            "host_thread_id": "thread-host-1",
            "target_thread_id": "thread-degraded-1",
            "reason": "thread_cap_reached",
            "affinity_ladder_step": 1,
        }
    return AuditEnvelope.model_validate(
        {
            "id": str(uuid4()),
            "_partitionKey": sim_id,
            "simulation_id": sim_id,
            "sequence_number": seq,
            "entry_type": entry_type,
            "timestamp": timestamp or datetime.now(UTC),
            "source": {"component": "controller_service"},
            "details": details or base_details,
            "correlation_id": correlation_id,
        }
    )


def _invocation(
    *,
    sim_id: str = "sim-S",
    invocation_id: str | None = None,
    agent_role: str = "risk-assessment",
    correlation_id: str | None = "corr-1",
    started_at: datetime | None = None,
) -> SubAgentInvocationRecord:
    started = started_at or datetime.now(UTC)
    return SubAgentInvocationRecord(
        invocation_id=invocation_id or str(uuid4()),
        simulation_id=sim_id,
        tenant_id="tenant-pacific",
        agent_role=agent_role,
        prompt_hash="a" * 64,
        model_deployment="gpt-4o-mini-australiaeast",
        latency_ms=120,
        outcome="success",
        started_at=started,
        ended_at=started + timedelta(seconds=2),
        correlation_id=correlation_id,
    )


# ---- T-S01 LessonsDraft skeleton ---------------------------------------


def test_build_draft_returns_lessons_draft_with_six_sections() -> None:
    audit = [
        _audit(seq=1, entry_type="injection.attempted"),
        _audit(seq=2, entry_type="lifecycle.paused"),
    ]
    invocations = [_invocation()]
    draft = build_draft(
        simulation_id="sim-S1",
        tenant_id="tenant-pacific",
        start_at=datetime.now(UTC) - timedelta(minutes=30),
        end_at=datetime.now(UTC),
        end_reason="completed",
        audit_entries=audit,
        sub_agent_invocations=invocations,
    )
    assert isinstance(draft, LessonsDraft)
    # All six sections present (T-S02..T-S06 + record).
    assert hasattr(draft, "timeline")
    assert hasattr(draft, "sub_agent_responses")
    assert hasattr(draft, "ic_decisions")
    assert hasattr(draft, "identified_gaps")
    assert hasattr(draft, "lessons_identified")
    assert draft.record.record_id == "sim-S1"


# ---- T-S02 timeline section ---------------------------------------------


def test_timeline_interleaves_audit_and_invocations_in_chronological_order() -> None:
    t0 = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    audit = [
        _audit(seq=1, entry_type="injection.attempted", timestamp=t0),
        _audit(seq=2, entry_type="injection.success", timestamp=t0 + timedelta(seconds=5)),
    ]
    inv = [
        _invocation(started_at=t0 + timedelta(seconds=2)),
    ]
    draft = build_draft(
        simulation_id="sim-S2",
        tenant_id="tenant-pacific",
        start_at=t0,
        end_at=t0 + timedelta(minutes=10),
        end_reason="completed",
        audit_entries=audit,
        sub_agent_invocations=inv,
    )
    # Timeline produces (timestamp, label, source) tuples sorted asc.
    timestamps = [entry["timestamp"] for entry in draft.timeline]
    assert timestamps == sorted(timestamps)
    sources = {entry["source"] for entry in draft.timeline}
    assert "audit" in sources
    assert "sub_agent" in sources


# ---- T-S03 sub-agent responses section ---------------------------------


def test_sub_agent_responses_attribute_aiims_function() -> None:
    inv = _invocation(agent_role="risk-assessment")
    draft = build_draft(
        simulation_id="sim-S3",
        tenant_id="tenant-pacific",
        start_at=datetime.now(UTC) - timedelta(minutes=10),
        end_at=datetime.now(UTC),
        end_reason="completed",
        audit_entries=[],
        sub_agent_invocations=[inv],
    )
    assert len(draft.sub_agent_responses) == 1
    response = draft.sub_agent_responses[0]
    assert response["correlation_id"] == "corr-1"
    assert response["aiims_function"] == "planning"
    assert response["agent_role"] == "risk-assessment"


# ---- T-S04 IC decisions section ----------------------------------------


def test_ic_decisions_filters_lifecycle_entries() -> None:
    audit = [
        _audit(seq=1, entry_type="lifecycle.paused"),
        _audit(seq=2, entry_type="lifecycle.resumed"),
        _audit(seq=3, entry_type="lifecycle.aborted"),
        _audit(seq=4, entry_type="injection.success"),  # excluded
    ]
    draft = build_draft(
        simulation_id="sim-S4",
        tenant_id="tenant-pacific",
        start_at=datetime.now(UTC) - timedelta(minutes=10),
        end_at=datetime.now(UTC),
        end_reason="completed",
        audit_entries=audit,
        sub_agent_invocations=[],
    )
    types = {d["entry_type"] for d in draft.ic_decisions}
    assert types == {"lifecycle.paused", "lifecycle.resumed", "lifecycle.aborted"}


# ---- T-S05 identified gaps section -------------------------------------


def test_identified_gaps_aggregates_degraded_fan_outs() -> None:
    audit = [
        _audit(seq=1, entry_type="cascade.degraded_to_annotation"),
        _audit(seq=2, entry_type="cascade.degraded_to_annotation"),
        _audit(seq=3, entry_type="injection.success"),  # not a gap
    ]
    draft = build_draft(
        simulation_id="sim-S5",
        tenant_id="tenant-pacific",
        start_at=datetime.now(UTC) - timedelta(minutes=10),
        end_at=datetime.now(UTC),
        end_reason="completed",
        audit_entries=audit,
        sub_agent_invocations=[],
    )
    assert len(draft.identified_gaps) == 2
    assert all(g["entry_type"] == "cascade.degraded_to_annotation" for g in draft.identified_gaps)


# ---- T-S06 lessons-identified narrative --------------------------------


def test_lessons_identified_returns_narrative_paragraph() -> None:
    audit = [
        _audit(seq=1, entry_type="injection.success"),
        _audit(seq=2, entry_type="cascade.degraded_to_annotation"),
        _audit(seq=3, entry_type="lifecycle.aborted"),
    ]
    inv = [_invocation(agent_role="risk-assessment")]
    draft = build_draft(
        simulation_id="sim-S6",
        tenant_id="tenant-pacific",
        start_at=datetime.now(UTC) - timedelta(minutes=10),
        end_at=datetime.now(UTC),
        end_reason="completed",
        audit_entries=audit,
        sub_agent_invocations=inv,
    )
    assert isinstance(draft.lessons_identified, str)
    # A coherent paragraph (single string) — at least 50 chars and ends with '.'.
    assert len(draft.lessons_identified) >= 50
    assert draft.lessons_identified.rstrip().endswith(".")


# ---- T-S07 deterministic ordering ---------------------------------------


def test_canonical_sort_total_order() -> None:
    t0 = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    items = [
        {"timestamp": t0 + timedelta(seconds=2), "sequence_number": 5, "aiims_function": "operations"},
        {"timestamp": t0, "sequence_number": 1, "aiims_function": "planning"},
        {"timestamp": t0 + timedelta(seconds=2), "sequence_number": 3, "aiims_function": "intelligence"},
        {"timestamp": t0, "sequence_number": 1, "aiims_function": "operations"},
    ]
    sorted_items = _canonical_sort(items)
    # Stable across runs.
    assert _canonical_sort(items) == sorted_items
    # Total order respects (timestamp asc, sequence_number asc, aiims asc).
    assert sorted_items[0]["timestamp"] == t0
    assert sorted_items[-1]["sequence_number"] == 5


def test_canonical_sort_handles_missing_aiims() -> None:
    """An entry without an ``aiims_function`` key sorts deterministically."""

    items = [
        {"timestamp": datetime(2025, 1, 1, 9, 0, tzinfo=UTC), "sequence_number": 2},
        {"timestamp": datetime(2025, 1, 1, 9, 0, tzinfo=UTC), "sequence_number": 1},
    ]
    out = _canonical_sort(items)
    assert [e["sequence_number"] for e in out] == [1, 2]
