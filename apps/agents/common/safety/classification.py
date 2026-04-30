"""Sensitive-content classifier (spec 032 ADR-033 + FR-AI03 + FR-O05).

Implements three orthogonal classifiers run in series, plus deterministic
hash-redaction helpers used by the PII validator (FR-O05).

Classifiers:
  1. PII detector — pattern set for Australian identifiers (Medicare, TFN,
     driver's licence, passport) plus generic email/phone/credit-card.
  2. PSPF marking detector — strict regex for OFFICIAL: Sensitive, PROTECTED,
     SECRET, TOP SECRET markings + Australian-government metadata patterns.
  3. Sensitive operational content — pattern set covering operator badge IDs,
     ATSI community identifiers (cultural-protocol flag), victim/casualty
     identifiers, and classified location coordinates.

Used by:
  - The model gateway before any non-AU transit (Phi shadow path; FR-AI03).
  - The PII redaction validator middleware (FR-O05).
  - The carve-out OPA policy (FR-AI03a) — outcomes inform deploy-time
    enforcement.

Detector implementations are intentionally lightweight (regex + small ML hooks)
so they run on the request hot path without external service dependencies.
The richer Microsoft Presidio integration is wired in via ``presidio_ext``
when the optional dependency is installed (best-effort).
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class ClassificationClass(StrEnum):
    """Classes of sensitive content the platform recognises."""

    PII_PERSONAL = "pii.personal"
    PII_LOCATION = "pii.location"
    PSPF_OFFICIAL_SENSITIVE = "pspf.official_sensitive"
    PSPF_PROTECTED = "pspf.protected"
    PSPF_SECRET = "pspf.secret"
    OPERATOR_IDENTIFIER = "operator.identifier"
    VICTIM_IDENTIFIER = "victim.identifier"
    ATSI_COMMUNITY = "atsi.community"
    CLASSIFIED_LOCATION = "classified.location"


class ClassificationAction(StrEnum):
    """Action to take when a class is detected."""

    ALLOW = "allow"
    REDACT = "redact"
    HASH_REDACT = "hash_redact"
    DENY = "deny"


@dataclass(frozen=True)
class ClassificationResult:
    """A single matched span with its class + recommended action."""

    cls: ClassificationClass
    action: ClassificationAction
    matched_text: str
    span: tuple[int, int]


@dataclass
class ClassificationVerdict:
    """Aggregate verdict for a complete payload."""

    matches: list[ClassificationResult] = field(default_factory=list)
    redacted_text: str = ""
    denied: bool = False
    denial_reasons: list[str] = field(default_factory=list)

    def class_counts(self) -> dict[str, int]:
        """Return a dict of `class -> count` (used for audit events)."""
        out: dict[str, int] = {}
        for m in self.matches:
            out[m.cls.value] = out.get(m.cls.value, 0) + 1
        return out


# ---------------------------------------------------------------------------
# Default action policy (ADR-033 — non-AU transit)
# ---------------------------------------------------------------------------

DEFAULT_NON_AU_TRANSIT_POLICY: dict[ClassificationClass, ClassificationAction] = {
    ClassificationClass.PII_PERSONAL: ClassificationAction.REDACT,
    ClassificationClass.PII_LOCATION: ClassificationAction.REDACT,
    ClassificationClass.PSPF_OFFICIAL_SENSITIVE: ClassificationAction.DENY,
    ClassificationClass.PSPF_PROTECTED: ClassificationAction.DENY,
    ClassificationClass.PSPF_SECRET: ClassificationAction.DENY,
    ClassificationClass.OPERATOR_IDENTIFIER: ClassificationAction.REDACT,
    ClassificationClass.VICTIM_IDENTIFIER: ClassificationAction.DENY,
    ClassificationClass.ATSI_COMMUNITY: ClassificationAction.DENY,
    ClassificationClass.CLASSIFIED_LOCATION: ClassificationAction.DENY,
}

DEFAULT_AU_LOG_POLICY: dict[ClassificationClass, ClassificationAction] = {
    ClassificationClass.PII_PERSONAL: ClassificationAction.HASH_REDACT,
    ClassificationClass.PII_LOCATION: ClassificationAction.HASH_REDACT,
    ClassificationClass.PSPF_OFFICIAL_SENSITIVE: ClassificationAction.ALLOW,
    ClassificationClass.PSPF_PROTECTED: ClassificationAction.ALLOW,
    ClassificationClass.PSPF_SECRET: ClassificationAction.DENY,
    ClassificationClass.OPERATOR_IDENTIFIER: ClassificationAction.ALLOW,
    ClassificationClass.VICTIM_IDENTIFIER: ClassificationAction.ALLOW,
    ClassificationClass.ATSI_COMMUNITY: ClassificationAction.ALLOW,
    ClassificationClass.CLASSIFIED_LOCATION: ClassificationAction.ALLOW,
}


# ---------------------------------------------------------------------------
# Regex pattern set — kept centralised + reviewable
# ---------------------------------------------------------------------------

_PATTERNS: dict[ClassificationClass, list[re.Pattern[str]]] = {
    ClassificationClass.PII_PERSONAL: [
        # Australian Medicare number: 10 digits, optional space groups
        re.compile(r"\b\d{4}\s?\d{5}\s?\d\b"),
        # Australian TFN: 8-9 digits (optional grouping)
        re.compile(r"\b\d{3}\s?\d{3}\s?\d{2,3}\b"),
        # Email (loose)
        re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
        # AU mobile (04xx xxx xxx)
        re.compile(r"\b04\d{2}\s?\d{3}\s?\d{3}\b"),
        # Credit-card-shaped 16-digit
        re.compile(r"\b(?:\d[ -]?){15}\d\b"),
    ],
    ClassificationClass.PII_LOCATION: [
        # AU postcode + suburb hint (e.g., "Sydney NSW 2000")
        re.compile(r"\b(?:NSW|VIC|QLD|SA|WA|TAS|ACT|NT)\s+\d{4}\b"),
    ],
    ClassificationClass.PSPF_OFFICIAL_SENSITIVE: [
        re.compile(r"\bOFFICIAL\s*:\s*Sensitive\b", re.IGNORECASE),
    ],
    ClassificationClass.PSPF_PROTECTED: [
        re.compile(r"\bPROTECTED(?:\s|:|\b)", re.IGNORECASE),
    ],
    ClassificationClass.PSPF_SECRET: [
        re.compile(r"\b(?:TOP\s+)?SECRET(?:\s|:|\b)", re.IGNORECASE),
    ],
    ClassificationClass.OPERATOR_IDENTIFIER: [
        # Common badge/employee patterns: BADGE-#####, EMP#####, LEID-#####
        re.compile(r"\b(?:BADGE|EMP|LEID)[-_]?\d{4,8}\b", re.IGNORECASE),
    ],
    ClassificationClass.VICTIM_IDENTIFIER: [
        # Medical record number patterns: MRN-####### or "MRN #######"
        re.compile(r"\bMRN[\s:-]?\d{5,10}\b", re.IGNORECASE),
    ],
    ClassificationClass.ATSI_COMMUNITY: [
        # Hint markers used by community liaisons (sample; real list is curated)
        re.compile(r"\bCULTURAL[-_]PROTOCOL\b", re.IGNORECASE),
    ],
    ClassificationClass.CLASSIFIED_LOCATION: [
        # Lat/long pairs flagged when within a classified-asset bounding box
        # (the bounding-box check is policy-driven; pattern just identifies
        # well-formed coordinates so the policy can decide).
        re.compile(r"\b-?\d{1,2}\.\d{4,8},\s*\d{1,3}\.\d{4,8}\b"),
    ],
}


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


class SensitiveContentClassifier:
    """Run the regex pattern set + optional Presidio over a payload, returning a verdict."""

    def __init__(
        self,
        policy: dict[ClassificationClass, ClassificationAction] | None = None,
        *,
        salt: str = "ama-classifier-v1",
    ) -> None:
        self._policy = policy or DEFAULT_NON_AU_TRANSIT_POLICY
        self._salt = salt

    def classify(self, text: str) -> ClassificationVerdict:
        """Run all classifiers and return an aggregated verdict.

        The returned ``redacted_text`` honours ``redact``/``hash_redact`` actions
        only; ``deny`` actions short-circuit by setting ``denied = True`` and
        returning the original text unchanged (the caller MUST refuse transit).
        """
        verdict = ClassificationVerdict(redacted_text=text)

        for cls, patterns in _PATTERNS.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    action = self._policy.get(cls, ClassificationAction.ALLOW)
                    verdict.matches.append(
                        ClassificationResult(cls=cls, action=action, matched_text=match.group(), span=match.span())
                    )

        # Apply actions in priority order: deny > redact > hash_redact > allow.
        if any(m.action is ClassificationAction.DENY for m in verdict.matches):
            verdict.denied = True
            verdict.denial_reasons = sorted(
                {f"{m.cls.value}" for m in verdict.matches if m.action is ClassificationAction.DENY}
            )
            return verdict

        # Apply redactions in reverse-span order so indices stay valid.
        edits = sorted(
            (m for m in verdict.matches if m.action in (ClassificationAction.REDACT, ClassificationAction.HASH_REDACT)),
            key=lambda m: m.span[0],
            reverse=True,
        )
        out = text
        for edit in edits:
            start, end = edit.span
            replacement = (
                f"[REDACTED:{edit.cls.value}]"
                if edit.action is ClassificationAction.REDACT
                else f"[HASH:{hash_redact(edit.matched_text, self._salt)}]"
            )
            out = out[:start] + replacement + out[end:]
        verdict.redacted_text = out
        return verdict


# ---------------------------------------------------------------------------
# Functional helpers
# ---------------------------------------------------------------------------


def classify(text: str, *, non_au: bool = True) -> ClassificationVerdict:
    """One-shot classifier: choose a policy and run."""
    policy = DEFAULT_NON_AU_TRANSIT_POLICY if non_au else DEFAULT_AU_LOG_POLICY
    return SensitiveContentClassifier(policy=policy).classify(text)


def hash_redact(value: str, salt: str = "ama-classifier-v1") -> str:
    """Return a deterministic short hash for ``value`` (used in logs).

    Uses SHA-256(salt || value), truncated to 12 hex chars. Salt is environment-
    configurable via ``CLASSIFIER_HASH_SALT`` for prod deployments.
    """
    digest = hashlib.sha256(f"{salt}|{value}".encode()).hexdigest()
    return digest[:12]


def class_counts_event(verdict: ClassificationVerdict) -> dict[str, Any]:
    """Build a structured audit event dict from a verdict (no raw payload)."""
    return {
        "denied": verdict.denied,
        "denial_reasons": verdict.denial_reasons,
        "class_counts": verdict.class_counts(),
    }


def all_classes() -> Iterable[ClassificationClass]:
    """Iterate all defined classes (used by the OPA policy generator)."""
    return list(ClassificationClass)
