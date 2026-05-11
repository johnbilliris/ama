"""Wave D / T-AA21 — audit_writer rejects caller-supplied `sequence_number`.

The gap-free allocator (Cycle 1 / ADR-036-007) is the SOLE source of
truth for ``sequence_number``. Any caller-supplied value in the
``details`` dict MUST be silently dropped (with a warning log) so a
future writer-side refactor cannot collapse the gap-free invariant.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import logging

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)


def test_caller_supplied_sequence_number_is_dropped(caplog) -> None:
    """A caller-supplied `sequence_number` is dropped + warning logged."""

    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)
    caplog.set_level(logging.WARNING, logger="apps.api.app.services.simulation.audit_writer")

    async def _run() -> None:
        await audit.write(
            "injection.refused",
            simulation_id="sim-aa21",
            actor="test",
            details={
                "sequence_number": 99999,  # MUST be ignored
                "chat_turn_id": "turn-1",
                "reason": "malformed_input",
            },
        )

    asyncio.run(_run())

    # Warning emitted.
    assert any("caller_sequence_number_ignored" in rec.message for rec in caplog.records), (
        "audit.caller_sequence_number_ignored warning MUST be emitted"
    )

    # Gap-free allocator-assigned sequence_number is NOT 99999.
    from apps.api.app.services.simulation import audit_writer as _aw

    persisted = _aw._memory_store["sim-aa21"]
    assert persisted, "envelope MUST be persisted"
    assert persisted[0].sequence_number != 99999, "Allocator MUST overwrite caller-supplied sequence_number."


def test_caller_sequence_number_does_not_break_envelope_validation() -> None:
    """The envelope MUST still validate when guard fires."""

    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)

    async def _run() -> None:
        await audit.write(
            "injection.refused",
            simulation_id="sim-aa21-ok",
            actor="test",
            details={
                "sequence_number": "not-a-number",  # garbage caller value
                "chat_turn_id": "turn-2",
                "reason": "malformed_input",
            },
        )

    asyncio.run(_run())  # Should NOT raise.
