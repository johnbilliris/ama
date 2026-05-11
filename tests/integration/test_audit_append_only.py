"""Spec-038 / T-F02 — Audit append-only contract."""

from __future__ import annotations

import pytest
from app.services.evidence._clients import get_registry, reset_registry
from app.services.evidence.instrumentation import audit_manager


def test_patch_or_delete_rejected_at_manager_tier():
    with pytest.raises(audit_manager.AppendOnlyViolation):
        audit_manager.reject_patch_or_delete()


def test_amendment_creates_new_entry_preserving_original():
    reset_registry()
    original = audit_manager.record(
        kind="ladder_version_published",
        value_id="kpi-x",
        actor="risk-mgr",
        payload={"version": 1},
    )
    amend = audit_manager.amend(
        original_entry_id=original.id,
        value_id="kpi-x",
        actor="risk-mgr",
        payload={"new_version": 2, "reason": "FR-002 attribute correction"},
    )
    container = get_registry().get("evidence_audit")
    rows = container.all()
    assert any(r["id"] == original.id for r in rows), "original must be preserved"
    assert amend.id != original.id
    assert amend.references["original_id"] == original.id
    assert amend.kind == "kpi_amendment_recorded"


def test_replace_or_delete_on_audit_container_blocked():
    reset_registry()
    entry = audit_manager.record(
        kind="signal_ingested",
        value_id="kpi-y",
        actor="ingest",
        references={"signal": "sig-1"},
    )
    container = get_registry().get("evidence_audit")
    with pytest.raises(PermissionError):
        container.replace_item(entry.id, {"id": entry.id, "tampered": True})
    with pytest.raises(PermissionError):
        container.delete_item(entry.id)
