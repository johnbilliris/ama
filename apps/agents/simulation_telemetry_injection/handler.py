"""Telemetry-Injection Agent handler (T-C09 orchestrator).

Wires together the Phase-C components into a single async ``handle`` entry
point that the controller's ``inject_telemetry`` tool invokes. Pipeline:

1. PII scrub the operator prompt (FR-031).
2. Run the life-safety gate (FR-010). If refused, return early with the
   ``injection.refused`` reason.
3. Ask the parse-attempt circuit breaker whether to take the LLM path or
   the regex fallback path (FR-009 layer-2).
4. LLM strict-json_schema parse (or fallback regex extract).
5. Run the contradiction detector (FR-013) and tag the candidate signal.
6. Return the :class:`InjectionOutcome` to the caller.

The handler does **not** persist the signal or write audit envelopes —
that is the controller's responsibility (single audit envelope per turn,
FR-008 / FR-015).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

from . import contradiction_detector, fallback_extractor
from .llm_client import LLMCall, ParseFailure, parse_to_signal
from .pii_scrubber import scrub

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InjectionOutcome:
    """Result of a single telemetry-injection invocation."""

    accepted: bool
    signal: SyntheticSignal | None = None
    refusal_reason: str | None = None
    contradicts: list[str] | None = None
    redactions: dict[str, int] | None = None
    extraction_path: str = "llm"  # llm | fallback_regex
    clarification_question: str | None = None


CircuitProbe = Callable[[str, str | None], Awaitable[str]]
"""``(user_id, simulation_id) -> Awaitable[str]`` returning the breaker state."""


async def handle(
    *,
    prompt: str,
    user_id: str,
    simulation_id: str,
    tenant_id: str,
    llm_call: LLMCall | None,
    system_prompt: str,
    circuit_probe: CircuitProbe | None = None,
    life_safety_evaluator: Callable[..., Awaitable[Any]] | None = None,
    recent_signals: Iterable[SyntheticSignal] = (),
) -> InjectionOutcome:
    """Run the telemetry-injection pipeline for a single coordinator prompt."""
    scrubbed = scrub(prompt)
    if scrubbed.total_redactions > 0:
        logger.info(
            "telemetry_injection.pii_scrubbed user=%s redactions=%s",
            user_id,
            scrubbed.redactions,
        )

    # 1. Life-safety gate — short-circuit on refusal.
    if life_safety_evaluator is not None:
        gate_decision = await life_safety_evaluator(prompt=scrubbed.text)
        if getattr(gate_decision, "refused", False):
            return InjectionOutcome(
                accepted=False,
                refusal_reason=getattr(gate_decision, "reason", "life_safety_low_confidence"),
                redactions=scrubbed.redactions,
            )

    # 2. Circuit-breaker probe.
    breaker_state = "closed"
    if circuit_probe is not None:
        breaker_state = await circuit_probe(user_id, simulation_id)

    use_fallback = breaker_state == "open" or llm_call is None

    candidate: SyntheticSignal | None = None
    extraction_path = "llm"
    if not use_fallback and llm_call is not None:
        try:
            candidate = await parse_to_signal(
                llm_call=llm_call,
                system_prompt=system_prompt,
                user_prompt=scrubbed.text,
            )
        except ParseFailure as exc:
            logger.warning(
                "telemetry_injection.llm_parse_failed user=%s err=%s", user_id, exc
            )
            use_fallback = True

    if candidate is None:
        candidate = fallback_extractor.extract(
            prompt=scrubbed.text,
            simulation_id=simulation_id,
            tenant_id=tenant_id,
        )
        extraction_path = "fallback_regex"

    if candidate is None:
        return InjectionOutcome(
            accepted=False,
            refusal_reason="malformed_input",
            redactions=scrubbed.redactions,
            extraction_path=extraction_path,
            clarification_question=(
                "Could you specify the hazard type, the affected area, and an "
                "approximate severity? (e.g. 'temperature 41C in Penrith 14:00')"
            ),
        )

    # Force the candidate's simulation_id / tenant_id to the caller's so the
    # LLM can't write across tenants.
    candidate = candidate.model_copy(update={
        "simulation_id": simulation_id,
        "tenant_id": tenant_id,
        "signal_id": candidate.signal_id or str(uuid4()),
    })

    # 3. Contradiction detection.
    contradicts = contradiction_detector.detect(
        candidate=candidate, recent_signals=recent_signals
    )

    return InjectionOutcome(
        accepted=True,
        signal=candidate,
        contradicts=contradicts or None,
        redactions=scrubbed.redactions,
        extraction_path=extraction_path,
    )
