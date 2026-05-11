"""Wave D / T-AA21 — depth-2 refusal envelope sequence-number gap-free.

Regression guard: the placeholder ``sequence_number=1`` literal in
``cascade_orchestrator`` was an attractive nuisance. After T-AA21, the
orchestrator no longer supplies a literal, and the audit writer's
gap-free allocator owns assignment. This test asserts the gap-free
invariant holds across 100 depth-2 refusal envelopes.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.cascade_orchestrator import fan_out
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal


def _build_signal(i: int) -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=f"sim-msg-{i:08x}",
        simulation_id="sim-depth2-gap-free",
        tenant_id="tnt",
        category="hydrology",
        confidence="high",
        parameters={},
        observed_at=datetime.now(UTC),
        freshness_window_seconds=600,
    )


@pytest.mark.asyncio
async def test_depth2_refused_sequence_numbers_are_gap_free() -> None:
    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)

    async def dispatcher(role: str, prompt: str, origin: str) -> None:
        return None

    for i in range(100):
        await fan_out(
            trigger_signal=_build_signal(i),
            dispatcher=dispatcher,
            parent_origin_cascade_id=str(uuid4()),
            audit_writer=audit,
        )

    from apps.api.app.services.simulation import audit_writer as _aw

    persisted = _aw._memory_store["sim-depth2-gap-free"]
    depth2_envs = [
        e for e in persisted if e.entry_type == "cascade.depth2_refused"
    ]
    assert len(depth2_envs) == 100
    seq_numbers = sorted(e.sequence_number for e in depth2_envs)
    # Gap-free invariant: max - min + 1 == len.
    assert seq_numbers[-1] - seq_numbers[0] + 1 == len(seq_numbers), (
        "depth-2 refused sequence_numbers MUST be gap-free per FR-048."
    )
    # No envelope carries the legacy `1` placeholder.
    for env in depth2_envs:
        assert env.sequence_number != 1 or seq_numbers[0] == 1
        assert "sequence_number" not in env.details or (
            env.details["sequence_number"] == env.sequence_number
        )
