"""AUD-022 — durable archive evidence, verified cleanup and retention-aware deletion."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.exercise_report_service import ExerciseReportService
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_service import SimulationService


@pytest.fixture
def repo() -> SimulationRepository:
    return SimulationRepository()


def _build_service(repo: SimulationRepository, *, audit: SimulationAuditWriter | None = None):
    audit = audit or SimulationAuditWriter()
    signals = SignalRepository()
    events = SimulationEventRepository()
    reports = ExerciseReportService(
        simulation_repository=repo,
        signal_repository=signals,
        event_repository=events,
        audit_writer=audit,
    )
    service = SimulationService(
        simulation_repository=repo,
        audit_writer=audit,
        report_service=reports,
        signal_repository=signals,
        event_repository=events,
    )
    return service, reports, signals, audit


async def _create(service: SimulationService, oid: str = "user-001"):
    return await service.create_tenant(
        scenario_type="Flood",
        jurisdictions=["nsw"],
        participants=[oid],
        creator_oid=oid,
    )


@pytest.mark.asyncio
async def test_manifest_enumerates_counts_and_checksums_tenant_audit_records(repo):
    service, reports, _signals, audit = _build_service(repo)
    tenant = await _create(service)
    for index in range(3):
        await audit.write_event(
            tenant_id=tenant.tenant_id,
            action="signal_write",
            actor_id="user-001",
            resource_id=f"sig-{index}",
            correlation_id=f"corr-{index}",
        )

    archived = await service.archive_tenant(tenant.tenant_id)
    manifest = await reports.get_archive_manifest(tenant.tenant_id)

    assert archived.status == "Archived"
    assert manifest is not None
    # tenant_created + three signal writes.
    assert manifest["auditEventCount"] == 4
    assert manifest["auditEventCount"] == len(manifest["auditEvents"])
    assert manifest["auditPrefix"] == f"audit/{tenant.tenant_id}/"
    assert len({entry["eventId"] for entry in manifest["auditEvents"]}) == 4
    assert all(len(entry["sha256"]) == 64 for entry in manifest["auditEvents"])
    assert len(manifest["auditSnapshotSha256"]) == 64


@pytest.mark.asyncio
async def test_cleanup_counts_and_post_purge_reads_precede_archived(repo):
    service, _reports, signals, _audit = _build_service(repo)
    tenant = await _create(service)
    bound = signals.bind(tenant.tenant_id)
    for index in range(4):
        await bound.create_signal(tenant.tenant_id, {"signal_id": f"sig-{index}", "category": "flood"})
    for index in range(2):
        await repo.upsert_document(
            {"id": f"{tenant.tenant_id}:seed:{index}", "tenant_id": tenant.tenant_id, "document_type": "seed"}
        )

    archived = await service.archive_tenant(tenant.tenant_id)

    assert archived.archive_cleanup is not None
    assert archived.archive_cleanup.verified is True
    assert archived.archive_cleanup.signals_removed == 4
    assert archived.archive_cleanup.documents_removed >= 2
    assert archived.archive_cleanup.residual_signals == 0
    assert archived.archive_cleanup.residual_documents == 0
    assert await bound.count_by_tenant(tenant.tenant_id) == 0
    assert await repo.count_operational_documents(tenant.tenant_id) == 0
    assert archived.resource_consumption.cache_keys == 0


@pytest.mark.asyncio
async def test_unverified_cleanup_never_reports_archived(repo):
    service, _reports, signals, _audit = _build_service(repo)
    tenant = await _create(service)

    class _LeakyRepository:
        def bind(self, tenant_id):  # noqa: ANN001, ANN202
            return self

        async def delete_by_tenant(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
            return 0

        async def count_by_tenant(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
            return 7

    service._signal_repository = _LeakyRepository()

    with pytest.raises(RuntimeError, match="cleanup verification failed"):
        await service.archive_tenant(tenant.tenant_id)

    persisted = await repo.get_by_tenant_id(tenant.tenant_id)
    assert persisted.status == "Archiving"
    assert persisted.archive_job_state == "manifest_written"
    assert signals is not None


@pytest.mark.asyncio
async def test_concurrent_archivers_produce_one_report_and_manifest(repo):
    class _CountingReports:
        def __init__(self) -> None:
            self.report_calls = 0
            self.manifest_calls = 0
            self.report = type("Report", (), {"report_id": "rpt-once"})()

        async def generate_report(self, tenant_id):  # noqa: ANN001, ANN202
            self.report_calls += 1
            await asyncio.sleep(0)
            tenant = await repo.get_by_tenant_id(tenant_id)
            await repo.update(
                tenant.model_copy(
                    update={
                        "exercise_report_id": "rpt-once",
                        "exercise_report_uri": f"simulation/{tenant_id}/reports/rpt-once.json",
                    }
                )
            )
            return self.report

        async def get_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
            return self.report

        async def persist_archive_manifest(self, tenant_id, report, audit_writer=None):  # noqa: ANN001, ANN202, ARG002
            self.manifest_calls += 1
            await asyncio.sleep(0)
            return f"simulation/{tenant_id}/archive/manifest.json"

    reports = _CountingReports()
    service = SimulationService(simulation_repository=repo, report_service=reports)
    tenant = await _create(service)

    results = await asyncio.gather(
        service.archive_tenant(tenant.tenant_id),
        service.archive_tenant(tenant.tenant_id),
    )

    assert reports.report_calls == 1
    assert reports.manifest_calls == 1
    assert any(result.status == "Archived" for result in results)
    final = await repo.get_by_tenant_id(tenant.tenant_id)
    assert final.status == "Archived"
    assert final.archive_job_state == "completed"
    assert final.archive_lease_owner is None


@pytest.mark.asyncio
async def test_archive_retains_foreign_tenant_resources(repo):
    service, _reports, signals, _audit = _build_service(repo)
    archived_tenant = await _create(service, "user-001")
    retained_tenant = await _create(service, "user-002")

    await signals.bind(retained_tenant.tenant_id).create_signal(
        retained_tenant.tenant_id, {"signal_id": "keep-1", "category": "flood"}
    )
    await repo.upsert_document(
        {
            "id": f"{retained_tenant.tenant_id}:seed:0",
            "tenant_id": retained_tenant.tenant_id,
            "document_type": "seed",
        }
    )

    await service.archive_tenant(archived_tenant.tenant_id)

    assert await signals.bind(retained_tenant.tenant_id).count_by_tenant(retained_tenant.tenant_id) == 1
    # Scenario run plus the seeded document: neither belongs to the archived tenant.
    assert await repo.count_operational_documents(retained_tenant.tenant_id) == 2
    assert await repo.get_document(document_type="seed", document_id=f"{retained_tenant.tenant_id}:seed:0")
    survivor = await repo.get_by_tenant_id(retained_tenant.tenant_id)
    assert survivor.status == "Active"


@pytest.mark.asyncio
async def test_deletion_after_retention_keeps_evidence_and_retains_other_tenants(repo):
    service, _reports, _signals, _audit = _build_service(repo)
    deleted_tenant = await _create(service, "user-001")
    retained_tenant = await _create(service, "user-002")

    await service.archive_tenant(deleted_tenant.tenant_id)
    archived = await repo.get_by_tenant_id(deleted_tenant.tenant_id)
    await repo.update(archived.model_copy(update={"delete_after": datetime.now(UTC) - timedelta(seconds=1)}))

    evidence = await service.delete_archived_tenant(deleted_tenant.tenant_id, actor_id="admin-9")

    assert await repo.get_by_tenant_id(deleted_tenant.tenant_id) is None
    assert evidence["evidence_retained"] is True
    lookup = await service.get_archive_evidence(deleted_tenant.tenant_id)
    assert lookup["archive_uri"] == archived.archive_uri
    assert lookup["exercise_report_uri"] == archived.exercise_report_uri
    assert await repo.get_by_tenant_id(retained_tenant.tenant_id) is not None
