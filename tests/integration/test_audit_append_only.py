"""Spec-038 / T-F02 — Audit append-only contract."""

from __future__ import annotations

from unittest import mock

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
    archived = get_registry().blob_archive.list_json("audit/kpi-x/")
    assert {row["id"] for _, row in archived} == {original.id, amend.id}


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


def test_duplicate_audit_id_with_different_payload_is_rejected():
    from app.services.evidence.audit_writer import (
        AuditWriteUnavailableError,
        write_audit_entry_sync,
    )

    reset_registry()
    base = {
        "id": "fixed-entry",
        "audit_id": "fixed-value",
        "value_id": "fixed-value",
        "kind": "signal_ingested",
        "actor": "fixture",
        "occurred_at": "2026-09-24T00:00:00+00:00",
        "references": {},
        "payload": {"version": 1},
        "correlation_id": "fixed",
        "region": "australiaeast",
        "storage_source": "hot",
    }
    write_audit_entry_sync(base)

    with pytest.raises(AuditWriteUnavailableError):
        write_audit_entry_sync({**base, "payload": {"version": 2}})


def test_mirror_checkpoint_advances_only_after_durable_batch():
    from app.services.evidence.jobs.audit_mirror import mirror_batch

    reset_registry()
    audit_manager.record(
        kind="signal_ingested",
        value_id="mirror-value",
        actor="fixture",
    )
    registry = get_registry()

    assert mirror_batch(registry=registry) == 1
    assert mirror_batch(registry=registry) == 0
    checkpoints = [row for row in registry.get("evidence_audit_dlq").all() if row["kind"] == "audit_mirror_checkpoint"]
    assert len(checkpoints) == 1


def test_mirror_replays_safely_after_checkpoint_failure():
    from app.services.evidence.jobs.audit_mirror import mirror_batch

    reset_registry()
    audit_manager.record(
        kind="signal_ingested",
        value_id="restart-value",
        actor="fixture",
    )
    registry = get_registry()
    checkpoint_store = registry.get("evidence_audit_dlq")
    original_create = checkpoint_store.create_item

    with mock.patch.object(
        checkpoint_store,
        "create_item",
        side_effect=ConnectionError("checkpoint unavailable"),
    ):
        with pytest.raises(ConnectionError):
            mirror_batch(registry=registry)

    assert mirror_batch(registry=registry) == 1
    assert original_create is not None
    assert len(registry.blob_archive.list_json("audit/restart-value/")) == 1


def test_real_cosmos_adapter_blocks_append_only_mutations():
    from app.services.evidence._clients import CosmosContainerAdapter

    class _FakeContainer:
        def create_item(self, body, **kwargs):
            return body

        def upsert_item(self, body, **kwargs):
            raise AssertionError("append-only adapter must not call SDK upsert")

        def replace_item(self, **kwargs):
            raise AssertionError("append-only adapter must not call SDK replace")

        def delete_item(self, **kwargs):
            raise AssertionError("append-only adapter must not call SDK delete")

    adapter = CosmosContainerAdapter(
        "evidence_audit",
        _FakeContainer(),
        "audit_id",
        append_only=True,
    )

    assert adapter.upsert_item({"id": "new", "audit_id": "trace"})["id"] == "new"
    with pytest.raises(PermissionError):
        adapter.replace_item("new", {"id": "new", "audit_id": "trace"})
    with pytest.raises(PermissionError):
        adapter.delete_item("new", partition_key="trace")
