"""T-C11 — single-turn injection→fan-out barrier integration test.

Verifies the FR-008 / FR-015 contract end-to-end without depending on
live Cosmos: an in-memory injection runner stamps a monotonically
increasing session token; a sub-agent dispatcher records whether it
saw the just-written signal under that token.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.controller_turn_barrier import (
    InjectionResult,
    SubAgentDispatchResult,
    assert_audit_envelope_invariants,
    run_turn_barrier,
)


def _make_injection_runner(token_prefix: str = "0:0:0:") -> tuple[list[str], callable]:
    """Build a runner + a list capturing the prompts seen."""

    seen_prompts: list[str] = []
    counter = {"i": 0}

    async def runner(prompt: str) -> InjectionResult:
        seen_prompts.append(prompt)
        counter["i"] += 1
        return InjectionResult(
            accepted=True,
            signal_id=f"sig-{counter['i']}",
            session_token=f"{token_prefix}{counter['i']:06d}",
            audit_sequence_number=0,  # populated by barrier
        )

    return seen_prompts, runner


def _make_dispatcher() -> tuple[list[tuple[str, str | None]], callable]:
    seen: list[tuple[str, str | None]] = []

    async def dispatch(role: str, session_token: str | None) -> SubAgentDispatchResult:
        seen.append((role, session_token))
        return SubAgentDispatchResult(
            role=role,
            audit_sequence_number=0,  # populated by barrier
            saw_injected_signal=session_token is not None,
        )

    return seen, dispatch


@pytest.mark.asyncio
async def test_single_turn_orders_injections_before_dispatch() -> None:
    seen_prompts, inj_runner = _make_injection_runner()
    seen_dispatch, dispatcher = _make_dispatcher()

    result = await run_turn_barrier(
        injection_prompts=["smoke at canberra", "wind 80 km/h"],
        substantive_roles=["risk-assessment", "communication"],
        injection_runner=inj_runner,
        sub_agent_dispatcher=dispatcher,
        turn_id="turn-c11-1",
    )

    # 2 injection entries, 2 dispatch entries.
    assert len(result.injection_results) == 2
    assert len(result.dispatch_results) == 2
    # Injections were processed in chronological order.
    assert seen_prompts == ["smoke at canberra", "wind 80 km/h"]
    # Audit sequence numbers strictly increasing, injection-first.
    seqs_inj = [r.audit_sequence_number for r in result.injection_results]
    seqs_dispatch = [d.audit_sequence_number for d in result.dispatch_results]
    assert seqs_inj == [1, 2]
    assert seqs_dispatch == [3, 4]
    assert max(seqs_inj) < min(seqs_dispatch)


@pytest.mark.asyncio
async def test_session_token_propagated_to_dispatchers() -> None:
    _, inj_runner = _make_injection_runner(token_prefix="0:0:0:")
    seen_dispatch, dispatcher = _make_dispatcher()

    await run_turn_barrier(
        injection_prompts=["a", "b", "c"],
        substantive_roles=["risk-assessment"],
        injection_runner=inj_runner,
        sub_agent_dispatcher=dispatcher,
    )

    # The dispatcher must have observed the LATEST session token (the
    # write-then-read-your-own-write barrier).
    assert seen_dispatch == [("risk-assessment", "0:0:0:000003")]


@pytest.mark.asyncio
async def test_assert_envelope_invariants_helper_catches_violation() -> None:
    """The helper MUST raise on a hand-crafted ordering violation."""
    from apps.api.app.services.simulation.controller_turn_barrier import (
        TurnBarrierResult,
    )

    bad = TurnBarrierResult(
        turn_id="turn-bad",
        injection_results=[
            InjectionResult(
                accepted=True,
                signal_id="sig-1",
                session_token="t-1",
                audit_sequence_number=5,
            )
        ],
        dispatch_results=[
            SubAgentDispatchResult(
                role="risk-assessment",
                audit_sequence_number=3,
                saw_injected_signal=True,
            )
        ],
    )
    with pytest.raises(AssertionError, match="FR-015 violation"):
        assert_audit_envelope_invariants(bad)


@pytest.mark.asyncio
async def test_no_injection_no_dispatch_passes_invariants() -> None:
    """Empty turn — barrier is a no-op."""
    _, inj_runner = _make_injection_runner()
    _, dispatcher = _make_dispatcher()

    result = await run_turn_barrier(
        injection_prompts=[],
        substantive_roles=[],
        injection_runner=inj_runner,
        sub_agent_dispatcher=dispatcher,
    )
    assert result.injection_results == []
    assert result.dispatch_results == []
    assert_audit_envelope_invariants(result)
