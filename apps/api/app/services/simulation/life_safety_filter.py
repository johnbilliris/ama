"""Post-parse life-safety filter (T-AA03 / I1 / FR-010 strengthen).

Wave 4 amendment — the original ``life_safety_gate.py`` runs a regex
blocklist against the **raw** prompt before the structured parse. That
yields false positives whenever an unrelated mention of (for example)
"evacuation" appears in narrative context — e.g. "we drilled an
evacuation last month" gets refused.

This module shifts the low-confidence life-safety check **post-parse**
so it operates on structured attributes (category, action_verbs,
confidence, target_audience). The deterministic blocklist in
``life_safety_gate.py`` still runs first as a hard refusal for
unambiguous real-world action requests; this filter handles the
borderline cases that previously caused noise.

Decision matrix (post-parse):

* category ∈ life-safety set AND confidence == "low" → REFUSE
  (matches the FR-010 "life-safety low-confidence" clause).
* category ∈ life-safety set AND target_audience == "public" AND
  any action_verb ∈ DANGEROUS_VERBS → REFUSE.
* otherwise → ACCEPT (caller may still log low-confidence on the
  signal envelope — that's accepted behaviour for non-life-safety).

The output mirrors :class:`life_safety_gate.GateDecision` for caller
parity so the audit envelope ``injection.refused.reason`` enum is
shared.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


#: Categories whose synthetic signals can directly impact life-safety
#: decisions if the parser is wrong. Matches FR-010 + Q4 risk taxonomy.
LIFE_SAFETY_CATEGORIES: frozenset[str] = frozenset(
    {
        "evacuation",
        "comms-channel-state",
        "fire-behaviour",
        "geohazard",
    }
)


#: Action verbs that, when paired with ``target_audience == "public"``
#: under a life-safety category, indicate the parser surfaced something
#: requiring HITL review even at MEDIUM confidence.
DANGEROUS_VERBS: frozenset[str] = frozenset(
    {
        "evacuate",
        "broadcast",
        "warn",
        "shelter",
        "lockdown",
        "shutdown",
        "issue-warning",
        "all-clear",
    }
)


@dataclass(frozen=True)
class FilterDecision:
    """Outcome of the post-parse life-safety filter."""

    refused: bool
    reason: str | None = None  # injection.refused.reason
    matched_attribute: str | None = None


def evaluate_post_parse(
    *,
    parsed_category: str | None,
    inferred_confidence: str | None,
    action_verbs: list[str] | None = None,
    target_audience: str | None = None,
) -> FilterDecision:
    """Return refusal decision based on STRUCTURED parser output.

    Per T-AA03 this replaces the pre-parse text regex for borderline
    cases. The deterministic ``life_safety_gate.LIFE_SAFETY_BLOCKLIST``
    still runs first for unambiguous real-world action requests.
    """

    if not parsed_category or parsed_category not in LIFE_SAFETY_CATEGORIES:
        return FilterDecision(refused=False)

    confidence = (inferred_confidence or "").lower()
    if confidence == "low":
        return FilterDecision(
            refused=True,
            reason="life_safety_low_confidence",
            matched_attribute=f"category={parsed_category}",
        )

    audience = (target_audience or "").lower()
    if audience == "public":
        verbs = {(v or "").lower() for v in (action_verbs or [])}
        overlap = verbs & DANGEROUS_VERBS
        if overlap:
            return FilterDecision(
                refused=True,
                reason="life_safety_low_confidence",
                matched_attribute=f"public_action={sorted(overlap)[0]}",
            )

    return FilterDecision(refused=False)


__all__ = [
    "DANGEROUS_VERBS",
    "FilterDecision",
    "LIFE_SAFETY_CATEGORIES",
    "evaluate_post_parse",
]
