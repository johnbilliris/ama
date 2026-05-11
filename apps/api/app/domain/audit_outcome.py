"""Closed-set audit outcome enum (spec-035).

Source of truth: ``specs/035-webapp-capstone-closure/data-model.md`` § 4
"AuditTimelineEntry → Outcome enum (closed set)". MUST contain exactly 20
values; mirrors ``packages/domain/src/audit-outcome.ts``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class AuditOutcome(StrEnum):
    """Closed enumeration of every audit outcome the API may record."""

    APPROVED = "approved"
    DENIED = "denied"
    PUBLISHED = "published"
    ALLOCATE = "allocate"
    ADMIN_OVERRIDE = "admin_override"
    CLASSIFIER_DENY = "classifier_deny"
    CLASSIFIER_MASK = "classifier_mask"
    CLASSIFIER_FAILED = "classifier_failed"
    QUEUE_OVERFLOW = "queue_overflow"
    QUEUE_DISPLACED = "queue_displaced"
    ACTIVATION_MUTEX_VIOLATION = "activation_mutex_violation"
    RATE_LIMITED = "rate_limited"
    AUTH_UNAUTHORIZED = "auth_unauthorized"
    AUTH_FORBIDDEN = "auth_forbidden"
    SOVEREIGNTY_DENIED = "sovereignty_denied"
    SCHEMA_INVALID = "schema_invalid"
    SEED_NOT_READY = "seed_not_ready"
    EVALUATOR_NOT_ROUTABLE = "evaluator_not_routable"
    CULTURAL_SAFETY_TIMEOUT_OVERRIDE = "cultural_safety_timeout_override"
    CULTURAL_SAFETY_HELD = "cultural_safety_held"


AUDIT_OUTCOMES: Final[tuple[str, ...]] = tuple(member.value for member in AuditOutcome)
AUDIT_OUTCOME_COUNT: Final[int] = 20
