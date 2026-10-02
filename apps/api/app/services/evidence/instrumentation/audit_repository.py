from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from .._clients import get_registry
from ..models.audit import AuditEntry, AuditTrace

HOT_RETENTION_DAYS = 90


def list_for_value(value_id: str) -> list[AuditEntry]:
    registry = get_registry()
    hot_rows = [
        row
        for row in registry.get("evidence_audit").all()
        if row.get("value_id") == value_id or row.get("audit_id") == value_id
    ]
    cold_rows = [row for _, row in registry.blob_archive.list_json(f"audit/{value_id}/")]
    merged = _merge_rows(hot_rows, cold_rows)

    referenced_ids = {reference_id for row in merged.values() for reference_id in row.get("references", {}).values()}
    if referenced_ids:
        extra_hot = [
            row
            for row in registry.get("evidence_audit").all()
            if row.get("id") in referenced_ids or row.get("value_id") in referenced_ids
        ]
        extra_cold: list[dict[str, Any]] = []
        for reference_id in referenced_ids:
            extra_cold.extend(row for _, row in registry.blob_archive.list_json(f"audit/{reference_id}/"))
        merged = _merge_rows(
            [*hot_rows, *extra_hot],
            [*cold_rows, *extra_cold],
        )
    return [_entry_from_row(row) for row in merged.values()]


def list_archived_for_value(value_id: str) -> list[AuditEntry]:
    rows = [row for _, row in get_registry().blob_archive.list_json(f"audit/{value_id}/")]
    return [_entry_from_row({**row, "storage_source": "cold"}) for row in rows]


def archive_old_entries() -> int:
    cutoff = datetime.now(UTC) - timedelta(days=HOT_RETENTION_DAYS)
    return sum(
        1
        for row in get_registry().get("evidence_audit").all()
        if datetime.fromisoformat(str(row["occurred_at"])) < cutoff
    )


def build_trace(value_id: str) -> AuditTrace | None:
    entries = list_for_value(value_id)
    if not entries:
        return None
    return AuditTrace.build(
        value_id,
        entries,
        served_from_cold_archive=any(entry.storage_source == "cold" for entry in entries),
    )


def _merge_rows(
    hot_rows: list[dict[str, Any]],
    cold_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in cold_rows:
        merged[str(row["id"])] = {**row, "storage_source": "cold"}
    for row in hot_rows:
        item_id = str(row["id"])
        source = "hot+cold" if item_id in merged else "hot"
        merged[item_id] = {**row, "storage_source": source}
    return dict(
        sorted(
            merged.items(),
            key=lambda item: str(item[1].get("occurred_at", "")),
        )
    )


def _entry_from_row(row: dict[str, Any]) -> AuditEntry:
    return AuditEntry.model_validate({key: value for key, value in row.items() if key in AuditEntry.model_fields})
