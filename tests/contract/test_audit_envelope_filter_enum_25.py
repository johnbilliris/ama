"""Wave A / T-AA12 — Audit-envelope filter enumeration contract.

Asserts that the typed ``EntryType`` Literal in
:mod:`packages.domain.src.domain.models.telemetry_injection_audit_entry`
enumerates exactly 26 entries (Cycle 2 added entry-25
``signal_pipeline.dispatch_failed`` per Amendment A2-01 / FR-067; Cycle 3
added entry-26 ``staging_promotion.refused`` per Amendment A3-01 / FR-071)
and that ``DetailsByEntry`` contains a Pydantic dispatch class for every
one of them.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from typing import get_args

from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    ALL_ENTRY_TYPES,
    DetailsByEntry,
    EntryType,
)


def test_entry_type_literal_size_is_26() -> None:
    members = set(get_args(EntryType))
    assert len(members) == 26, (
        f"EntryType Literal MUST have exactly 26 members (got {len(members)}: {sorted(members)})."
    )


def test_all_entry_types_tuple_matches_literal() -> None:
    assert set(ALL_ENTRY_TYPES) == set(get_args(EntryType)), "ALL_ENTRY_TYPES MUST match the EntryType Literal members."


def test_every_entry_type_has_a_dispatch_class() -> None:
    """No entry_type may exist without a typed Pydantic dispatch class."""

    missing = sorted(e for e in ALL_ENTRY_TYPES if e not in DetailsByEntry)
    assert not missing, (
        f"Entry types MISSING from DetailsByEntry: {missing}. "
        "Every audit entry_type MUST have a typed Pydantic dispatch class."
    )


def test_signal_pipeline_dispatch_failed_is_entry_25() -> None:
    """Cycle 2 — `signal_pipeline.dispatch_failed` is entry-25."""

    assert "signal_pipeline.dispatch_failed" in ALL_ENTRY_TYPES
    assert "signal_pipeline.dispatch_failed" in DetailsByEntry


def test_staging_promotion_refused_is_entry_26() -> None:
    """Cycle 3 — `staging_promotion.refused` is entry-26 (A3-01 / FR-071)."""

    assert "staging_promotion.refused" in ALL_ENTRY_TYPES
    assert "staging_promotion.refused" in DetailsByEntry
