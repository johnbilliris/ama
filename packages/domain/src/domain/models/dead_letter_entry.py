from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


ResolutionState = Literal["pending", "replayed", "discarded", "escalated"]
EntryType = Literal["handoff_failure", "ingestion_failure", "event_delivery_failure"]


class DeadLetterEntry(BaseModel):
    entry_id: str
    entry_type: EntryType
    correlation_id: str
    original_payload: dict[str, object] = Field(default_factory=dict)
    failure_reason: str
    failure_code: str
    retry_count: int = 0
    source_service: str
    target_service: str
    incident_id: str | None = None
    tenant_scope_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None
    resolution: ResolutionState = "pending"
