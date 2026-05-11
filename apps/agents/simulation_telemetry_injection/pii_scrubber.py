"""Pre-LLM PII scrubber (T-C04 / FR-031)."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?61[\s-]?)?(?:0|\(0\))?\d{1,2}[\s-]?\d{3,4}[\s-]?\d{3,4}(?!\d)")
AHPRA_RE = re.compile(r"\b[A-Z]{3}\s?\d{10}\b")
MEDICARE_RE = re.compile(r"\b\d{4}\s?\d{5}\s?\d\s?\d?\b")
TFN_RE = re.compile(r"\b\d{3}\s?\d{3}\s?\d{3}\b")


@dataclass(frozen=True)
class ScrubResult:
    """Result of a scrub pass — the redacted text and per-class counts."""

    text: str
    redactions: dict[str, int]

    @property
    def total_redactions(self) -> int:
        return sum(self.redactions.values())


def _replace_count(pattern: re.Pattern[str], text: str, token: str) -> tuple[str, int]:
    matches = pattern.findall(text)
    if not matches:
        return text, 0
    return pattern.sub(token, text), len(matches)


def scrub(
    text: str,
    *,
    extra_patterns: Iterable[tuple[str, re.Pattern[str], str]] | None = None,
) -> ScrubResult:
    """Return *text* with PII replaced by ``[REDACTED:<class>]`` tokens."""
    counts: dict[str, int] = {}
    out, n = _replace_count(EMAIL_RE, text, "[REDACTED:email]")
    if n:
        counts["email"] = n
    # AHPRA / Medicare / TFN MUST run before the phone regex so the long
    # all-digit identifiers are not eaten by the phone matcher.
    out, n = _replace_count(AHPRA_RE, out, "[REDACTED:ahpra]")
    if n:
        counts["ahpra"] = n
    out, n = _replace_count(MEDICARE_RE, out, "[REDACTED:medicare]")
    if n:
        counts["medicare"] = n
    out, n = _replace_count(TFN_RE, out, "[REDACTED:tfn]")
    if n:
        counts["tfn"] = n
    out, n = _replace_count(PHONE_RE, out, "[REDACTED:phone]")
    if n:
        counts["phone"] = n
    if extra_patterns:
        for name, pat, token in extra_patterns:
            out, n = _replace_count(pat, out, token)
            if n:
                counts[name] = n
    if os.getenv("USE_PRESIDIO") == "1":
        try:
            from presidio_analyzer import (  # type: ignore[import-not-found]
                AnalyzerEngine,
            )

            analyzer = AnalyzerEngine()
            findings = analyzer.analyze(text=out, language="en")
            for r in sorted(findings, key=lambda r: r.start, reverse=True):
                out = (
                    out[: r.start] + f"[REDACTED:{r.entity_type.lower()}]" + out[r.end :]
                )
                counts[r.entity_type.lower()] = counts.get(r.entity_type.lower(), 0) + 1
        except Exception:  # pragma: no cover - presidio missing in test env
            logger.debug("presidio_not_installed")
    return ScrubResult(text=out, redactions=counts)
