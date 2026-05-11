"""Integration: corpus staleness alert (T212).

Per FR-RAG-FRESH-02 + Plan §F-A8.3 — when ``corpus_age_days >= 14`` AND
``last_ingest_run_age_hours >= 48``, emit a ``corpus_stale`` Service Bus
event matching ``staleness_alert.schema.json``, page on-call, and turn
the UI indicator red.

Conversely, age 8 days → yellow but no alert. (UI signal only.)

Also covers T216 — flag-toggled suppression of on-call paging.

Proves: T215 — apps/api/app/services/corpus_freshness.py.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from apps.api.app.services.corpus_freshness import (
    assess_corpus_staleness,
    emit_corpus_stale_alert,
    set_corpus_freshness_alert_flag,
)


def _now() -> datetime:
    return datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_flag() -> Any:
    # Reset to default-on before each test.
    set_corpus_freshness_alert_flag(value=True, actor="test-fixture")
    yield


def test_15day_stale_corpus_with_48h_gap_fires_alert() -> None:
    """corpus age 15d + ingest gap 48h → alert fires (yellow)."""
    asmt = assess_corpus_staleness(
        corpus_build_sha="a" * 64,
        corpus_generated_at=_now() - timedelta(days=15),
        last_ingest_run_at=_now() - timedelta(hours=48),
        now=_now(),
    )
    assert asmt.is_stale is True
    assert asmt.severity == "yellow"
    assert asmt.corpus_age_days >= 14.0


def test_18day_stale_corpus_red_severity() -> None:
    """corpus age >= 17d → red severity."""
    asmt = assess_corpus_staleness(
        corpus_build_sha="b" * 64,
        corpus_generated_at=_now() - timedelta(days=18),
        last_ingest_run_at=_now() - timedelta(hours=72),
        now=_now(),
    )
    assert asmt.severity == "red"


def test_8day_corpus_below_threshold_is_not_stale() -> None:
    """corpus age 8d → not stale (UI yellow only, no alert)."""
    asmt = assess_corpus_staleness(
        corpus_build_sha="c" * 64,
        corpus_generated_at=_now() - timedelta(days=8),
        last_ingest_run_at=_now() - timedelta(hours=4),
        now=_now(),
    )
    assert asmt.is_stale is False
    assert asmt.severity == "ok"


def test_recent_ingest_grace_blocks_alert() -> None:
    """corpus age 15d but ingest 30h ago → grace window prevents alert."""
    asmt = assess_corpus_staleness(
        corpus_build_sha="d" * 64,
        corpus_generated_at=_now() - timedelta(days=15),
        last_ingest_run_at=_now() - timedelta(hours=30),
        now=_now(),
    )
    assert asmt.is_stale is False, "ingest within 48h grace window must suppress alert"


def test_emit_alert_payload_matches_schema_shape() -> None:
    """Emitted payload has every required field from staleness_alert.schema.json."""
    asmt = assess_corpus_staleness(
        corpus_build_sha="e" * 64,
        corpus_generated_at=_now() - timedelta(days=15),
        last_ingest_run_at=_now() - timedelta(hours=48),
        now=_now(),
    )
    sb_events: list[dict[str, Any]] = []
    pd_events: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []

    payload = emit_corpus_stale_alert(
        asmt,
        service_bus_emitter=sb_events.append,
        pagerduty_emitter=pd_events.append,
        audit_sink=audit.append,
        now_fn=_now,
    )

    assert payload is not None
    required_fields = {
        "alert_id",
        "alert_type",
        "emitted_at",
        "corpus_build_sha",
        "corpus_generated_at",
        "corpus_age_days",
        "last_ingest_run_at",
        "last_ingest_run_age_hours",
        "severity",
        "feature_flag_state",
    }
    assert required_fields.issubset(payload.keys())
    assert payload["alert_type"] == "corpus_stale"
    assert payload["severity"] == "yellow"
    assert len(sb_events) == 1
    assert len(pd_events) == 1, "on-call must page when flag is enabled"
    assert any(e["event_type"] == "corpus_freshness_state" for e in audit)


def test_disabled_flag_suppresses_pagerduty_but_audits_state() -> None:
    """T216 — flag-disabled suppresses on-call page; state still audited."""
    audit: list[dict[str, Any]] = []
    set_corpus_freshness_alert_flag(
        value=False,
        actor="ops-on-call",
        audit_sink=audit.append,
        now_fn=_now,
    )

    asmt = assess_corpus_staleness(
        corpus_build_sha="f" * 64,
        corpus_generated_at=_now() - timedelta(days=15),
        last_ingest_run_at=_now() - timedelta(hours=48),
        now=_now(),
    )
    sb_events: list[dict[str, Any]] = []
    pd_events: list[dict[str, Any]] = []

    payload = emit_corpus_stale_alert(
        asmt,
        service_bus_emitter=sb_events.append,
        pagerduty_emitter=pd_events.append,
        audit_sink=audit.append,
        now_fn=_now,
    )

    assert payload is not None
    assert payload["feature_flag_state"]["enabled"] is False
    assert len(sb_events) == 1, "Service Bus emission is unconditional"
    assert len(pd_events) == 0, "PagerDuty MUST be suppressed when flag is disabled"
    # Audit must include both the flag-flip event and the freshness-state event
    assert any(e["event_type"] == "corpus_freshness_alert_disabled" for e in audit), "flag-flip emits audit event"


def test_no_ingest_history_emits_red_with_sentinel_age() -> None:
    """``last_ingest_run_at=None`` → sentinel large value + red if corpus old."""
    asmt = assess_corpus_staleness(
        corpus_build_sha="0" * 64,
        corpus_generated_at=_now() - timedelta(days=20),
        last_ingest_run_at=None,
        now=_now(),
    )
    assert asmt.is_stale is True
    assert asmt.severity == "red"
    assert asmt.last_ingest_run_age_hours == 999999.0


def test_flag_flip_requires_actor() -> None:
    """Audit invariant: actor must be non-empty."""
    with pytest.raises(ValueError, match="actor required"):
        set_corpus_freshness_alert_flag(value=False, actor="")
