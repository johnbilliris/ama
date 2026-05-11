"""Wave B / T-AA15 — dispatch_failed idempotency replay test.

Asserts that re-invoking the dispatch path with the same idempotency-key
+ injection_correlation_id reproduces a byte-equal canonical form on the
audit envelope (CHK135 stable across replays). The actual idempotency
key persistence is owned by the route handler / Cosmos repo; this test
focuses on the canonicaliser determinism (the building block CHK135
enforces).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    canonicalise_triggered_sub_agents,
    reset_audit_writer_for_tests,
    write_dispatch_failed,
)
from apps.api.app.services.simulation.dispatch_status import TriggeredSubAgent


def test_replay_produces_byte_equal_envelope_details() -> None:
    """Same inputs across two replays → byte-equal canonical arrays."""

    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)
    entries = [
        TriggeredSubAgent(
            sub_agent="Operations",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000031"),
            dispatch_status="failed",
        ),
        TriggeredSubAgent(
            sub_agent="Intel",
            trigger_source="cascade",
            correlation_id=UUID("00000000-0000-0000-0000-000000000032"),
            dispatch_status="timed_out",
        ),
    ]
    args = dict(
        simulation_id="sim-replay",
        injection_correlation_id="00000000-0000-0000-0000-000000000041",
        exception_class="DispatchError",
        exception_message="dispatch failed",
        triggered_sub_agents=entries,
        prompt_hash="e" * 64,
        prompt_hash_source="raw_user_input",
        idempotency_key="idem-1",
        request_correlation_id="00000000-0000-0000-0000-000000000042",
    )
    first = asyncio.run(write_dispatch_failed(audit, **args))
    second = asyncio.run(write_dispatch_failed(audit, **args))
    a = json.dumps(first.details["triggered_sub_agents"], sort_keys=True)
    b = json.dumps(second.details["triggered_sub_agents"], sort_keys=True)
    assert a == b


def test_replay_preserves_fixed_field_set() -> None:
    """Canonical entries always carry the SAME field set (CHK135)."""

    entries = [
        TriggeredSubAgent(
            sub_agent="Health",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000050"),
            dispatch_status="acknowledged",
        ),
    ]
    canonical = canonicalise_triggered_sub_agents(entries)
    assert set(canonical[0].keys()) == {
        "correlation_id",
        "dispatch_status",
        "sub_agent",
        "trigger_source",
    }
