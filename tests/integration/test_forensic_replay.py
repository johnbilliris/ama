"""Wave B / T-AA15 — forensic-replay test (audit details survive read-back).

Persists a ``signal_pipeline.dispatch_failed`` envelope, reads it back
from the in-memory store, and asserts that every field required for
forensic replay (audit-envelope.md §3.25) is intact.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
    write_dispatch_failed,
)
from apps.api.app.services.simulation.dispatch_status import TriggeredSubAgent

REQUIRED_FIELDS = {
    "injection_correlation_id",
    "exception_class",
    "exception_message",
    "triggered_sub_agents",
    "prompt_hash",
    "prompt_hash_source",
    "idempotency_key",
    "request_correlation_id",
    "dispatch_ack_timeout_seconds",
}


def test_forensic_replay_envelope_round_trips() -> None:
    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)
    sim_id = "sim-forensic"
    args = dict(
        simulation_id=sim_id,
        injection_correlation_id="00000000-0000-0000-0000-000000000061",
        exception_class="DispatchError",
        exception_message="dispatch failed",
        triggered_sub_agents=[
            TriggeredSubAgent(
                sub_agent="Risk",
                trigger_source="primary",
                correlation_id=UUID("00000000-0000-0000-0000-000000000071"),
                dispatch_status="failed",
            )
        ],
        prompt_hash="f" * 64,
        prompt_hash_source="raw_user_input",
        idempotency_key=None,
        request_correlation_id="00000000-0000-0000-0000-000000000062",
    )
    envelope = asyncio.run(write_dispatch_failed(audit, **args))
    assert envelope.entry_type == "signal_pipeline.dispatch_failed"
    assert envelope.simulation_id == sim_id
    # All forensic fields present.
    missing = REQUIRED_FIELDS - set(envelope.details.keys())
    assert not missing, f"Forensic-replay envelope missing fields: {missing}"
    # Sequence number assigned by allocator (gap-free per simulation).
    assert isinstance(envelope.sequence_number, int)
    assert envelope.sequence_number >= 1


def test_forensic_replay_envelope_in_memory_readable() -> None:
    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)
    sim_id = "sim-forensic-2"
    args = dict(
        simulation_id=sim_id,
        injection_correlation_id="00000000-0000-0000-0000-000000000091",
        exception_class="DispatchError",
        exception_message="dispatch failed",
        triggered_sub_agents=[
            TriggeredSubAgent(
                sub_agent="Logistics",
                trigger_source="cascade",
                correlation_id=UUID("00000000-0000-0000-0000-000000000092"),
                dispatch_status="timed_out",
            )
        ],
        prompt_hash="0" * 64,
        prompt_hash_source="raw_user_input",
        idempotency_key=None,
        request_correlation_id="00000000-0000-0000-0000-000000000093",
    )
    envelope = asyncio.run(write_dispatch_failed(audit, **args))

    # Simulate a forensic operator re-reading the envelope from the store.
    from apps.api.app.services.simulation import audit_writer as _aw

    persisted = _aw._memory_store[sim_id]
    assert any(
        e.entry_type == "signal_pipeline.dispatch_failed"
        and e.details["injection_correlation_id"] == envelope.details["injection_correlation_id"]
        for e in persisted
    )
