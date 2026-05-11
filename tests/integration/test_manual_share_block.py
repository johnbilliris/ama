"""Spec-038 / T-A03 — Manual share > 50% blocked unless auditor sign-off."""

from __future__ import annotations

import pytest
from app.services.evidence._clients import reset_registry
from app.services.evidence.instrumentation import audit_manager
from app.services.evidence.kpi_ladder.manager import (
    ManualShareBlocked,
    publish_indicator,
)
from app.services.evidence.kpi_ladder.seed import _make


def _seed_two_auto_rows() -> None:
    publish_indicator(_make(kpi_id="a1", name="a1", kind="leading", sc="SC-CAP-015-001", provenance="auto"))
    publish_indicator(_make(kpi_id="a2", name="a2", kind="lagging", sc="SC-CAP-015-001", provenance="auto"))


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
    audit_manager.record(
        kind="auditor_signoff_recorded",
        value_id="kpi_ladder",
        actor="external-auditor",
    )
    # With auditor sign-off on file the 60% manual publish proceeds.
    publish_indicator(_make(kpi_id="m3", name="m3", kind="leading", sc="SC-CAP-015-003", provenance="manual"))
