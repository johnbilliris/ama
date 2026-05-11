"""T-B09: audit_writer gap-free sequence unit tests (FR-048)."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    reset_audit_writer_for_tests()


@pytest.mark.asyncio
async def test_sequence_numbers_are_gap_free() -> None:
    writer = AuditWriter()
    sim = str(uuid4())
    for _ in range(5):
        await writer.write(
            "lifecycle.paused",
            simulation_id=sim,
            details={"attempted_action": "chat_turn"},
        )
    seqs = [e.sequence_number for e in AuditWriter.memory_for_test(sim)]
    assert seqs == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_write_validates_payload() -> None:
    writer = AuditWriter()
    sim = str(uuid4())
    with pytest.raises(Exception):
        # ``injection.success`` requires chat_turn_id, etc.
        await writer.write(
            "injection.success",
            simulation_id=sim,
            details={"foo": "bar"},
        )


@pytest.mark.asyncio
async def test_write_synthetic_delivery_canonical_payload() -> None:
    writer = AuditWriter()
    sim = str(uuid4())
    env = await writer.write(
        "synthetic-delivery",
        simulation_id=sim,
        details={
            "channel": "sms",
            "audience": "operations",
            "message_id": f"sim-msg-{uuid4().hex[:12]}",
            "sim_timestamp": datetime.now(UTC),
            "block_reason": "simulation_tenant_egress_blocked",
            "payload_hash": hashlib.sha256(b"x").hexdigest(),
        },
    )
    assert env.entry_type == "synthetic-delivery"
    assert env.partition_key == sim


@pytest.mark.asyncio
async def test_concurrent_writes_assign_unique_sequence() -> None:
    writer = AuditWriter()
    sim = str(uuid4())

    async def _emit() -> int:
        env = await writer.write(
            "lifecycle.paused",
            simulation_id=sim,
            details={"attempted_action": "chat_turn"},
        )
        return env.sequence_number

    seqs = await asyncio.gather(*[_emit() for _ in range(10)])
    assert sorted(seqs) == list(range(1, 11))
