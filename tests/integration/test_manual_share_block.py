"""Spec-038 / T-A03 — Manual share > 50% blocked unless auditor sign-off."""

from __future__ import annotations

import pytest
from app.services.evidence._clients import reset_registry
from app.services.evidence.instrumentation import audit_manager
from app.services.evidence.kpi_ladder.manager import (
    ManualShareBlocked,
    publish_indicator,
    record_auditor_signoff,
)
from app.services.evidence.kpi_ladder.repository import list_published
from app.services.evidence.kpi_ladder.seed import _make


def _seed_two_auto_rows() -> None:
    publish_indicator(
        _make(
            kpi_id="a1",
            name="a1",
            kind="leading",
            sc="SC-CAP-015-001",
            provenance="auto",
            risk=(2, 2),
        )
    )
    publish_indicator(
        _make(
            kpi_id="a2",
            name="a2",
            kind="lagging",
            sc="SC-CAP-015-001",
            provenance="auto",
            risk=(2, 2),
        )
    )


def test_block_when_majority_manual_without_signoff():
    reset_registry()
    _seed_two_auto_rows()
    publish_indicator(_make(kpi_id="m1", name="m1", kind="leading", sc="SC-CAP-015-002", provenance="manual"))
    publish_indicator(_make(kpi_id="m2", name="m2", kind="lagging", sc="SC-CAP-015-002", provenance="manual"))
    # Now 2 manual / 4 = 50%, still ok. Adding a 3rd manual → 60% > 50% → block.
    with pytest.raises(ManualShareBlocked):
        publish_indicator(_make(kpi_id="m3", name="m3", kind="leading", sc="SC-CAP-015-003", provenance="manual"))


def test_unblock_after_auditor_signoff():
    reset_registry()
    _seed_two_auto_rows()
    publish_indicator(_make(kpi_id="m1", name="m1", kind="leading", sc="SC-CAP-015-002", provenance="manual"))
    publish_indicator(_make(kpi_id="m2", name="m2", kind="lagging", sc="SC-CAP-015-002", provenance="manual"))
    candidate = _make(
        kpi_id="m3",
        name="m3",
        kind="leading",
        sc="SC-CAP-015-003",
        provenance="manual",
    )
    record_auditor_signoff(
        artefact_id="kpi_ladder",
        indicators=[*list_published(), candidate],
        auditor_id="auditor-oid-123",
        approval_id="approval-123",
        basis="Reviewed the exact candidate snapshot and accepted manual provenance.",
    )
    publish_indicator(candidate)


def test_unbound_generic_signoff_does_not_unlock_candidate():
    reset_registry()
    _seed_two_auto_rows()
    publish_indicator(_make(kpi_id="m1", name="m1", kind="leading", sc="SC-CAP-015-002", provenance="manual"))
    publish_indicator(_make(kpi_id="m2", name="m2", kind="lagging", sc="SC-CAP-015-002", provenance="manual"))
    audit_manager.record(
        kind="auditor_signoff_recorded",
        value_id="kpi_ladder",
        actor="auditor-oid-123",
        payload={"authenticated": True, "auditor_id": "auditor-oid-123", "approval_id": "unbound"},
    )

    with pytest.raises(ManualShareBlocked):
        publish_indicator(
            _make(
                kpi_id="m3",
                name="m3",
                kind="leading",
                sc="SC-CAP-015-003",
                provenance="manual",
            )
        )


def test_replacement_denominator_deduplicates_stable_kpi_ids():
    reset_registry()
    first_auto = _make(
        kpi_id="a1",
        name="a1",
        kind="leading",
        sc="SC-CAP-015-001",
        provenance="auto",
        risk=(2, 2),
    )
    publish_indicator(first_auto)
    publish_indicator(
        _make(
            kpi_id="a2",
            name="a2",
            kind="lagging",
            sc="SC-CAP-015-001",
            provenance="auto",
            risk=(2, 2),
        )
    )
    publish_indicator(_make(kpi_id="m1", name="m1", kind="leading", sc="SC-CAP-015-002", provenance="manual"))
    replacement = _make(
        kpi_id="a1",
        name="a1 manual replacement",
        kind="leading",
        sc="SC-CAP-015-001",
        provenance="manual",
    ).model_copy(update={"version": 2})
    with pytest.raises(ManualShareBlocked):
        publish_indicator(replacement)
