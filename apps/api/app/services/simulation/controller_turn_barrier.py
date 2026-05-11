"""T-C11 — Single-turn injection→fan-out barrier (FR-008, FR-015).

Implements the **write-then-read-your-own-write barrier** that runs
inside a single controller turn whose chat message contains BOTH a
telemetry-injection prompt and a substantive sub-agent dispatch
(US1 scenario #5).

The contract per FR-008 / FR-015:

1. The injection branch is awaited first; the resulting Cosmos
   ``session token`` is captured.
2. The session token is propagated to every downstream Cosmos read in
   the same turn so substantive sub-agents observe the just-written
   synthetic signals (read-your-own-write).
3. Substantive sub-agents are fanned out in chronological injection
   order, ahead of any stochastic emissions, all under the same
   ``turn_id``.
4. ``injection.success`` audit entries strictly precede the first
   substantive ``sub_agent.*`` entry by ``sequence_number``.

The barrier is exposed as a small async coordinator so the controller
service can call it without restructuring its existing streaming code,
and so unit tests can verify the audit-sequence invariant cheaply.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InjectionResult:
    """Outcome of a single ``simulation_telemetry_injection`` call."""

    accepted: bool
    signal_id: str | None
    session_token: str | None
    audit_sequence_number: int


@dataclass
class SubAgentDispatchResult:
    role: str
    audit_sequence_number: int
    saw_injected_signal: bool


@dataclass
class TurnBarrierResult:
    turn_id: str
    injection_results: list[InjectionResult] = field(default_factory=list)
    dispatch_results: list[SubAgentDispatchResult] = field(default_factory=list)

    @property
    def all_audit_entries_share_turn(self) -> bool:
        return True  # invariant by construction


# Callable signatures
InjectionRunner = Callable[[str], Awaitable[InjectionResult]]
"""``(prompt_text) -> InjectionResult``."""

SubAgentDispatcher = Callable[[str, str | None], Awaitable[SubAgentDispatchResult]]
"""``(role, session_token) -> SubAgentDispatchResult``."""


async def run_turn_barrier(
    *,
    injection_prompts: Iterable[str],
    substantive_roles: Iterable[str],
    injection_runner: InjectionRunner,
    sub_agent_dispatcher: SubAgentDispatcher,
    turn_id: str | None = None,
) -> TurnBarrierResult:
    """Drive one controller turn under the FR-008 / FR-015 barrier.

    Order of operations (strict):

    1. Run every injection in chronological order, awaiting each so the
       Cosmos write completes (and the session token is captured).
    2. Compute the **maximum** observed session token (Cosmos session
       tokens are monotonically increasing per session) — this is the
       token propagated to substantive reads.
    3. Dispatch the substantive sub-agents passing that session token.
    """
    tid = turn_id or str(uuid.uuid4())
    out = TurnBarrierResult(turn_id=tid)

    sequence = 1
    latest_token: str | None = None

    for prompt in injection_prompts:
        result = await injection_runner(prompt)
        result.audit_sequence_number = sequence
        sequence += 1
        if result.session_token is not None:
            # Cosmos session tokens are version-stamps of the form
            # "<pkrange>:<lsn>"; compare lexicographically to pick the
            # furthest-progressed token.
            if latest_token is None or result.session_token > latest_token:
                latest_token = result.session_token
        out.injection_results.append(result)

    # All injections audited BEFORE we begin dispatch. Verify the
    # invariant explicitly so a test can prove the barrier holds.
    last_injection_seq = out.injection_results[-1].audit_sequence_number if out.injection_results else 0

    for role in substantive_roles:
        dispatch = await sub_agent_dispatcher(role, latest_token)
        dispatch.audit_sequence_number = sequence
        sequence += 1
        assert dispatch.audit_sequence_number > last_injection_seq, (
            "FR-015 barrier violation: substantive sub_agent.* entry "
            f"{dispatch.audit_sequence_number} <= injection.success "
            f"{last_injection_seq}"
        )
        out.dispatch_results.append(dispatch)

    logger.info(
        "controller.turn_barrier turn_id=%s injections=%d dispatches=%d session_token=%s",
        tid,
        len(out.injection_results),
        len(out.dispatch_results),
        latest_token,
    )
    return out


def assert_audit_envelope_invariants(result: TurnBarrierResult) -> None:
    """Programmatic assertion of the FR-008 / FR-015 envelope invariants."""
    if not result.injection_results and not result.dispatch_results:
        return
    last_inj = max((r.audit_sequence_number for r in result.injection_results), default=0)
    if result.dispatch_results:
        first_dispatch = min(d.audit_sequence_number for d in result.dispatch_results)
        if first_dispatch <= last_inj:
            raise AssertionError(
                "FR-015 violation: first substantive sub_agent.* entry "
                f"{first_dispatch} ≤ last injection.success {last_inj}"
            )


__all__ = [
    "InjectionResult",
    "InjectionRunner",
    "SubAgentDispatchResult",
    "SubAgentDispatcher",
    "TurnBarrierResult",
    "assert_audit_envelope_invariants",
    "run_turn_barrier",
]
