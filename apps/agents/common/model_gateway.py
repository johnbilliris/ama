"""Data-minimisation model gateway (Spec 036, FR-RAG-CV-03 / FR-RAG-CV-04).

Invoked **before** any non-AU Foundry call (deployment region read from the
carve-out registry). Responsibilities:

1. **PII redaction**: Presidio analyser pipeline (PHONE, EMAIL, NAME, …) →
   anonymizer. AU-mobile, email, person-name, and credit-card patterns covered.
2. **PSPF marking detection**: ``OFFICIAL: SENSITIVE``, ``PROTECTED``, ``SECRET``,
   ``TOP SECRET`` → DENY. (``OFFICIAL`` alone is allowed; carved-out paths above
   OFFICIAL go through FR-RAG-NS-07 opt-out.)
3. **Sensitive-operational classifier**: allow-list of safe topics; explicit
   tactical / hostage-rescue / breach-plan / CHIS-handle keywords default-deny.

Decision telemetry: every call emits an ``audit.gateway_decision`` field —
``allow`` / ``deny`` / ``redact``. Deny carries a structured ``reason``.

For AU East / Southeast deployments the gateway is **bypassed at the
boundary** (data residency holds; redaction would only mask the audit trail);
the call is still audited transparently.

Spec ref: spec.md FR-RAG-CV-03; data-model.md §AuditRecord (gateway_decision,
gateway_deny_reason).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Module constants — region partitioning (FR-RAG-CV-04).
# --------------------------------------------------------------------------- #

AU_REGIONS: frozenset[str] = frozenset({"australiaeast", "australiasoutheast"})

# --------------------------------------------------------------------------- #
# PSPF-marking detection (FR-RAG-CV-03).
# Order matters: longest-prefix-first so ``OFFICIAL: SENSITIVE`` wins over ``OFFICIAL``.
# --------------------------------------------------------------------------- #

_PSPF_DENY_MARKINGS: tuple[str, ...] = (
    "TOP SECRET",
    "SECRET",
    "PROTECTED",
    "OFFICIAL: SENSITIVE",
    "OFFICIAL:SENSITIVE",
)

# --------------------------------------------------------------------------- #
# Sensitive-operational keyword default-deny list. The agent must use the
# RAG-OPTOUT path (FR-RAG-NS-07) to carry above-OFFICIAL operational content.
# --------------------------------------------------------------------------- #

_SENSITIVE_OPERATIONAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bbreach\s+point\b", re.IGNORECASE),
    re.compile(r"\bhostage\s+rescue\b", re.IGNORECASE),
    re.compile(r"\btactical\s+entry\b", re.IGNORECASE),
    re.compile(r"\bchis\s+(handle|identity)\b", re.IGNORECASE),
    re.compile(r"\bcovert\s+source\b", re.IGNORECASE),
    re.compile(r"\bweapons?\s+cache\b", re.IGNORECASE),
)

# --------------------------------------------------------------------------- #
# Lightweight PII patterns. Used as primary path when presidio is unavailable;
# Presidio's analyser is strictly stronger but heavier.
# --------------------------------------------------------------------------- #

_PII_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b04\d{2}\s?\d{3}\s?\d{3}\b"), "<PHONE>"),
    (re.compile(r"\b0[2378]\s?\d{4}\s?\d{4}\b"), "<PHONE>"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b"), "<CREDIT_CARD>"),
)


# --------------------------------------------------------------------------- #
# Decision result.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GatewayDecision:
    """Outcome of the data-minimisation gateway.

    - ``gateway_decision`` is the audit-record discriminator
      (``allow`` / ``deny`` / ``redact``).
    - ``transmitted_text`` is the (possibly redacted) text safe to forward.
    - ``reason`` is non-empty iff ``gateway_decision == "deny"``.
    """

    gateway_decision: Literal["allow", "deny", "redact"]
    transmitted_text: str
    reason: str = ""
    redactions_applied: int = 0


# --------------------------------------------------------------------------- #
# Pipeline.
# --------------------------------------------------------------------------- #


def _detect_pspf_marking(text: str) -> str | None:
    upper = text.upper()
    for marking in _PSPF_DENY_MARKINGS:
        if marking in upper:
            return marking
    return None


def _detect_sensitive_operational(text: str) -> str | None:
    for pat in _SENSITIVE_OPERATIONAL_PATTERNS:
        if pat.search(text):
            return pat.pattern
    return None


def _redact_pii_with_regex(text: str) -> tuple[str, int]:
    redacted = text
    count = 0
    for pat, repl in _PII_PATTERNS:
        new_text, n = pat.subn(repl, redacted)
        redacted = new_text
        count += n
    return redacted, count


def _redact_pii_with_presidio(text: str) -> tuple[str, int] | None:
    """Use Presidio analyser+anonymizer when available. Returns None if presidio
    is not installed (regex fallback is used instead).

    Presidio emits its own entity tag conventions (``<PHONE_NUMBER>``,
    ``<EMAIL_ADDRESS>``, …). We post-normalise those to the canonical short
    forms (``<PHONE>``, ``<EMAIL>``) the audit schema and tests assert on.
    """
    try:
        from presidio_analyzer import AnalyzerEngine  # noqa: PLC0415
        from presidio_anonymizer import AnonymizerEngine  # noqa: PLC0415
    except ImportError:
        return None
    try:
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()
        results = analyzer.analyze(text=text, language="en")
        if not results:
            return text, 0
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        normalised = _normalise_presidio_tags(anonymized.text)
        return normalised, len(results)
    except Exception:  # noqa: BLE001 — presidio occasionally raises on malformed input
        logger.warning("Presidio analyser failed; falling back to regex", exc_info=True)
        return None


_PRESIDIO_TAG_MAP: tuple[tuple[str, str], ...] = (
    ("<PHONE_NUMBER>", "<PHONE>"),
    ("<EMAIL_ADDRESS>", "<EMAIL>"),
    ("<CREDIT_CARD>", "<CREDIT_CARD>"),
    ("<PERSON>", "<PERSON>"),
    ("<LOCATION>", "<LOCATION>"),
    ("<DATE_TIME>", "<DATE>"),
    ("<IBAN_CODE>", "<IBAN>"),
    ("<IP_ADDRESS>", "<IP>"),
)


def _normalise_presidio_tags(text: str) -> str:
    """Rewrite Presidio's verbose entity tags to the canonical short forms."""
    out = text
    for src, dst in _PRESIDIO_TAG_MAP:
        if src in out and src != dst:
            out = out.replace(src, dst)
    return out


def apply(*, text: str, deployment_region: str) -> GatewayDecision:
    """Run the data-minimisation gateway on ``text`` for a deployment in ``deployment_region``.

    AU regions (``australiaeast`` / ``australiasoutheast``) bypass redaction
    (data residency holds) but are still audited as ``allow``.

    Non-AU regions:
      1. PSPF-marking detection → DENY if above ``OFFICIAL``.
      2. Sensitive-operational classifier → DENY if a default-deny phrase fires.
      3. PII redaction (Presidio, falling back to regex) → REDACT if any PII
         removed; ALLOW with original text otherwise.
    """
    region = (deployment_region or "").lower()

    # AU bypass — pre-empts every other check.
    if region in AU_REGIONS:
        return GatewayDecision(gateway_decision="allow", transmitted_text=text)

    # 1. PSPF-marking detection.
    marking = _detect_pspf_marking(text)
    if marking is not None:
        return GatewayDecision(
            gateway_decision="deny",
            transmitted_text="",
            reason=f"PSPF marking detected: {marking}",
        )

    # 2. Sensitive-operational classifier.
    sensitive = _detect_sensitive_operational(text)
    if sensitive is not None:
        return GatewayDecision(
            gateway_decision="deny",
            transmitted_text="",
            reason=f"Sensitive operational content matched pattern {sensitive!r}",
        )

    # 3. PII redaction (Presidio first, regex fallback).
    presidio_result = _redact_pii_with_presidio(text)
    if presidio_result is not None:
        redacted_text, count = presidio_result
    else:
        redacted_text, count = _redact_pii_with_regex(text)

    if count > 0:
        return GatewayDecision(
            gateway_decision="redact",
            transmitted_text=redacted_text,
            redactions_applied=count,
        )
    return GatewayDecision(gateway_decision="allow", transmitted_text=text)


__all__ = ["AU_REGIONS", "GatewayDecision", "apply"]
