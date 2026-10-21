from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from ..audit_writer import write_audit_entry_sync
from ..models.audit import AuditEntry, AuditKind


class AppendOnlyViolation(PermissionError):
    pass


def record(
    *,
    kind: AuditKind,
    value_id: str,
    actor: str,
    references: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    correlation_id: str = "",
    region: str = "australiaeast",
    language_fallback_used: str | None = None,
) -> AuditEntry:
    if region not in {"australiaeast", "australiasoutheast"}:
        raise PermissionError(f"audit row region {region!r} is not AU-sovereign")
    if not actor.strip():
        raise ValueError("audit actor is required")
    entry_id = secrets.token_hex(13)
    entry = {
        "id": entry_id,
        "audit_id": value_id,
        "value_id": value_id,
        "kind": kind,
        "actor": actor,
        "occurred_at": datetime.now(UTC).isoformat(),
        "references": references or {},
        "payload": payload or {},
        "correlation_id": correlation_id,
        "region": region,
        "language_fallback_used": language_fallback_used,
        "storage_source": "hot",
    }
    if language_fallback_used is None:
        entry.pop("language_fallback_used")
    receipt = write_audit_entry_sync(entry)
    persisted = {key: value for key, value in receipt.entry.items() if key in AuditEntry.model_fields}
    return AuditEntry.model_validate(persisted)


def amend(
    *,
    original_entry_id: str,
    value_id: str,
    actor: str,
    payload: dict[str, Any] | None = None,
    correlation_id: str = "",
    region: str = "australiaeast",
) -> AuditEntry:
    return record(
        kind="kpi_amendment_recorded",
        value_id=value_id,
        actor=actor,
        references={"original_id": original_entry_id},
        payload=payload or {},
        correlation_id=correlation_id,
        region=region,
    )


def record_mutation_attempt(
    *,
    value_id: str,
    method: str,
    actor: str,
    correlation_id: str,
) -> AuditEntry:
    return record(
        kind="audit_mutation_attempted",
        value_id=value_id,
        actor=actor,
        references={"original_id": value_id},
        payload={"method": method.upper()},
        correlation_id=correlation_id,
    )


def reject_patch_or_delete() -> None:
    raise AppendOnlyViolation("evidence_audit is append-only; use amend() to record changes")
