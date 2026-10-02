from datetime import UTC, datetime
from uuid import uuid4

from app.services.state_store import DEAD_LETTERS
from fastapi import HTTPException

from packages.domain.src.domain.models.dead_letter_entry import DeadLetterEntry, ResolutionState


def _active_tenant_scope() -> str:
    from app.core.tenant_context import get_current_tenant

    try:
        return get_current_tenant().tenant_id
    except LookupError:
        return "live"


def _tenant_scope_matches(entry_scope_key: str, tenant_scope: str) -> bool:
    return entry_scope_key == tenant_scope or entry_scope_key.startswith(f"{tenant_scope}:")


class DeadLetterService:
    def create_entry(
        self,
        *,
        entry_type: str,
        correlation_id: str,
        original_payload: dict[str, object],
        failure_reason: str,
        failure_code: str,
        source_service: str,
        target_service: str,
        tenant_scope_key: str,
        incident_id: str | None = None,
        retry_count: int = 0,
        attempt_count: int | None = None,
    ) -> DeadLetterEntry:
        resolved_attempt_count = attempt_count if attempt_count is not None else retry_count + 1
        entry = DeadLetterEntry(
            entry_id=f"dlq-{uuid4().hex}",
            entry_type=entry_type,
            correlation_id=correlation_id,
            original_payload=original_payload,
            failure_reason=failure_reason,
            failure_code=failure_code,
            attempt_count=resolved_attempt_count,
            source_service=source_service,
            target_service=target_service,
            tenant_scope_key=tenant_scope_key,
            incident_id=incident_id,
            retry_count=retry_count,
        )
        DEAD_LETTERS[entry.entry_id] = entry
        return entry

    def query_entries(
        self,
        *,
        entry_type: str | None = None,
        resolution: ResolutionState | None = None,
        incident_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[DeadLetterEntry], int]:
        tenant_scope = _active_tenant_scope()
        records = [
            record for record in DEAD_LETTERS.values() if _tenant_scope_matches(record.tenant_scope_key, tenant_scope)
        ]
        if entry_type is not None:
            records = [record for record in records if record.entry_type == entry_type]
        if resolution is not None:
            records = [record for record in records if record.resolution == resolution]
        if incident_id is not None:
            records = [record for record in records if record.incident_id == incident_id]

        total = len(records)
        return records[offset : offset + limit], total

    def resolve_entry(
        self,
        *,
        entry_id: str,
        resolution: ResolutionState,
        resolved_by_persona_id: str,
        notes: str | None = None,
    ) -> DeadLetterEntry:
        tenant_scope = _active_tenant_scope()
        entry = DEAD_LETTERS.get(entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Dead-letter entry not found")
        if not _tenant_scope_matches(entry.tenant_scope_key, tenant_scope):
            raise HTTPException(status_code=404, detail="Dead-letter entry not found")

        if entry.resolution != "pending":
            raise HTTPException(status_code=409, detail="Dead-letter entry is already resolved")
        entry.resolve(
            resolution=resolution,
            reviewed_by=resolved_by_persona_id,
            reviewed_at=datetime.now(UTC),
            notes=notes,
        )
        DEAD_LETTERS[entry.entry_id] = entry
        return entry
