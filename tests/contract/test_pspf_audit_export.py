"""Contract: PSPF audit export endpoint (T205).

Per FR-RAG-COMP-03 + SC-018 + Plan §F-A6.3 — ``GET /api/audit/export?
format=pspf&start=...&end=...`` returns CSV with the six PSPF-mandated
columns: ``Timestamp, User, Action, Resource, Outcome, Justification``.

Proves: T207 — apps/api/app/api/routes/audit_compliance.py.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from apps.api.app.api.routes.audit_compliance import (
    PSPF_COLUMNS,
    _render_pspf_csv,
    _to_pspf_row,
)


def _ev(**kw: Any) -> dict[str, Any]:
    return kw


def test_pspf_columns_exact_order() -> None:
    """Column header order is fixed and pinned per FR-RAG-COMP-03."""
    assert PSPF_COLUMNS == (
        "Timestamp",
        "User",
        "Action",
        "Resource",
        "Outcome",
        "Justification",
    )


def test_pspf_csv_header_first_row() -> None:
    """The first row of the CSV is the column header."""
    body = _render_pspf_csv([])
    reader = csv.reader(io.StringIO(body))
    assert next(reader) == list(PSPF_COLUMNS)


def test_pspf_csv_row_projection() -> None:
    """Each event projects to the 6-column shape."""
    event = _ev(
        timestamp="2026-06-01T12:00:00Z",
        actor_id="op-1@ama.local",
        event_type="evac_decision",
        resource="incident-007",
        outcome="success",
        justification="Bega Valley fire",
    )
    row = _to_pspf_row(event)
    assert row == (
        "2026-06-01T12:00:00Z",
        "op-1@ama.local",
        "evac_decision",
        "incident-007",
        "success",
        "Bega Valley fire",
    )


def test_pspf_csv_value_escaping_rfc4180() -> None:
    """Embedded commas and quotes are RFC 4180 escaped."""
    event = _ev(
        timestamp="2026-06-01T12:00:00Z",
        actor_id="op-1",
        event_type="note",
        resource="incident-007",
        outcome="success",
        justification='Comma, and "quote" in body',
    )
    body = _render_pspf_csv([event])
    reader = csv.reader(io.StringIO(body))
    rows = list(reader)
    assert rows[0] == list(PSPF_COLUMNS)
    assert rows[1][5] == 'Comma, and "quote" in body'


def test_pspf_csv_uses_crlf_line_terminator() -> None:
    """RFC 4180 mandates CRLF line endings."""
    body = _render_pspf_csv([])
    assert "\r\n" in body
    # exactly 1 CRLF for the header on an empty events list.
    assert body.count("\r\n") == 1


def test_pspf_csv_alt_field_names_supported() -> None:
    """Alternate field names (``user_id``, ``action``, ``target``,
    ``rationale``, ``created_at``) project to the same columns — repository
    drift insurance."""
    event = _ev(
        created_at="2026-06-01T00:00:00Z",
        user_id="op-2",
        action="read",
        target="audit-log",
        outcome="denied",
        rationale="rate-limited",
    )
    body = _render_pspf_csv([event])
    reader = csv.reader(io.StringIO(body))
    rows = list(reader)
    assert rows[1] == [
        "2026-06-01T00:00:00Z",
        "op-2",
        "read",
        "audit-log",
        "denied",
        "rate-limited",
    ]


def test_pspf_csv_default_outcome_when_missing() -> None:
    """If outcome is absent, default to 'success' (audit-record-llm-call.json
    treats success as the default)."""
    event = _ev(timestamp="2026-06-01T00:00:00Z", actor_id="op", event_type="r")
    row = _to_pspf_row(event)
    assert row[4] == "success"


def test_pspf_csv_multiple_events_in_order() -> None:
    """Events are emitted in input order (caller controls ordering)."""
    events = [
        _ev(timestamp="2026-06-01T00:00:00Z", actor_id="op", event_type="a"),
        _ev(timestamp="2026-06-02T00:00:00Z", actor_id="op", event_type="b"),
        _ev(timestamp="2026-06-03T00:00:00Z", actor_id="op", event_type="c"),
    ]
    body = _render_pspf_csv(events)
    reader = csv.reader(io.StringIO(body))
    rows = list(reader)
    assert [r[2] for r in rows[1:]] == ["a", "b", "c"]
