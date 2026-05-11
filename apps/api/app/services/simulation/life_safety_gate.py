"""Hybrid life-safety gate (T-C07 / FR-010).

Combines:

1. A deterministic regex blocklist that always refuses the prompt (e.g.
   "issue an evacuation order", "broadcast all-clear").
2. An optional LLM judge invocation for borderline phrasings — caller
   supplies the judge as an injected callable so this module remains
   hermetic.

**Non-life-safety low-confidence acceptance.** The gate must NOT refuse a
non-life-safety prompt simply because the parser's confidence is low — that
case is accepted by the controller and recorded with ``confidence: "low"``
on the synthetic-signal envelope. Only life-safety prompts trigger refusal.

Returns a :class:`GateDecision` enum with the reason code that gets
mirrored onto the ``injection.refused`` audit entry.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# 30 fixture life-safety phrases — covering evacuation orders, broadcasts,
# medical dispatches, and all-clears across AU jurisdictions.
LIFE_SAFETY_BLOCKLIST: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bissue\s+(an?\s+)?evacuation\s+order\b",
        r"\border\s+(?:the\s+)?evacuation\b",
        r"\bsend\s+(?:a\s+)?real\s+evacuation\b",
        r"\bdeclare\s+all[-\s]?clear\b",
        r"\bissue\s+all[-\s]?clear\b",
        r"\bbroadcast\s+(?:a\s+)?(?:real|live|actual)\b",
        r"\bcall\s+(?:000|triple\s+zero|999|911)\b",
        r"\bdispatch\s+(?:real|actual)\s+(?:police|ambulance|fire)\b",
        r"\bcontact\s+(?:emergency\s+services|police|ambulance)\s+(?:for\s+real|live)\b",
        r"\b(?:trigger|activate)\s+(?:real|live)\s+sirens?\b",
        r"\bsend\s+(?:real|actual)\s+(?:sms|email|broadcast)\b",
        r"\bpublish\s+(?:to|on)\s+(?:abc|seven|nine|ten)\s+for\s+real\b",
        r"\bfire\s+(?:real|live)\s+ammunition\b",
        r"\b(?:hostile|active)\s+shooter\s+protocol\b",
        r"\bmass\s+casualty\s+(?:plan|alert)\s+(?:trigger|activate)\b",
        r"\bdeclare\s+a\s+(?:state|public)\s+emergency\b",
        r"\bcontact\s+(?:nsw|vic|qld|wa|sa|tas|nt|act)\s+(?:rfs|cfa|qfes|fes)\s+for\s+real\b",
        r"\bevacuate\s+(?:hospital|aged\s+care|prison)\b",
        r"\bissue\s+(?:tsunami|cyclone|bushfire)\s+warning\s+(?:to\s+the\s+public|live)\b",
        r"\bturn\s+off\s+(?:real\s+)?gas\s+main\b",
        r"\bcut\s+(?:real\s+)?power\s+to\b",
        r"\bopen\s+(?:dam|spillway)\s+for\s+real\b",
        r"\border\s+aviation\s+ground\s+stop\b",
        r"\border\s+rail\s+shutdown\b",
        r"\bstop\s+real\s+traffic\s+on\b",
        r"\bsend\s+(?:a\s+)?real\s+helicopter\b",
        r"\border\s+military\s+(?:deployment|callout)\b",
        r"\bissue\s+a\s+real\s+lockdown\b",
        r"\bask\s+abc\s+to\s+broadcast\s+(?:live|for\s+real)\b",
        r"\bgive\s+the\s+all[-\s]?clear\b",
    )
)


@dataclass(frozen=True)
class GateDecision:
    """Outcome of the life-safety gate."""

    refused: bool
    reason: str | None = None  # injection-refused.reason
    detected_pattern: str | None = None
    judge_score: float | None = None


JudgeCall = Callable[[str], Awaitable[float]]
"""Async callable returning a 0–1 risk score (1 = certain life-safety)."""


JUDGE_THRESHOLD = 0.65
"""LLM judge threshold above which the prompt is refused (FR-010 borderline)."""


async def evaluate(
    prompt: str,
    *,
    parsed_category: str | None = None,
    inferred_confidence: str | None = None,
    judge: JudgeCall | None = None,
) -> GateDecision:
    """Decide whether *prompt* triggers the life-safety hard refusal.

    Non-life-safety prompts pass even when ``inferred_confidence='low'`` —
    they are accepted by the controller and tagged with ``confidence: low``
    on the synthetic-signal envelope.
    """
    text = (prompt or "").strip()
    if not text:
        return GateDecision(refused=False)

    for pat in LIFE_SAFETY_BLOCKLIST:
        if pat.search(text):
            return GateDecision(
                refused=True,
                reason="real_world_action_request",
                detected_pattern=pat.pattern,
            )

    # Optional LLM judge for borderline phrasings.
    if judge is not None:
        try:
            score = await judge(text)
        except Exception:
            logger.exception("life_safety_gate.judge_error")
            return GateDecision(refused=False, judge_score=None)
        if score >= JUDGE_THRESHOLD:
            return GateDecision(
                refused=True,
                reason="life_safety_low_confidence",
                judge_score=score,
            )
        return GateDecision(refused=False, judge_score=score)

    # No judge supplied → accept (the parser's confidence is captured
    # downstream).
    if parsed_category and parsed_category in {"evacuation", "comms-channel-state"}:
        if inferred_confidence == "low":
            # Per FR-010 second clause: non-life-safety LOW-CONFIDENCE is
            # ACCEPTED — but life-safety LOW-CONFIDENCE is REFUSED. The
            # ``evacuation`` category is life-safety adjacent, so
            # low-confidence evacuation prompts MUST be refused. Other
            # categories pass through with ``confidence: low``.
            if parsed_category == "evacuation":
                return GateDecision(refused=True, reason="life_safety_low_confidence")
    return GateDecision(refused=False)
