"""Unit tests for AuditExportService (T049)."""

import pytest

from apps.api.app.services.audit_export_service import (
    MAX_CONCURRENT_EXPORTS_PER_USER,
    AuditExportService,
)


class TestAuditExportService:
    def setup_method(self):
        self.service = AuditExportService()

    def test_create_export_job(self):
        job = self.service.create_export_job(
            format="csv",
            filter_params={"actor": "test"},
            record_ids=["e1", "e2"],
            requested_by="user-001",
        )
        assert job.id.startswith("export-")
        assert job.status == "queued"
        assert job.format == "csv"

    def test_process_csv_export(self):
        job = self.service.create_export_job(
            format="csv",
            filter_params={},
            record_ids=[],
            requested_by="user-001",
        )
        result = self.service.process_export(
            job.id,
            [
                {"id": "1", "actor": "admin", "action": "registered"},
            ],
        )
        assert result.status == "complete"
        assert result.download_url is not None

    def test_process_json_export(self):
        job = self.service.create_export_job(
            format="json",
            filter_params={},
            record_ids=[],
            requested_by="user-001",
        )
        result = self.service.process_export(job.id, [{"test": "data"}])
        assert result.status == "complete"

    def test_process_pdf_export(self):
        job = self.service.create_export_job(
            format="pdf",
            filter_params={},
            record_ids=[],
            requested_by="user-001",
        )
        result = self.service.process_export(job.id, [])
        assert result.status == "complete"

    def test_concurrent_export_limit(self):
        user = "user-limit-test"
        for i in range(MAX_CONCURRENT_EXPORTS_PER_USER):
            self.service.create_export_job(
                format="csv",
                filter_params={},
                record_ids=[],
                requested_by=user,
            )

        with pytest.raises(ValueError, match="Maximum"):
            self.service.create_export_job(
                format="csv",
                filter_params={},
                record_ids=[],
                requested_by=user,
            )

    def test_job_status_transitions(self):
        job = self.service.create_export_job(
            format="csv",
            filter_params={},
            record_ids=[],
            requested_by="user-001",
        )
        assert job.status == "queued"
        result = self.service.process_export(job.id, [])
        assert result.status == "complete"

    def test_get_nonexistent_job(self):
        assert self.service.get_job("nonexistent") is None

    def test_process_nonexistent_job_raises(self):
        with pytest.raises(ValueError, match="not found"):
            self.service.process_export("nonexistent", [])
