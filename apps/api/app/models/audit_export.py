"""Audit export request/response models for the governance dashboard API."""

from pydantic import BaseModel, Field

from packages.domain.src.domain.models.audit_export import ExportFormat


class AuditExportRequest(BaseModel):
    """Request body for POST /governance/dashboard/audit/export."""

    format: ExportFormat
    filter_params: dict[str, object] = Field(default_factory=dict)
    record_ids: list[str] = Field(default_factory=list)


class AuditExportJobResponse(BaseModel):
    """Response for export job status queries."""

    id: str
    status: str
    download_url: str | None = None
    progress: float = Field(ge=0.0, le=100.0, default=0.0)
    error_message: str | None = None
