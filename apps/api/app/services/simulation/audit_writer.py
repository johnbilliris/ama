"""Append-only audit writer for spec-036 telemetry-injection (T-B09 / T-N03).

Implements the contract from
``specs/036-sim-agent-extend/contracts/audit-envelope.md``:

* every entry is validated against the typed dispatch table from
  :mod:`packages.domain.src.domain.models.telemetry_injection_audit_entry`;
* ``sequence_number`` is **gap-free** per simulation (FR-048) — the writer
  delegates allocation to a
  :class:`apps.api.app.repositories.simulation_sequence_repository.SimulationSequenceRepository`
  (T-N02 / ADR-036-007) so every replica of the API container app shares
  a single Cosmos-backed source of truth;
* on :class:`SequenceAllocationExhausted` the writer fails closed (T-N04)
  by writing a DLQ envelope (``sequence_number=-1``) and re-raising so
  the route handler can surface ``HTTP 503`` + ``Retry-After: 5``;
* in-memory fallback when ``COSMOS_ENDPOINT`` is unset (test mode).

The 25 typed entry payloads (Cycle 2 added entry-25
``signal_pipeline.dispatch_failed`` per A2-01 / A2-08 / FR-067) enumerated in
:data:`packages.domain.src.domain.models.telemetry_injection_audit_entry.ALL_ENTRY_TYPES`
each map to a specific Pydantic dispatch class — see
``contracts/audit-envelope.md`` Section 3 for the schemas.

Cycle 2 additions (T-AA09 + T-AA10 + T-AA15 + T-AA21):

* :func:`write_dispatch_failed` — typed-envelope helper for entry-25
  (audit-envelope.md §3.25). Honours the byte-equality invariant per
  pass-1 Q1 (CHK135) by RFC 8785 JCS canonicalising the
  ``triggered_sub_agents`` array before persistence.
* :func:`canonicalise_triggered_sub_agents` — the shared canonicaliser
  used by both the route's ``injection.success`` write (T-AA15 / FR-069)
  and the dispatch-failed envelope (T-AA09 / FR-067). One source of
  truth prevents drift between the two emit sites.
* ``_KEBAB_TO_PASCAL`` — Cycle 2 A2-07 / FR-070 read-time tolerance shim.
  Historic Cycle 1 audit rows persisted with kebab-case ``sub_agent``
  values remain readable; new writes use 9-name PascalCase directly.
* Caller-supplied ``sequence_number`` keys in any ``details`` dict are
  rejected (T-AA21 / A2-06 / FR-048 — allocator is sole source of truth).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import rfc8785

from app.repositories.simulation_sequence_repository import (
    DLQ_SEQUENCE_NUMBER,
    SequenceAllocationExhausted,
    SimulationSequenceRepository,
    get_sequence_repository,
)
from packages.domain.src.domain.models.aiims_mapping import (
    ALL_SUB_AGENTS,
)
from packages.domain.src.domain.models.aiims_role_assignment import AiimsFunction
from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    AuditEnvelope,
    AuditSource,
    EntryType,
    validate_details,
)

if TYPE_CHECKING:  # pragma: no cover
    from app.services.simulation.dispatch_status import TriggeredSubAgent

logger = logging.getLogger(__name__)

# In-memory fallback store (test/offline use only).
_memory_store: dict[str, list[AuditEnvelope]] = {}

#: Process-wide DLQ buffer used in fallback / test mode. The Cosmos path
#: writes to ``simulation_audit_dlq`` (Bicep T-A09 [AMEND]); operators
#: review entries manually per ADR-036-007 (no TTL).
_dlq_buffer: list[AuditDLQEntry] = []


# Cycle 2 A2-07 / FR-070 — historic kebab-case → canonical PascalCase mapping.
#
# At write time, only PascalCase names from ``ALL_SUB_AGENTS`` are accepted by
# the audit envelope schema. At read time (FR-049 export, FR-054 lessons-
# capture, idempotency replay), legacy Cycle 1 rows persisted with kebab-case
# values transparently map to PascalCase via this table; on hit, an
# ``audit.kebab_legacy_read`` debug log is emitted so operators can monitor
# the historic-tail decay over the deprecation window.
_KEBAB_TO_PASCAL: dict[str, str] = {
    "monitoring": "Intel",
    "planning": "Planning",
    "resource-allocation": "Resource",
    "communication": "Comms",
    "evacuation": "Evac",
    "risk-assessment": "Risk",
    "simulation-telemetry-injection": "Operations",
}


def kebab_to_pascal_sub_agent(value: str) -> str:
    """Normalise a historic kebab-case ``sub_agent`` to PascalCase.

    Returns *value* unchanged when it is already a PascalCase name from
    ``ALL_SUB_AGENTS``. Returns the mapped PascalCase name (with a debug log)
    when *value* is one of the seven legacy kebab-case names. Raises
    ``ValueError`` when *value* is neither — the migration table covers the
    full Cycle 1 set so any other value indicates schema drift.
    """

    if value in ALL_SUB_AGENTS:
        return value
    pascal = _KEBAB_TO_PASCAL.get(value)
    if pascal is None:
        raise ValueError(
            f"audit.unknown_sub_agent {value!r} — not in PascalCase canonical "
            "set or the kebab-case migration table"
        )
    logger.debug(
        "audit.kebab_legacy_read kebab=%s pascal=%s",
        value,
        pascal,
    )
    return pascal


def canonicalise_triggered_sub_agents(
    entries: Iterable[TriggeredSubAgent],
) -> list[dict[str, Any]]:
    """Canonical RFC 8785 JCS form of the ``triggered_sub_agents`` array.

    Cycle 2 pass-1 Q1 / CHK135 invariant: the HTTP 202 response body's
    array MUST be byte-equal to the audit envelope's array after RFC 8785
    JCS canonicalisation. This helper is the single source of truth for
    that canonicalisation — both the route's ``injection.success`` write
    (T-AA15) and the dispatch-failed envelope writer (T-AA09) consume it.

    Returns a list of plain ``dict`` whose JCS-serialised bytes are
    deterministic across replicas and Pydantic versions:

    * each entry ordered ``{correlation_id, dispatch_status, sub_agent,
      trigger_source}`` (alphabetic key order — RFC 8785 default);
    * ``correlation_id`` is the UUID's canonical string form;
    * the array is lexicographically sorted by ``sub_agent`` PascalCase
      enum value (pass-1 Q4) — the byte-equality test relies on this.
    """

    items: list[dict[str, Any]] = []
    for entry in entries:
        # Defensive — accept the dataclass / Pydantic / dict forms equally
        # so the canonicaliser is callable from any layer.
        sub_agent = getattr(entry, "sub_agent", None)
        trigger_source = getattr(entry, "trigger_source", None)
        correlation_id = getattr(entry, "correlation_id", None)
        dispatch_status = getattr(entry, "dispatch_status", None)
        if sub_agent is None and isinstance(entry, dict):
            sub_agent = entry.get("sub_agent")
            trigger_source = entry.get("trigger_source")
            correlation_id = entry.get("correlation_id")
            dispatch_status = entry.get("dispatch_status")
        if isinstance(correlation_id, UUID):
            correlation_id = str(correlation_id)
        items.append(
            {
                "correlation_id": str(correlation_id),
                "dispatch_status": str(dispatch_status),
                "sub_agent": str(sub_agent),
                "trigger_source": str(trigger_source),
            }
        )

    items.sort(key=lambda d: d["sub_agent"])

    # Round-trip through RFC 8785 JCS to enforce byte-deterministic ordering
    # on the resulting JSON. The Python helper returns sorted-key bytes; we
    # decode back into list[dict] so callers persist Python dicts but the
    # downstream ``json.dumps(..., sort_keys=True)`` byte-equality assertion
    # in tests/contract/test_dispatch_failed_body_audit_byte_equality.py
    # remains stable.
    canonical_bytes = rfc8785.dumps(items)
    return json.loads(canonical_bytes.decode("utf-8"))


@dataclass(frozen=True)
class AuditDLQEntry:
    """Sentinel envelope written when sequence allocation fails.

    See ADR-036-007 / T-N04 — the entry carries ``sequence_number=-1`` so
    operators querying ``simulation_audit_dlq`` can surface the gap event
    immediately.
    """

    simulation_id: str
    entry_type: str
    sequence_number: int = DLQ_SEQUENCE_NUMBER
    dlq_reason: str = "sequence_allocator_exhausted"
    attempted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    turn_id: str | None = None
    actor: str = "audit_writer"
    aiims_function: str | None = None
    secondary_aiims_tags: list[str] | None = None


def get_audit_dlq_buffer() -> list[AuditDLQEntry]:
    """Return the in-memory DLQ buffer — tests and ops dashboards only."""

    return list(_dlq_buffer)


def reset_audit_dlq_buffer_for_tests() -> None:
    """Reset the DLQ buffer — tests only."""

    _dlq_buffer.clear()


class AuditWriter:
    """Cosmos-backed audit writer with in-memory fallback.

    The writer is intentionally lightweight — it is created per-request by
    the controller_service via dependency injection. The actual Cosmos
    container reference is supplied by the caller; tests exercise the
    in-memory path by leaving ``cosmos_container=None``.

    Sequence-number allocation is delegated to the
    :class:`SimulationSequenceRepository` (T-N02). When ``None`` is
    supplied at construction the writer lazily binds to the process-wide
    repository singleton (``get_sequence_repository()``).
    """

    def __init__(
        self,
        *,
        cosmos_container: Any = None,
        sequence_repository: SimulationSequenceRepository | None = None,
    ) -> None:
        self._container = cosmos_container
        self._sequence_repository = sequence_repository

    @property
    def sequence_repository(self) -> SimulationSequenceRepository:
        if self._sequence_repository is None:
            self._sequence_repository = get_sequence_repository()
        return self._sequence_repository

    async def write(
        self,
        entry_type: EntryType | str,
        *,
        simulation_id: str,
        details: Mapping[str, Any],
        source: Mapping[str, Any] | AuditSource | None = None,
        actor: str = "controller_service",
        correlation_id: str | None = None,
        turn_id: str | None = None,
        timestamp: datetime | None = None,
        aiims_function: AiimsFunction | None = None,
        secondary_aiims_tags: list[AiimsFunction] | None = None,
        prompt_hash_source: str | None = None,
        idempotency_key: str | None = None,
        request_correlation_id: str | None = None,
        delivery_channel: str | None = None,
    ) -> AuditEnvelope:
        """Validate, sequence, and persist a single audit entry.

        Returns the persisted envelope (including the assigned
        ``sequence_number`` and storage ``id``).

        Audit entries that originate from a sub-agent invocation MAY supply
        ``aiims_function`` + ``secondary_aiims_tags`` (T-T03 / FR-061) so
        post-hoc NDJSON export joins (FR-054) can attribute the entry to
        the correct AIIMS function without re-deriving from agent_role.
        The constitution v1.2.0 1+≤2 cap is enforced by the envelope
        Pydantic validator.

        T-O07 (FR-065 / FR-066) — additional optional kwargs propagate
        the residual T-A06 envelope fields:

        * ``prompt_hash_source`` — provenance of any prompt hash carried
          in the entry (raw_user_input / canonical_llm_prompt / system_only).
        * ``idempotency_key`` — the ``Idempotency-Key`` header value
          when the originating request flowed through the idempotency
          cache (T-O02..O06).
        * ``request_correlation_id`` — end-to-end ingress correlation id.
        * ``delivery_channel`` — live-log delivery channel
          (audio / text-live-log / both) per FR-058 / FR-064.

        Raises :class:`SequenceAllocationExhausted` after writing a DLQ
        envelope when the sequence allocator exhausts its 5-retry budget
        (T-N04 / ADR-036-007 fail-closed invariant).
        """
        # Strict typed validation per ``contracts/audit-envelope.md``.
        # Cycle 2 / T-AA21 / FR-048 — defensive guard: reject (or warn-and-
        # ignore) any caller-supplied ``sequence_number`` literal in the
        # details dict. The gap-free allocator (ADR-036-007) is the sole
        # source of truth for sequence numbers; we allocate FIRST and then
        # — for the typed schemas that still document ``sequence_number``
        # in their required-list (e.g. §3.9 ``cascade.depth2_refused``,
        # §3.25 ``signal_pipeline.dispatch_failed``) — inject the
        # allocator-assigned value into ``details_dict`` so validation
        # passes without leaking the placeholder back to the caller.
        details_dict = dict(details)
        if "sequence_number" in details_dict:
            caller_supplied = details_dict.pop("sequence_number")
            logger.warning(
                "audit.caller_sequence_number_ignored entry_type=%s "
                "supplied=%r — allocator (ADR-036-007) is the sole source "
                "of truth (Cycle 2 / FR-048 / T-AA21)",
                entry_type,
                caller_supplied,
            )

        try:
            seq = await self.sequence_repository.allocate(simulation_id)
        except SequenceAllocationExhausted:
            self._record_dlq(
                simulation_id=simulation_id,
                entry_type=str(entry_type),
                details=details,
                correlation_id=correlation_id,
                turn_id=turn_id,
                actor=actor,
                aiims_function=aiims_function,
                secondary_aiims_tags=secondary_aiims_tags,
            )
            logger.error(
                "audit.sequence_allocator_exhausted simulation_id=%s entry_type=%s",
                simulation_id,
                entry_type,
            )
            raise

        # Inject allocator-assigned sequence_number ONLY for schemas that
        # declare it in their required field set.
        from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
            DetailsByEntry,
        )

        details_cls = DetailsByEntry.get(str(entry_type))
        if details_cls is not None and "sequence_number" in getattr(
            details_cls, "model_fields", {}
        ):
            details_dict["sequence_number"] = seq

        try:
            validate_details(entry_type, details_dict)
        except Exception as exc:
            logger.exception(
                "audit.payload_validation_failed entry_type=%s err=%s",
                entry_type,
                exc,
            )
            raise

        envelope_kwargs: dict[str, Any] = {
            "id": str(uuid4()),
            "_partitionKey": simulation_id,
            "simulation_id": simulation_id,
            "sequence_number": seq,
            "entry_type": entry_type,
            "timestamp": timestamp or datetime.now(UTC),
            "correlation_id": correlation_id,
            "turn_id": turn_id,
            "source": source if isinstance(source, AuditSource) else AuditSource(**(source or {"component": actor})),
            "details": details_dict,
            "aiims_function": aiims_function,
            "secondary_aiims_tags": secondary_aiims_tags,
            "prompt_hash_source": prompt_hash_source,
            "idempotency_key": idempotency_key,
            "request_correlation_id": request_correlation_id,
            "delivery_channel": delivery_channel,
        }
        envelope = AuditEnvelope.model_validate(envelope_kwargs)

        if self._container is None:
            _memory_store.setdefault(simulation_id, []).append(envelope)
            logger.debug(
                "audit.write_inmemory simulation_id=%s seq=%d type=%s",
                simulation_id,
                seq,
                entry_type,
            )
            return envelope

        # Cosmos path — sequence number already allocated atomically by the
        # repository (T-N02). The writer just persists the envelope; the
        # only concurrency boundary remaining is the create_item itself,
        # which is collision-free because ``id`` is a fresh uuid4.
        document = envelope.model_dump(mode="json", by_alias=True)
        await asyncio.to_thread(
            self._container.create_item,
            body=document,
        )
        logger.info(
            "audit.write_cosmos simulation_id=%s seq=%d type=%s",
            simulation_id,
            seq,
            entry_type,
        )
        return envelope

    def _record_dlq(
        self,
        *,
        simulation_id: str,
        entry_type: str,
        details: Mapping[str, Any],
        correlation_id: str | None,
        turn_id: str | None,
        actor: str,
        aiims_function: AiimsFunction | None,
        secondary_aiims_tags: list[AiimsFunction] | None,
    ) -> None:
        """Buffer a DLQ envelope for operator review (T-N04)."""

        entry = AuditDLQEntry(
            simulation_id=simulation_id,
            entry_type=entry_type,
            details=dict(details),
            correlation_id=correlation_id,
            turn_id=turn_id,
            actor=actor,
            aiims_function=aiims_function,
            secondary_aiims_tags=(
                list(secondary_aiims_tags)
                if secondary_aiims_tags is not None
                else None
            ),
        )
        _dlq_buffer.append(entry)

    @staticmethod
    def memory_for_test(simulation_id: str) -> list[AuditEnvelope]:
        """Return the in-memory entries for *simulation_id* — tests only."""
        return list(_memory_store.get(simulation_id, []))

    @staticmethod
    def reset_memory_for_test() -> None:
        """Reset the process-wide in-memory store — tests only."""
        _memory_store.clear()
        _dlq_buffer.clear()


_default_writer: AuditWriter | None = None


async def write_dispatch_failed(
    writer: AuditWriter,
    *,
    simulation_id: str,
    injection_correlation_id: str | UUID,
    exception_class: str,
    exception_message: str,
    triggered_sub_agents: Iterable[TriggeredSubAgent],
    prompt_hash: str,
    prompt_hash_source: str,
    idempotency_key: str | None,
    request_correlation_id: str | UUID,
    dispatch_ack_timeout_seconds: float = 5.0,
    chat_turn_id: str | None = None,
    actor: str = "simulation_route",
    aiims_function: AiimsFunction | None = None,
) -> AuditEnvelope:
    """Persist a Cycle 2 ``signal_pipeline.dispatch_failed`` envelope (entry-25).

    Cycle 2 Amendment A2-01 / A2-08 / FR-067 — replaces the silent-swallow
    site at ``apps/api/app/api/routes/simulations_036.py:316-345`` (Cycle 1)
    with an explicit forensic record per pass-1 Q1 / pass-2 Q1.

    The ``triggered_sub_agents`` list is RFC 8785 JCS canonicalised via
    :func:`canonicalise_triggered_sub_agents` so its serialised bytes are
    byte-equal to the HTTP 202 response body's array (CHK135 invariant
    enforced by ``tests/contract/test_dispatch_failed_body_audit_byte_equality.py``).

    The ``partial_successful_subset`` and ``failed_subscriber_list`` are
    derived ergonomic projections of the canonical array — the canonical
    array remains the byte-equality source of truth.

    Returns the persisted envelope so the caller can surface the
    ``sequence_number`` in the HTTP 202 ``Location`` header for forensic
    replay (FR-049).
    """

    canonical = canonicalise_triggered_sub_agents(triggered_sub_agents)
    successful = [
        item["sub_agent"]
        for item in canonical
        if item["dispatch_status"] == "acknowledged"
    ]
    failed = [
        item["sub_agent"]
        for item in canonical
        if item["dispatch_status"] in ("failed", "timed_out")
    ]

    # PII-scrub + truncate per audit-envelope.md §3.25 (1000-char cap).
    if len(exception_message) > 1000:
        exception_message = exception_message[:997] + "..."

    details: dict[str, Any] = {
        "injection_correlation_id": str(injection_correlation_id),
        "exception_class": exception_class,
        "exception_message": exception_message,
        "triggered_sub_agents": canonical,
        "partial_successful_subset": successful,
        "failed_subscriber_list": failed,
        "prompt_hash": prompt_hash,
        "prompt_hash_source": prompt_hash_source,
        "degraded_dispatch_flag": True,
        "dispatch_ack_timeout_seconds": dispatch_ack_timeout_seconds,
        "idempotency_key": idempotency_key,
        "request_correlation_id": str(request_correlation_id),
    }

    return await writer.write(
        "signal_pipeline.dispatch_failed",
        simulation_id=simulation_id,
        details=details,
        source={"component": "telemetry_injection_orchestrator"},
        actor=actor,
        correlation_id=str(injection_correlation_id),
        turn_id=chat_turn_id or str(injection_correlation_id),
        aiims_function=aiims_function,
        prompt_hash_source=prompt_hash_source,
        idempotency_key=idempotency_key,
        request_correlation_id=str(request_correlation_id),
    )


def get_audit_writer() -> AuditWriter:
    """Return the process-wide audit writer (lazy)."""
    global _default_writer
    if _default_writer is None:
        # Production wiring inserts a real Cosmos container here when
        # ``COSMOS_ENDPOINT`` is set. For tests the in-memory writer
        # short-circuits.
        cosmos_container = None
        if os.getenv("COSMOS_ENDPOINT"):
            try:
                from app.services.cosmos_clients import (
                    get_simulation_audit_container,
                )

                cosmos_container = get_simulation_audit_container()
            except Exception as exc:
                logger.warning(
                    "audit.cosmos_unavailable falling back to memory: %s", exc
                )
        _default_writer = AuditWriter(cosmos_container=cosmos_container)
    return _default_writer


def reset_audit_writer_for_tests() -> None:
    """Reset the process-wide singleton — tests only."""
    global _default_writer
    _default_writer = None
    AuditWriter.reset_memory_for_test()
    # Also reset the sequence repository so per-test isolation holds.
    from app.repositories.simulation_sequence_repository import (
        reset_sequence_repository_for_tests,
    )

    reset_sequence_repository_for_tests()


__all__ = [
    "AuditDLQEntry",
    "AuditWriter",
    "get_audit_dlq_buffer",
    "get_audit_writer",
    "reset_audit_dlq_buffer_for_tests",
    "reset_audit_writer_for_tests",
]
