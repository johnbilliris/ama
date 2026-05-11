"""Spec 036 / Phase F (T215 + T216) — Corpus staleness alert emitter.

Per FR-RAG-FRESH-02 + Plan §F-A8.3 — when the global corpus index is stale
(``corpus_age_days >= 14`` AND ``last_ingest_run_age_hours >= 48``), emit
a ``corpus_stale`` alert to Service Bus + on-call PagerDuty. Scope is
**global** (single signal per Pass 1 Q-P1-05), NOT per-jurisdiction.

Per Plan §F-A8.4 (T216) — ``feature.corpus_freshness_alert.enabled``
(Reversible class) suppresses the on-call paging when disabled but still
records the underlying state in the audit log.

This module is import-clean — Service Bus client is lazy.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Plan §F-A8.3 + spec contract:
STALE_AGE_THRESHOLD_DAYS: float = 14.0
STALE_INGEST_GAP_THRESHOLD_HOURS: float = 48.0
RED_AGE_THRESHOLD_DAYS: float = 17.0


# Module-level Reversible feature flag state.
_CORPUS_FRESHNESS_ALERT_ENABLED: bool = True
_FLAG_LAST_ACTOR: str | None = None
_FLAG_LAST_CHANGED_AT: datetime | None = None


def get_corpus_freshness_alert_enabled() -> bool:
    """Return the current ``feature.corpus_freshness_alert.enabled`` value."""
    return _CORPUS_FRESHNESS_ALERT_ENABLED


def set_corpus_freshness_alert_flag(
    *,
    value: bool,
    actor: str,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> None:
    """Flip the corpus-freshness alert feature flag.

    Reversible class per Pass 2 Q-P2-08. Disabling does NOT halt staleness
    detection — the underlying state is still recorded; only the on-call
    page is suppressed. Emits ``corpus_freshness_alert_disabled`` (or
    ``..._enabled``) audit event.
    """
    global _CORPUS_FRESHNESS_ALERT_ENABLED
    global _FLAG_LAST_ACTOR
    global _FLAG_LAST_CHANGED_AT

    if not actor:
        raise ValueError("actor required for feature-flag change (audit invariant)")
    old_value = _CORPUS_FRESHNESS_ALERT_ENABLED
    _CORPUS_FRESHNESS_ALERT_ENABLED = bool(value)
    _FLAG_LAST_ACTOR = actor
    _FLAG_LAST_CHANGED_AT = (now_fn or (lambda: datetime.now(tz=UTC)))()

    if audit_sink is not None:
        audit_sink(
            {
                "event_type": (
                    "corpus_freshness_alert_disabled" if not bool(value) else "corpus_freshness_alert_enabled"
                ),
                "flag_name": "feature.corpus_freshness_alert.enabled",
                "old_value": old_value,
                "new_value": _CORPUS_FRESHNESS_ALERT_ENABLED,
                "actor_id": actor,
                "timestamp": _FLAG_LAST_CHANGED_AT.isoformat(),
            }
        )


def _flag_state_block() -> dict[str, Any]:
    return {
        "flag_name": "feature.corpus_freshness_alert.enabled",
        "enabled": _CORPUS_FRESHNESS_ALERT_ENABLED,
        "actor_id": _FLAG_LAST_ACTOR,
        "changed_at": _FLAG_LAST_CHANGED_AT.isoformat() if _FLAG_LAST_CHANGED_AT else None,
    }


@dataclass(frozen=True)
class StalenessAssessment:
    """Outcome of one drift-detection sweep."""

    is_stale: bool
    severity: str  # "yellow" | "red" | "ok"
    corpus_age_days: float
    last_ingest_run_age_hours: float
    corpus_build_sha: str
    corpus_generated_at: datetime
    last_ingest_run_at: datetime | None


def assess_corpus_staleness(
    *,
    corpus_build_sha: str,
    corpus_generated_at: datetime,
    last_ingest_run_at: datetime | None,
    now: datetime | None = None,
) -> StalenessAssessment:
    """Compute the staleness assessment for the global corpus index."""
    ts = now or datetime.now(tz=UTC)
    age_days = (ts - corpus_generated_at).total_seconds() / 86400.0
    if last_ingest_run_at is None:
        ingest_age_hours = 999_999.0
    else:
        ingest_age_hours = (ts - last_ingest_run_at).total_seconds() / 3600.0

    is_stale = age_days >= STALE_AGE_THRESHOLD_DAYS and ingest_age_hours >= STALE_INGEST_GAP_THRESHOLD_HOURS
    if not is_stale:
        severity = "ok"
    elif age_days >= RED_AGE_THRESHOLD_DAYS:
        severity = "red"
    else:
        severity = "yellow"

    return StalenessAssessment(
        is_stale=is_stale,
        severity=severity,
        corpus_age_days=round(age_days, 1),
        last_ingest_run_age_hours=(round(ingest_age_hours, 1) if last_ingest_run_at else 999999.0),
        corpus_build_sha=corpus_build_sha,
        corpus_generated_at=corpus_generated_at,
        last_ingest_run_at=last_ingest_run_at,
    )


def emit_corpus_stale_alert(
    assessment: StalenessAssessment,
    *,
    service_bus_emitter: Callable[[dict[str, Any]], None] | None = None,
    pagerduty_emitter: Callable[[dict[str, Any]], None] | None = None,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any] | None:
    """Emit a corpus-staleness alert to Service Bus + PagerDuty.

    Returns the alert payload (matching staleness_alert.schema.json) when
    emitted; ``None`` when the assessment is not stale OR the feature flag
    is disabled (in which case the audit log still records the state).
    """
    ts = (now_fn or (lambda: datetime.now(tz=UTC)))()

    # Always record state in audit log per Plan §F-A8.4.
    if audit_sink is not None:
        audit_sink(
            {
                "event_type": "corpus_freshness_state",
                "is_stale": assessment.is_stale,
                "severity": assessment.severity,
                "corpus_build_sha": assessment.corpus_build_sha,
                "corpus_age_days": assessment.corpus_age_days,
                "last_ingest_run_age_hours": assessment.last_ingest_run_age_hours,
                "feature_flag_enabled": _CORPUS_FRESHNESS_ALERT_ENABLED,
                "timestamp": ts.isoformat(),
            }
        )

    if not assessment.is_stale:
        return None

    payload: dict[str, Any] = {
        "alert_id": str(uuid.uuid4()),
        "alert_type": "corpus_stale",
        "emitted_at": ts.isoformat(),
        "corpus_build_sha": assessment.corpus_build_sha,
        "corpus_generated_at": assessment.corpus_generated_at.isoformat(),
        "corpus_age_days": assessment.corpus_age_days,
        "last_ingest_run_at": (assessment.last_ingest_run_at.isoformat() if assessment.last_ingest_run_at else None),
        "last_ingest_run_age_hours": assessment.last_ingest_run_age_hours,
        "severity": assessment.severity,
        "feature_flag_state": _flag_state_block(),
        "remediation_link": "https://github.com/johnbilliris/ama/blob/main/docs/runbooks/036-foundry-rag-corpus-stale.md",
        "correlation_id": correlation_id or str(uuid.uuid4()),
    }

    # Service Bus emission is unconditional — downstream queue consumers
    # decide whether to act.
    if service_bus_emitter is not None:
        try:
            service_bus_emitter(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("corpus_stale_servicebus_error err=%s", exc)

    # PagerDuty paging is gated by the feature flag.
    if _CORPUS_FRESHNESS_ALERT_ENABLED and pagerduty_emitter is not None:
        try:
            pagerduty_emitter(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("corpus_stale_pagerduty_error err=%s", exc)

    return payload


__all__ = [
    "RED_AGE_THRESHOLD_DAYS",
    "STALE_AGE_THRESHOLD_DAYS",
    "STALE_INGEST_GAP_THRESHOLD_HOURS",
    "StalenessAssessment",
    "assess_corpus_staleness",
    "emit_corpus_stale_alert",
    "get_corpus_freshness_alert_enabled",
    "set_corpus_freshness_alert_flag",
]
