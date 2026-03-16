from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.services.state_store import DEAD_LETTERS
from packages.domain.src.domain.models.dead_letter_entry import DeadLetterEntry, ResolutionState


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
    ) -> DeadLetterEntry:
        entry = DeadLetterEntry(
            entry_id=f"dlq-{uuid4().hex}",
            entry_type=entry_type,
            correlation_id=correlation_id,
            original_payload=original_payload,
            failure_reason=failure_reason,
            failure_code=failure_code,
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
        records = list(DEAD_LETTERS.values())
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
        entry = DEAD_LETTERS.get(entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Dead-letter entry not found")

        if entry.resolution != "pending":
            raise HTTPException(status_code=409, detail="Dead-letter entry is already resolved")

        entry.resolution = resolution
        entry.reviewed_by = resolved_by_persona_id
        entry.reviewed_at = datetime.now(timezone.utc)
        if notes:
            entry.original_payload["resolution_notes"] = notes
        DEAD_LETTERS[entry.entry_id] = entry
        return entry
