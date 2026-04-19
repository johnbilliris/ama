"""Unit tests for AuditExportJob state machine transitions (T030)."""

from datetime import UTC, datetime

import pytest

from packages.domain.src.domain.models.audit_export import AuditExportJob


class TestAuditExportJob:
    def _make_job(self, status="queued"):
        return AuditExportJob(
            id="export-abc123",
            tenant_id="live",
            requested_by="user-001",
            requested_at=datetime.now(UTC),
            format="csv",
            status=status,
        )

    def test_valid_queued_job(self):
        job = self._make_job()
        assert job.status == "queued"
        assert job.download_url is None
        assert job.error_message is None

    def test_queued_to_processing_allowed(self):
        job = self._make_job("queued")
        assert job.can_transition_to("processing") is True

    def test_processing_to_complete_allowed(self):
        job = self._make_job("processing")
        assert job.can_transition_to("complete") is True

    def test_processing_to_failed_allowed(self):
        job = self._make_job("processing")
        assert job.can_transition_to("failed") is True

    def test_queued_to_complete_not_allowed(self):
        job = self._make_job("queued")
        assert job.can_transition_to("complete") is False

    def test_queued_to_failed_not_allowed(self):
        job = self._make_job("queued")
        assert job.can_transition_to("failed") is False

    def test_complete_no_transitions(self):
        job = self._make_job("complete")
        assert job.can_transition_to("queued") is False
        assert job.can_transition_to("processing") is False
        assert job.can_transition_to("failed") is False

    def test_failed_no_transitions(self):
        job = self._make_job("failed")
        assert job.can_transition_to("queued") is False
        assert job.can_transition_to("processing") is False
        assert job.can_transition_to("complete") is False

    def test_download_url_only_when_complete(self):
        job = AuditExportJob(
            id="export-test",
            tenant_id="live",
            requested_by="user-001",
            requested_at=datetime.now(UTC),
            format="pdf",
            status="complete",
            download_url="https://storage.blob.core.windows.net/test/export.pdf",
            completed_at=datetime.now(UTC),
        )
        assert job.download_url is not None

    def test_queued_job_has_no_download(self):
        job = self._make_job("queued")
        assert job.download_url is None

    def test_field_constraints(self):
        with pytest.raises(Exception):
            AuditExportJob(
                id="export-test",
                tenant_id="live",
                requested_by="user-001",
                requested_at=datetime.now(UTC),
                format="csv",
                status="queued",
                record_count=-1,  # ge=0 violated
            )
