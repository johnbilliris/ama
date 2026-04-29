"""Sanitise-real workflow — converts a real-world incident transcript into a
synthetic case suitable for the eval corpus.

PII redaction → graphic-hazard sensitivity tagging → dual-reviewer requirement.
Used by Phase 8 (US6) operators with `Eval.DatasetCurator` role.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

# Common PII patterns — operator must add jurisdiction-specific patterns at runtime.
_DEFAULT_PII_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b", "[REDACTED-CARD]"),
    (r"\b\d{2}-\d{3}-\d{3}\b", "[REDACTED-MEDICARE]"),
    (r"\b04\d{2}\s?\d{3}\s?\d{3}\b", "[REDACTED-MOBILE-AU]"),
    (r"\b[\w.-]+@[\w.-]+\.\w+\b", "[REDACTED-EMAIL]"),
    (r"\b\d+\s+[A-Z][a-z]+\s+(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr)\b", "[REDACTED-ADDRESS]"),
]


@dataclass
class SanitisationLog:
    appliedPatterns: list[str] = field(default_factory=list)
    redactionCount: int = 0
    sanitiserId: str = ""
    sanitisedAt: datetime = field(default_factory=lambda: datetime.now(UTC))
    sourceHash: str = ""


@dataclass
class SanitiseResult:
    sanitisedText: str
    log: SanitisationLog
    requiresGraphicHazardTag: bool


_GRAPHIC_HAZARD_KEYWORDS = {
    "burned bodies",
    "human remains",
    "decapitated",
    "dismembered",
    "charred remains",
    "fatality",
    "deceased",
    "corpse",
}


def sanitise(text: str, sanitiser_id: str, patterns: list[tuple[str, str]] | None = None) -> SanitiseResult:
    """Return a sanitised version of `text` with a SanitisationLog."""
    pat = patterns or _DEFAULT_PII_PATTERNS
    log = SanitisationLog(sanitiserId=sanitiser_id, sourceHash=f"sha256:{hashlib.sha256(text.encode()).hexdigest()}")
    out = text
    for regex, replacement in pat:
        new_out, count = re.subn(regex, replacement, out)
        if count:
            log.appliedPatterns.append(regex)
            log.redactionCount += count
            out = new_out
    lower = out.lower()
    requires_tag = any(kw in lower for kw in _GRAPHIC_HAZARD_KEYWORDS)
    return SanitiseResult(sanitisedText=out, log=log, requiresGraphicHazardTag=requires_tag)


__all__ = ["SanitisationLog", "SanitiseResult", "sanitise"]
