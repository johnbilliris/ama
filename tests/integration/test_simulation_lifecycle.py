from datetime import UTC, datetime, timedelta

import pytest
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_service import SimulationService

pytestmark = pytest.mark.spec007_isolation


@pytest.fixture
def repo():
    return SimulationRepository()


@pytest.fixture
def service(repo):
    return SimulationService(simulation_repository=repo)


class TestSimulationLifecycle:
    """Full lifecycle: create → seed → operate → archive → delete."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="Bushfire",
            jurisdictions=["nsw-sw"],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "Active"
        assert tenant.elapsed_seconds == 0.0

        # UI reports 60s elapsed when pausing
        tenant = tenant.transition_to("Paused", elapsed_seconds=60.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Paused"
        assert tenant.elapsed_seconds == 60.0

        # UI reports same 60s when resuming (timer was frozen)
        tenant = tenant.transition_to("Active", elapsed_seconds=60.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Active"
        assert tenant.elapsed_seconds == 60.0

        # UI reports 90s when archiving
        tenant = tenant.transition_to("Archiving", elapsed_seconds=90.0)
        tenant = await repo.update(tenant)
        assert tenant.status == "Archiving"
        assert tenant.elapsed_seconds == 90.0

        tenant = tenant.transition_to("Archived")
        tenant = await repo.update(tenant)
        assert tenant.status == "Archived"
        assert tenant.elapsed_seconds == 90.0

        tenant = tenant.transition_to("Deleted")
        tenant = await repo.update(tenant)
        assert tenant.status == "Deleted"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self, service, repo):
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.status == "Active"

        with pytest.raises(ValueError, match="Cannot transition"):
            tenant.transition_to("Deleted")

    @pytest.mark.asyncio
    async def test_elapsed_preserved_across_pause_resume(self, service, repo):
        """Elapsed seconds sent by the UI are preserved through transitions."""
        tenant = await service.create_tenant(
            scenario_type="Flood",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        assert tenant.elapsed_seconds == 0.0

        # Pause with 120s elapsed
        tenant = tenant.transition_to("Paused", elapsed_seconds=120.0)
        assert tenant.elapsed_seconds == 120.0

        # Resume — elapsed stays at 120s (timer was paused)
        tenant = tenant.transition_to("Active", elapsed_seconds=120.0)
        assert tenant.elapsed_seconds == 120.0

        # Pause again with 180s elapsed
        tenant = tenant.transition_to("Paused", elapsed_seconds=180.0)
        assert tenant.elapsed_seconds == 180.0

        # Archive from paused with same value
        tenant = tenant.transition_to("Archiving", elapsed_seconds=180.0)
        assert tenant.elapsed_seconds == 180.0

    @pytest.mark.asyncio
    async def test_transition_without_elapsed_keeps_existing(self, service, repo):
        """Transitions that don't supply elapsed_seconds preserve the stored value."""
        tenant = await service.create_tenant(
            scenario_type="Cyclone",
            jurisdictions=[],
            participants=["user-001"],
            creator_oid="user-001",
        )
        tenant = tenant.transition_to("Paused", elapsed_seconds=50.0)
        assert tenant.elapsed_seconds == 50.0

        # Resume without explicit elapsed_seconds — should keep 50.0
        tenant = tenant.transition_to("Active")
        assert tenant.elapsed_seconds == 50.0

    @pytest.mark.asyncio
    async def test_archive_writes_evidence_before_cleanup_and_retains_metadata(self, repo):
        class _ReportService:
            def __init__(self) -> None:
                self.calls = []
                self.report = type("Report", (), {"report_id": "rpt-stable"})()

            async def generate_report(self, tenant_id):  # noqa: ANN001, ANN202
                self.calls.append("report")
                tenant = await repo.get_by_tenant_id(tenant_id)
                await repo.update(
                    tenant.model_copy(
                        update={
                            "exercise_report_id": "rpt-stable",
                            "exercise_report_uri": f"simulation/{tenant_id}/reports/rpt-stable.json",
                        }
                    )
                )
                return self.report

            async def get_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
                return self.report

            async def persist_archive_manifest(self, tenant_id, report, audit_writer=None):  # noqa: ANN001, ANN202, ARG002
                self.calls.append("manifest")
                return f"simulation/{tenant_id}/archive/manifest.json"

        reports = _ReportService()
        archive_service = SimulationService(
            simulation_repository=repo,
            report_service=reports,
            signal_repository=SignalRepository(),
            event_repository=SimulationEventRepository(),
        )
        tenant = await archive_service.create_tenant(
            scenario_type="Flood",
            jurisdictions=["nsw"],
            participants=["user-001"],
            creator_oid="user-001",
        )

        archived = await archive_service.archive_tenant(tenant.tenant_id)

        assert reports.calls == ["report", "manifest"]
        assert archived.status == "Archived"
        assert archived.archive_job_state == "completed"
        assert archived.exercise_report_id == "rpt-stable"
        assert archived.archive_uri.endswith("/archive/manifest.json")
        assert archived.delete_after > archived.archived_at

    @pytest.mark.asyncio
    async def test_archive_evidence_failure_does_not_report_archived(self, repo):
        class _FailingReports:
            async def generate_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
                raise RuntimeError("blob unavailable")

        archive_service = SimulationService(simulation_repository=repo, report_service=_FailingReports())
        tenant = await archive_service.create_tenant(
            scenario_type="Flood",
            jurisdictions=["nsw"],
            participants=["user-001"],
            creator_oid="user-001",
        )

        with pytest.raises(RuntimeError, match="blob unavailable"):
            await archive_service.archive_tenant(tenant.tenant_id)

        persisted = await repo.get_by_tenant_id(tenant.tenant_id)
        assert persisted.status == "Archiving"
        assert persisted.archive_job_state == "not_started"

    @pytest.mark.asyncio
    async def test_delete_requires_retention_then_retains_evidence(self, repo):
        class _Reports:
            def __init__(self) -> None:
                self.deleted = []

            async def delete_archive(self, tenant_id, report_uri, archive_uri):  # noqa: ANN001, ANN202
                self.deleted.append((tenant_id, report_uri, archive_uri))

        reports = _Reports()
        archive_service = SimulationService(simulation_repository=repo, report_service=reports)
        tenant = await archive_service.create_tenant(
            scenario_type="Flood",
            jurisdictions=["nsw"],
            participants=["admin-1"],
            creator_oid="admin-1",
        )
        archived_at = datetime.now(UTC)
        archived = (
            tenant.transition_to("Archiving")
            .transition_to("Archived")
            .model_copy(
                update={
                    "archive_job_state": "completed",
                    "archived_at": archived_at,
                    "delete_after": archived_at + timedelta(days=1),
                    "exercise_report_id": "rpt-retained",
                    "exercise_report_uri": "simulation/report.json",
                    "archive_uri": "simulation/manifest.json",
                }
            )
        )
        await repo.update(archived)

        with pytest.raises(PermissionError, match="retention"):
            await archive_service.delete_archived_tenant(tenant.tenant_id)

        await repo.update(archived.model_copy(update={"delete_after": archived_at - timedelta(seconds=1)}))
        await archive_service.delete_archived_tenant(tenant.tenant_id, actor_id="admin-1")

        assert await repo.get_by_tenant_id(tenant.tenant_id) is None
        # Operational deletion must not destroy immutable report/manifest evidence.
        assert reports.deleted == []
        evidence = await repo.get_archive_evidence(tenant.tenant_id)
        assert evidence is not None
        assert evidence["exercise_report_uri"] == "simulation/report.json"
        assert evidence["archive_uri"] == "simulation/manifest.json"
        assert evidence["deleted_by"] == "admin-1"
