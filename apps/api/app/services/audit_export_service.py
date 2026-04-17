"""Audit export service.

Handles async generation of PDF/CSV/JSON exports from audit trail data.
Tracks export jobs with state machine (queued → processing → complete/failed).
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from packages.domain.src.domain.models.audit_export import AuditExportJob

logger = logging.getLogger("audit_export_service")

MAX_CONCURRENT_EXPORTS_PER_USER = 3


class AuditExportService:
    """Manages async audit export operations."""

    def __init__(self) -> None:
        self._jobs: dict[str, AuditExportJob] = {}
        self._user_active_counts: dict[str, int] = {}

    def create_export_job(
        self,
        *,
        format: str,
        filter_params: dict,
        record_ids: list[str],
        requested_by: str,
        tenant_id: str = "live",
    ) -> AuditExportJob:
        """Create a new export job. Raises if concurrent limit exceeded."""
        active = self._user_active_counts.get(requested_by, 0)
        if active >= MAX_CONCURRENT_EXPORTS_PER_USER:
            msg = f"Maximum {MAX_CONCURRENT_EXPORTS_PER_USER} concurrent exports per user"
            raise ValueError(msg)

        job = AuditExportJob(
            id=f"export-{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            requested_by=requested_by,
            requested_at=datetime.now(UTC),
            format=format,
            status="queued",
            filter_params=filter_params,
            record_count=len(record_ids),
        )

        self._jobs[job.id] = job
        self._user_active_counts[requested_by] = active + 1
        return job

    def get_job(self, job_id: str) -> AuditExportJob | None:
        """Get export job by ID."""
        return self._jobs.get(job_id)

    def process_export(self, job_id: str, records: list[dict]) -> AuditExportJob:
        """Process an export job (synchronous simulation of async worker)."""
        job = self._jobs.get(job_id)
        if not job:
            msg = f"Job {job_id} not found"
            raise ValueError(msg)

        # Transition to processing
        job = job.model_copy(update={"status": "processing"})
        self._jobs[job_id] = job

        try:
            if job.format == "csv":
                content = self._generate_csv(records)
            elif job.format == "json":
                content = self._generate_json(records)
            elif job.format == "pdf":
                content = self._generate_pdf_placeholder(records)
            else:
                msg = f"Unsupported format: {job.format}"
                raise ValueError(msg)

            # In production, upload to Azure Blob Storage and get SAS URL
            download_url = f"https://storage.blob.core.windows.net/governance-exports/{job_id}.{job.format}"

            job = job.model_copy(update={
                "status": "complete",
                "record_count": len(records),
                "download_url": download_url,
                "download_expires_at": datetime.now(UTC) + timedelta(hours=24),
                "completed_at": datetime.now(UTC),
            })

        except Exception as e:
            job = job.model_copy(update={
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(UTC),
            })

        self._jobs[job_id] = job

        # Decrement active count
        active = self._user_active_counts.get(job.requested_by, 1)
        self._user_active_counts[job.requested_by] = max(0, active - 1)

        return job

    def _generate_csv(self, records: list[dict]) -> str:
        """Generate CSV content from audit records."""
        if not records:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()

    def _generate_json(self, records: list[dict]) -> str:
        """Generate JSON content from audit records."""
        return json.dumps({"records": records, "count": len(records)}, indent=2, default=str)

    def _generate_pdf_placeholder(self, records: list[dict]) -> bytes:
        """Generate PDF content (placeholder — ReportLab in production)."""
        # In production, use ReportLab for formatted PDF generation
        logger.info("PDF export requested for %d records (placeholder)", len(records))
        return b"PDF placeholder content"
