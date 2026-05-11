"""Append-only audit Manager (T-S12, FR-025, CHK046, CHK054).

Centralises the audit-row emission contract:
    - Container `evidence_audit` rejects PATCH/DELETE; amendments are NEW
      entries with `kind="kpi_amendment_recorded"` + `references["original_id"]`.
    - All audit rows persist in AU regions only (FR-029).
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from .._clients import get_registry
from ..models.audit import AuditEntry, AuditKind


class AppendOnlyViolation(PermissionError):
    """Raised on attempted PATCH/DELETE against the audit container."""


def _new_id() -> str:
    return secrets.token_hex(13)  # 26 chars, ULID-like


def record(
    *,
    kind: AuditKind,
    value_id: str,
    actor: str,
    references: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    correlation_id: str = "",
    region: str = "australiaeast",
) -> AuditEntry:
    """Write a new append-only audit row. FR-025."""
    if region not in {"australiaeast", "australiasoutheast"}:
        raise PermissionError(f"audit row region {region!r} not AU-sovereign (FR-029)")
    entry = AuditEntry(
        id=_new_id(),
        audit_id=value_id,
        value_id=value_id,
        kind=kind,
        actor=actor,
        occurred_at=datetime.now(UTC),
        references=references or {},
        payload=payload or {},
        correlation_id=correlation_id,
        region=region,  # type: ignore[arg-type]
    )
    container = get_registry().get("evidence_audit")
    container.create_item(entry.model_dump(mode="json"))
    return entry


def amend(
    *,
    original_entry_id: str,
    value_id: str,
    actor: str,
    payload: dict[str, Any] | None = None,
    correlation_id: str = "",
    region: str = "australiaeast",
) -> AuditEntry:
    """Record an amendment as a NEW entry (FR-025)."""
    refs = {"original_id": original_entry_id}
    return record(
        kind="kpi_amendment_recorded",
        value_id=value_id,
        actor=actor,
        references=refs,
        payload=payload or {},
        correlation_id=correlation_id,
        region=region,
    )


def reject_patch_or_delete() -> None:
    """Hook used by the FastAPI router layer to assert the contract."""
    raise AppendOnlyViolation("evidence_audit container is append-only; use amend() to record changes (FR-025)")
