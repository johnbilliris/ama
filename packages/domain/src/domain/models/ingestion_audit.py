from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class IngestionAuditEntry(BaseModel):
    audit_id: str
    signal_id: str | None = None
    data_source_id: str
    correlation_id: str
    timestamp: datetime
    outcome: Literal["success", "rejected", "failed", "deduplicated"]
    validation_errors: list[str] = Field(default_factory=list)
    raw_payload_blob_uri: str | None = None
    normalisation_latency_ms: float = 0.0
    pipeline_id: str = ""
    dedup_hash: str = ""

    @model_validator(mode="after")
    def validate_outcome_fields(self) -> "IngestionAuditEntry":
        if self.outcome == "rejected" and not self.validation_errors:
            raise ValueError("validation_errors required when outcome is 'rejected'")
        if self.outcome == "success" and (not self.signal_id or not self.raw_payload_blob_uri):
            raise ValueError("signal_id and raw_payload_blob_uri required when outcome is 'success'")
        return self
