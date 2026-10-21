from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class IngestionAuditEntry(BaseModel):
    audit_id: str
    signal_id: str | None = None
    data_source_id: str
    correlation_id: str
    timestamp: datetime
    outcome: Literal["success", "rejected", "failed", "deduplicated", "blocked", "degraded"]
    validation_status: Literal["pending", "validated", "contradicted", "rejected", "escalated"] | None = None
    validation_errors: list[str] = Field(default_factory=list)
    raw_payload_blob_uri: str | None = None
    raw_archival_enabled: bool = True
    normalisation_latency_ms: float = 0.0
    pipeline_id: str = ""
    dedup_hash: str = ""

    @model_validator(mode="after")
    def validate_outcome_fields(self) -> "IngestionAuditEntry":
        if self.outcome == "rejected" and not self.validation_errors:
            raise ValueError("validation_errors required when outcome is 'rejected'")
        if self.outcome == "success" and not self.signal_id:
            raise ValueError("signal_id required when outcome is 'success'")
        if self.outcome == "success" and self.validation_status is None:
            raise ValueError("validation_status required when outcome is 'success'")
        if self.raw_archival_enabled and self.outcome == "success" and not self.raw_payload_blob_uri:
            raise ValueError("raw_payload_blob_uri required when archival is enabled and outcome is 'success'")
        if self.outcome in {"blocked", "degraded"} and not self.validation_errors:
            raise ValueError("validation_errors required when outcome is 'blocked' or 'degraded'")
        return self
