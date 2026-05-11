"""T-C14 — US1 scenario #5 single-envelope integration test.

Pairs with T-C11. A single chat turn contains both:

* A telemetry-injection prompt → ``injection.success``
* A substantive sub-agent request → ``sub_agent.*``

The acceptance contract:

(a) ONE ``turn_id`` across all audit entries.
(b) ``injection.success`` precedes substantive ``sub_agent.*`` entries
    by ``sequence_number``.
(c) Cosmos session token observed by substantive sub-agents matches the
    write-side token (RYOW).
(d) Substantive sub-agents read the just-written synthetic signals.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.controller_turn_barrier import (
    InjectionResult,
    SubAgentDispatchResult,
    assert_audit_envelope_invariants,
    run_turn_barrier,
)


@pytest.mark.asyncio
async def test_us1_scenario_5_single_audit_envelope() -> None:
    """One turn → one envelope → injection-then-substantive ordering."""
    audit_log: list[dict] = []

    async def inj(prompt: str) -> InjectionResult:
        return InjectionResult(
            accepted=True,
            signal_id=f"sig-{prompt[:8]}",
            session_token="0:1:0:000007",
            audit_sequence_number=0,
        )

    async def dispatch(role: str, session_token: str | None) -> SubAgentDispatchResult:
        return SubAgentDispatchResult(
            role=role,
            audit_sequence_number=0,
            saw_injected_signal=session_token == "0:1:0:000007",
        )

    result = await run_turn_barrier(
        injection_prompts=["smoke plume east of canberra"],
        substantive_roles=["risk-assessment", "communication", "intelligence"],
        injection_runner=inj,
        sub_agent_dispatcher=dispatch,
        turn_id="turn-us1-5",
    )
    audit_log.extend(
        {
            "turn_id": result.turn_id,
            "entry_type": "injection.success",
            "sequence_number": r.audit_sequence_number,
            "signal_id": r.signal_id,
        }
        for r in result.injection_results
    )
    audit_log.extend(
        {
            "turn_id": result.turn_id,
            "entry_type": "sub_agent.dispatched",
            "sequence_number": d.audit_sequence_number,
            "role": d.role,
            "saw_injected_signal": d.saw_injected_signal,
        }
        for d in result.dispatch_results
    )

    # (a) ONE turn_id across all audit entries.
    assert {entry["turn_id"] for entry in audit_log} == {"turn-us1-5"}

    # (b) injection.success precedes substantive sub_agent.* by sequence_number.
    inj_seqs = [e["sequence_number"] for e in audit_log if e["entry_type"] == "injection.success"]
    sub_seqs = [e["sequence_number"] for e in audit_log if e["entry_type"] == "sub_agent.dispatched"]
    assert max(inj_seqs) < min(sub_seqs)

    # (c) + (d) Cosmos session token propagated; substantive sub-agents saw it.
    assert all(e["saw_injected_signal"] for e in audit_log if e["entry_type"] == "sub_agent.dispatched")

    # Programmatic helper agrees.
    assert_audit_envelope_invariants(result)
