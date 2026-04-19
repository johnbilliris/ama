"""Audit export job tracking models.

New domain models for async audit export operations (021).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ExportFormat = Literal["pdf", "csv", "json"]


class AuditExportJob(BaseModel):
    """Tracks an asynchronous audit export operation."""

    id: str = Field(description="Unique job ID, format: export-{uuid}")
    tenant_id: str
    requested_by: str = Field(description="User identity who initiated the export")
    requested_at: datetime
    format: ExportFormat
    status: Literal["queued", "processing", "complete", "failed"]
    filter_params: dict = Field(
        default_factory=dict,
        description="The search/filter parameters used to select records",
    )
    record_count: int = Field(ge=0, default=0, description="Number of records in export")
    download_url: str | None = Field(
        default=None,
        description="Azure Blob Storage SAS URL, set when status='complete'",
    )
    download_expires_at: datetime | None = Field(default=None, description="SAS URL expiry (24h)")
    error_message: str | None = Field(default=None, description="Set when status='failed'")
    completed_at: datetime | None = Field(default=None)

    def can_transition_to(self, new_status: str) -> bool:
        """Check if a status transition is valid."""
        valid_transitions: dict[str, set[str]] = {
            "queued": {"processing"},
            "processing": {"complete", "failed"},
            "complete": set(),
            "failed": set(),
        }
        return new_status in valid_transitions.get(self.status, set())
