# Atomic, versioned KPI ladder repository.

from __future__ import annotations

import hashlib
import threading
from datetime import UTC, datetime
from typing import Any

from .._clients import get_registry
from ..models.kpi import IndicatorDefinition, RiskAdjustment

CONTAINER = "kpi_ladder"
_publish_lock = threading.RLock()


class VersionMonotonicityError(ValueError):
    pass


class DuplicateIndicatorIdError(ValueError):
    pass


def _model_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def _active(row: dict[str, Any]) -> bool:
    return not row.get("superseded_by") and row.get("publication_status", "published") == "published"


def latest_version_for(kpi_id: str) -> int:
    rows = [row for row in get_registry().get(CONTAINER).all() if row.get("kpi_id") == kpi_id]
    return max((int(row.get("version", 0)) for row in rows), default=0)


def _legacy_id(kpi_id: str, version: int, source_id: str) -> str:
    digest = hashlib.sha256(f"{kpi_id}|{version}|{source_id}|manual-risk-3x3".encode()).hexdigest()
    return digest[:26]


def _promote_legacy_risk_adjustments() -> None:
    with _publish_lock:
        container = get_registry().get(CONTAINER)
        active_rows = [row for row in container.all() if _active(row)]
        latest_by_kpi: dict[str, dict[str, Any]] = {}
        for row in active_rows:
            kpi_id = str(row.get("kpi_id", ""))
            previous = latest_by_kpi.get(kpi_id)
            if previous is None or int(row.get("version", 0)) > int(previous.get("version", 0)):
                latest_by_kpi[kpi_id] = row

        for kpi_id, row in latest_by_kpi.items():
            if row.get("risk_adjustment") is not None:
                continue
            legacy = IndicatorDefinition.model_validate(_model_row(row))
            promoted_version = latest_version_for(kpi_id) + 1
            promoted = legacy.model_copy(
                update={
                    "id": _legacy_id(kpi_id, promoted_version, legacy.id),
                    "version": promoted_version,
                    "risk_adjustment": RiskAdjustment(
                        likelihood=3,
                        consequence=3,
                        provenance="manual",
                        auditor_signoff_required=True,
                    ),
                    "provenance": "manual",
                    "publication_status": "published",
                    "superseded_by": None,
                    "created_at": datetime.now(UTC),
                    "created_by": "legacy-risk-migration",
                }
            )
            publish(promoted)


def list_published() -> list[IndicatorDefinition]:
    _promote_legacy_risk_adjustments()
    rows = get_registry().get(CONTAINER).all()
    by_kpi: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not _active(row):
            continue
        kpi_id = str(row.get("kpi_id", ""))
        previous = by_kpi.get(kpi_id)
        if previous is None or int(row.get("version", 0)) > int(previous.get("version", 0)):
            by_kpi[kpi_id] = row
    return [IndicatorDefinition.model_validate(_model_row(row)) for row in by_kpi.values()]


def list_versions(kpi_id: str) -> list[IndicatorDefinition]:
    rows = [row for row in get_registry().get(CONTAINER).all() if row.get("kpi_id") == kpi_id]
    rows.sort(key=lambda row: (int(row.get("version", 0)), str(row.get("id", ""))))
    return [IndicatorDefinition.model_validate(_model_row(row)) for row in rows]


def get_by_id(doc_id: str) -> IndicatorDefinition | None:
    try:
        row = get_registry().get(CONTAINER).read_item(doc_id)
    except KeyError:
        return None
    return IndicatorDefinition.model_validate(_model_row(row))


def get_version(kpi_id: str, version: int) -> IndicatorDefinition | None:
    matches = [indicator for indicator in list_versions(kpi_id) if indicator.version == version]
    return matches[-1] if matches else None


def _cosmos_batch_publish(
    container: Any,
    indicator: IndicatorDefinition,
    prior_rows: list[dict[str, Any]],
) -> bool:
    batch_container = getattr(container, "_container", container)
    execute_batch = getattr(batch_container, "execute_item_batch", None)
    if not callable(execute_batch):
        return False
    operations: list[tuple[str, tuple[Any, ...]]] = [
        ("create", (indicator.model_dump(mode="json"),)),
    ]
    for row in prior_rows:
        replacement = dict(row)
        replacement["superseded_by"] = indicator.id
        replacement["publication_status"] = "superseded"
        operations.append(("replace", (replacement["id"], replacement)))
    execute_batch(batch_operations=operations, partition_key=indicator.kpi_id)
    return True


def _memory_publish(
    container: Any,
    indicator: IndicatorDefinition,
    prior_rows: list[dict[str, Any]],
) -> None:
    replacements: list[tuple[str, dict[str, Any]]] = []
    for row in prior_rows:
        replacement = dict(row)
        replacement["superseded_by"] = indicator.id
        replacement["publication_status"] = "superseded"
        replacements.append((replacement["id"], replacement))
    replace_and_create = getattr(container, "replace_and_create", None)
    if callable(replace_and_create):
        replace_and_create(replacements, indicator.model_dump(mode="json"))
        return

    items = getattr(container, "_items", None)
    snapshot = {key: dict(value) for key, value in items.items()} if isinstance(items, dict) else None
    original_rows = [dict(row) for row in prior_rows]
    try:
        container.create_item(indicator.model_dump(mode="json"))
        for row in prior_rows:
            replacement = dict(row)
            replacement["superseded_by"] = indicator.id
            replacement["publication_status"] = "superseded"
            container.replace_item(replacement["id"], replacement)
    except Exception:
        if snapshot is not None and isinstance(items, dict):
            items.clear()
            items.update(snapshot)
        else:
            container.delete_item(indicator.id)
            for original in original_rows:
                container.replace_item(original["id"], original)
        raise


def publish(indicator: IndicatorDefinition) -> IndicatorDefinition:
    container = get_registry().get(CONTAINER)
    with _publish_lock:
        container_lock = getattr(container, "_lock", None)
        if container_lock is not None:
            container_lock.acquire()
        try:
            rows = container.all()
            if any(row.get("id") == indicator.id for row in rows):
                raise DuplicateIndicatorIdError(f"indicator id {indicator.id} already exists")
            current_max = max(
                (int(row.get("version", 0)) for row in rows if row.get("kpi_id") == indicator.kpi_id),
                default=0,
            )
            if indicator.version <= current_max:
                raise VersionMonotonicityError(
                    f"version {indicator.version} not greater than current max {current_max}"
                )
            prior_rows = [row for row in rows if row.get("kpi_id") == indicator.kpi_id and _active(row)]
            if not _cosmos_batch_publish(container, indicator, prior_rows):
                _memory_publish(container, indicator, prior_rows)
        finally:
            if container_lock is not None:
                container_lock.release()
    return indicator
