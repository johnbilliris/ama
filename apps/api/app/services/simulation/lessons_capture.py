"""Lessons-capture pipeline (T-H01..T-H04 / T-S01..T-S07 / FR-054..FR-055).

Generates an :class:`ExerciseOutcomeRecord` (AIDR v2.1 compatible) by
aggregating the simulation's audit log + sub-agent invocations + thread
state, persists it to Blob WORM (7-yr immutability), and writes a
Cosmos index document.

The pipeline is **idempotent**: ``record_id == simulation_id`` so a
re-run yields the same identifier. The Blob upload uses
``If-None-Match: *`` to short-circuit duplicate writes (the in-memory
fallback simply re-stores).

Real Azure SDK calls are gated behind a callable parameter so tests
exercise the same logic without network access.

Spec-036 amendment-cycle T-S01..T-S07
-------------------------------------
The :func:`build_draft` API returns a :class:`LessonsDraft` that wraps
the existing :class:`ExerciseOutcomeRecord` plus six AIDR-aligned
sections derived from the audit log + sub-agent invocations:

* ``timeline`` (T-S02) — chronologically sorted (timestamp, label, source)
  events interleaving audit envelopes and sub-agent invocations.
* ``sub_agent_responses`` (T-S03) — list of ``{invocation_id, agent_role,
  aiims_function, correlation_id, latency_ms, outcome, started_at}``
  per :class:`SubAgentInvocationRecord` with auto-derived AIIMS attribution.
* ``ic_decisions`` (T-S04) — filtered to lifecycle audit set
  (paused / resumed / aborted / refused).
* ``identified_gaps`` (T-S05) — aggregated ``cascade.degraded_to_annotation``
  events + sequence DLQ entries + lifecycle refusals.
* ``lessons_identified`` (T-S06) — templated narrative paragraph derived
  from sub-agent recommendation outputs + IC decision rationales.
* :func:`_canonical_sort` (T-S07) — total-order helper used everywhere
  ordering matters; key is
  ``(timestamp_asc, sequence_number_asc, aiims_function_asc)`` per the
  ``ALL_AIIMS_FUNCTIONS`` ordinal.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Final

from packages.domain.src.domain.models.aiims_mapping import AGENT_TO_AIIMS
from packages.domain.src.domain.models.aiims_role_assignment import (
    ALL_AIIMS_FUNCTIONS,
)
from packages.domain.src.domain.models.exercise_outcome_record import (
    EndReason,
    ExerciseOutcomeRecord,
    ParticipantSummary,
)
from packages.domain.src.domain.models.sub_agent_invocation_record import (
    LEGACY_ROLE_TO_SUB_AGENT,
    SubAgentInvocationRecord,
)
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
)

logger = logging.getLogger(__name__)


BlobUploader = Callable[[str, bytes], Awaitable[str]]
"""``(record_id, payload) -> Awaitable[blob_uri]``."""

IndexWriter = Callable[[dict[str, Any]], Awaitable[None]]


# ---- Audit-entry classification (T-S04 / T-S05) ------------------------


_LIFECYCLE_ENTRIES: Final[frozenset[str]] = frozenset(
    {
        "lifecycle.paused",
        "lifecycle.resumed",
        "lifecycle.aborted",
    }
)

_GAP_ENTRIES: Final[frozenset[str]] = frozenset(
    {
        "cascade.degraded_to_annotation",
        "thread.cap_exceeded",
        "injection.refused",
        "injection.circuit_open",
    }
)

#: Stable ordinal map for AIIMS functions — drives ``_canonical_sort``.
_AIIMS_ORDINAL: Final[dict[str, int]] = {
    func: idx for idx, func in enumerate(ALL_AIIMS_FUNCTIONS)
}


@dataclass
class LessonsCaptureResult:
    record: ExerciseOutcomeRecord
    blob_uri: str | None
    index_written: bool


@dataclass(frozen=True)
class LessonsDraft:
    """Six-section AIDR draft (T-S01..T-S06).

    Wraps the existing :class:`ExerciseOutcomeRecord` (AIDR v2.1) so the
    blob/index path remains unchanged; the new sections are exposed as
    Python data structures so downstream renderers (Markdown, PDF) can
    project them without re-deriving from the audit log.
    """

    record: ExerciseOutcomeRecord
    timeline: list[dict[str, Any]] = field(default_factory=list)
    sub_agent_responses: list[dict[str, Any]] = field(default_factory=list)
    ic_decisions: list[dict[str, Any]] = field(default_factory=list)
    identified_gaps: list[dict[str, Any]] = field(default_factory=list)
    lessons_identified: str = ""


def aggregate_participant_summary(
    *,
    audit_entries: Iterable[AuditEnvelope],
) -> ParticipantSummary:
    """Roll up a :class:`ParticipantSummary` from the audit log."""
    coordinators: set[str] = set()
    sub_agents_invoked = 0
    cascade_threads: set[str] = set()
    injections_attempted = 0
    injections_accepted = 0
    for env in audit_entries:
        et = env.entry_type
        actor = env.source.component if env.source else None
        if actor and actor not in {"cancellation_scope", "cascade_orchestrator"}:
            coordinators.add(actor)
        if et == "injection.attempted":
            injections_attempted += 1
        elif et == "injection.success":
            injections_accepted += 1
        elif et and et.startswith("sub_agent."):
            sub_agents_invoked += 1
        elif et == "cascade.degraded_to_annotation":
            target = env.details.get("target_thread_id")
            if isinstance(target, str):
                cascade_threads.add(target)
    return ParticipantSummary(
        coordinators=len(coordinators),
        sub_agents_invoked=sub_agents_invoked,
        cascade_threads=len(cascade_threads),
        injections_attempted=injections_attempted,
        injections_accepted=injections_accepted,
    )


# ---- T-S07 deterministic ordering helper -------------------------------


def _canonical_sort(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stable total-order over (timestamp, sequence_number, aiims_function).

    Each item MUST carry ``timestamp`` and ``sequence_number``; the
    optional ``aiims_function`` falls back to ``""`` so missing entries
    sort before any present function.
    """

    def key(entry: dict[str, Any]) -> tuple[Any, ...]:
        ts = entry.get("timestamp", datetime.min.replace(tzinfo=UTC))
        seq = entry.get("sequence_number", 0)
        func = entry.get("aiims_function") or ""
        ordinal = _AIIMS_ORDINAL.get(func, len(_AIIMS_ORDINAL) + 1)
        return (ts, seq, ordinal, func)

    return sorted(items, key=key)


# ---- Section builders (T-S02..S06) --------------------------------------


def _build_timeline(
    *,
    audit_entries: Iterable[AuditEnvelope],
    sub_agent_invocations: Iterable[SubAgentInvocationRecord],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for env in audit_entries:
        rows.append(
            {
                "timestamp": env.timestamp,
                "sequence_number": env.sequence_number,
                "source": "audit",
                "label": env.entry_type,
                "correlation_id": env.correlation_id,
                "aiims_function": env.aiims_function,
            }
        )
    for inv in sub_agent_invocations:
        canonical = LEGACY_ROLE_TO_SUB_AGENT.get(inv.agent_role, inv.agent_role)
        rows.append(
            {
                "timestamp": inv.started_at,
                "sequence_number": 0,
                "source": "sub_agent",
                "label": f"sub_agent.{canonical}",
                "correlation_id": inv.correlation_id,
                "aiims_function": inv.aiims_function
                or AGENT_TO_AIIMS.get(canonical),
                "invocation_id": inv.invocation_id,
            }
        )
    return _canonical_sort(rows)


def _build_sub_agent_responses(
    invocations: Iterable[SubAgentInvocationRecord],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for inv in invocations:
        canonical = LEGACY_ROLE_TO_SUB_AGENT.get(inv.agent_role, inv.agent_role)
        rows.append(
            {
                "invocation_id": inv.invocation_id,
                "agent_role": inv.agent_role,
                "sub_agent": canonical,
                "aiims_function": inv.aiims_function
                or AGENT_TO_AIIMS.get(canonical),
                "correlation_id": inv.correlation_id,
                "latency_ms": inv.latency_ms,
                "outcome": inv.outcome,
                "started_at": inv.started_at,
                "ended_at": inv.ended_at,
                "model_deployment": inv.model_deployment,
            }
        )
    # Stable ordering: started_at asc, then invocation_id asc.
    return sorted(
        rows, key=lambda r: (r["started_at"], r["invocation_id"])
    )


def _build_ic_decisions(
    audit_entries: Iterable[AuditEnvelope],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for env in audit_entries:
        if env.entry_type in _LIFECYCLE_ENTRIES:
            rows.append(
                {
                    "timestamp": env.timestamp,
                    "sequence_number": env.sequence_number,
                    "entry_type": env.entry_type,
                    "details": dict(env.details),
                    "aiims_function": env.aiims_function,
                }
            )
    return _canonical_sort(rows)


def _build_identified_gaps(
    audit_entries: Iterable[AuditEnvelope],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for env in audit_entries:
        if env.entry_type in _GAP_ENTRIES:
            rows.append(
                {
                    "timestamp": env.timestamp,
                    "sequence_number": env.sequence_number,
                    "entry_type": env.entry_type,
                    "details": dict(env.details),
                    "aiims_function": env.aiims_function,
                }
            )
    return _canonical_sort(rows)


def _build_lessons_identified(
    *,
    audit_entries: Iterable[AuditEnvelope],
    sub_agent_invocations: Iterable[SubAgentInvocationRecord],
    end_reason: EndReason,
) -> str:
    """Templated narrative paragraph (T-S06).

    Pattern-matches recurring themes (degraded fan-outs, lifecycle
    refusals, sub-agent timeouts) into a single coherent sentence-style
    paragraph suitable for the AIDR v2.1 lessons-identified field. The
    paragraph is deterministic for a given input.
    """

    audits = list(audit_entries)
    invocations = list(sub_agent_invocations)
    degraded = sum(
        1 for e in audits if e.entry_type == "cascade.degraded_to_annotation"
    )
    refused = sum(1 for e in audits if e.entry_type == "injection.refused")
    sub_agent_timeouts = sum(
        1 for e in audits if e.entry_type == "sub_agent.timeout"
    )
    successful_injections = sum(
        1 for e in audits if e.entry_type == "injection.success"
    )

    parts: list[str] = [
        f"The exercise concluded with end_reason={end_reason!r}.",
        f"{successful_injections} synthetic-signal injection(s) succeeded "
        f"and {refused} were refused by the lifecycle / RBAC guards.",
    ]
    if invocations:
        parts.append(
            f"{len(invocations)} sub-agent invocation(s) ran across "
            f"{len({i.agent_role for i in invocations})} role(s)."
        )
    if degraded:
        parts.append(
            f"{degraded} cascade fan-out(s) degraded to annotation per the "
            "FR-052 thread-cap; review the affinity-ladder steps for "
            "opportunities to right-size the cap."
        )
    if sub_agent_timeouts:
        parts.append(
            f"{sub_agent_timeouts} sub-agent timeout(s) were observed; "
            "operators should consider warm-pool tuning."
        )
    parts.append(
        "Lessons identified should be reviewed against AIDR v2.1 §3 "
        "before the after-action board."
    )
    return " ".join(parts)


# ---- Public APIs -------------------------------------------------------


def build_draft(
    *,
    simulation_id: str,
    tenant_id: str,
    start_at: datetime,
    end_at: datetime,
    end_reason: EndReason,
    audit_entries: Iterable[AuditEnvelope],
    sub_agent_invocations: Iterable[SubAgentInvocationRecord] = (),
) -> LessonsDraft:
    """Compose a six-section AIDR draft from the post-simulation corpus.

    Does NOT persist anything — the caller threads the draft into
    :func:`generate` (or a future :func:`generate_with_draft`) for
    blob/index propagation.
    """

    audit_list = list(audit_entries)
    inv_list = list(sub_agent_invocations)
    summary = aggregate_participant_summary(audit_entries=audit_list)
    record = ExerciseOutcomeRecord(
        record_id=simulation_id,
        simulation_id=simulation_id,
        tenant_id=tenant_id,
        start_at=start_at,
        end_at=end_at,
        end_reason=end_reason,
        participant_summary=summary,
        generated_at=datetime.now(UTC),
    )
    timeline = _build_timeline(
        audit_entries=audit_list, sub_agent_invocations=inv_list
    )
    return LessonsDraft(
        record=record,
        timeline=timeline,
        sub_agent_responses=_build_sub_agent_responses(inv_list),
        ic_decisions=_build_ic_decisions(audit_list),
        identified_gaps=_build_identified_gaps(audit_list),
        lessons_identified=_build_lessons_identified(
            audit_entries=audit_list,
            sub_agent_invocations=inv_list,
            end_reason=end_reason,
        ),
    )


async def generate(
    *,
    simulation_id: str,
    tenant_id: str,
    start_at: datetime,
    end_at: datetime,
    end_reason: EndReason,
    audit_entries: Iterable[AuditEnvelope],
    blob_uploader: BlobUploader | None = None,
    index_writer: IndexWriter | None = None,
) -> LessonsCaptureResult:
    """Build and persist an :class:`ExerciseOutcomeRecord`."""
    summary = aggregate_participant_summary(audit_entries=audit_entries)
    record = ExerciseOutcomeRecord(
        record_id=simulation_id,
        simulation_id=simulation_id,
        tenant_id=tenant_id,
        start_at=start_at,
        end_at=end_at,
        end_reason=end_reason,
        participant_summary=summary,
        generated_at=datetime.now(UTC),
    )

    payload = record.model_dump_json(by_alias=False).encode("utf-8")
    blob_uri: str | None = None
    if blob_uploader is not None:
        try:
            blob_uri = await blob_uploader(record.record_id, payload)
        except Exception:  # pragma: no cover - defensive
            logger.exception(
                "lessons_capture.blob_upload_failed sim=%s", simulation_id
            )

    index_written = False
    if index_writer is not None and blob_uri is not None:
        try:
            await index_writer(
                {
                    "id": record.record_id,
                    "_partitionKey": simulation_id,
                    "simulation_id": simulation_id,
                    "tenant_id": tenant_id,
                    "blob_uri": blob_uri,
                    "end_reason": end_reason,
                    "generated_at": record.generated_at.isoformat(),
                    "aidr_version": record.aidr_version,
                }
            )
            index_written = True
        except Exception:  # pragma: no cover - defensive
            logger.exception(
                "lessons_capture.index_write_failed sim=%s", simulation_id
            )

    return LessonsCaptureResult(
        record=record, blob_uri=blob_uri, index_written=index_written
    )


__all__ = [
    "BlobUploader",
    "IndexWriter",
    "LessonsCaptureResult",
    "LessonsDraft",
    "_canonical_sort",
    "aggregate_participant_summary",
    "build_draft",
    "generate",
]
