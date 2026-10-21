"""AUD-023 — scheduled idle expiry with reliable, tenant-visible advance notices."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_notifier import NOTICE_DOCUMENT_TYPE, SimulationNotifier
from app.services.simulation_service import SimulationService


class _RecordingNotifier(SimulationNotifier):
    def __init__(self, failures: int = 0) -> None:
        self.delivered: list[dict] = []
        self.failures = failures

    async def deliver(self, notice: dict) -> dict:
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("notice transport unavailable")
        self.delivered.append(notice)
        return notice


class _StubReports:
    def __init__(self) -> None:
        self.report = type("Report", (), {"report_id": "rpt-expiry"})()

    async def generate_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
        return self.report

    async def get_report(self, tenant_id):  # noqa: ANN001, ANN202, ARG002
        return self.report

    async def persist_archive_manifest(self, tenant_id, report, audit_writer=None):  # noqa: ANN001, ANN202, ARG002
        return f"simulation/{tenant_id}/archive/manifest.json"


@pytest.fixture
def repo() -> SimulationRepository:
    return SimulationRepository()


def _service(repo: SimulationRepository, notifier: SimulationNotifier | None = None) -> SimulationService:
    return SimulationService(
        simulation_repository=repo,
        audit_writer=SimulationAuditWriter(),
        report_service=_StubReports(),
        notifier=notifier,
    )


async def _tenant(service: SimulationService, oid: str = "user-001"):
    return await service.create_tenant(
        scenario_type="Flood",
        jurisdictions=["nsw"],
        participants=[oid, "user-observer"],
        creator_oid=oid,
    )


async def _set_expiry(repo: SimulationRepository, tenant, expires_at: datetime, status: str | None = None):
    updates: dict = {"expires_at": expires_at, "expiry_notice_sent_at": None}
    if status is not None:
        updates["status"] = status
    return await repo.update(tenant.model_copy(update=updates))


@pytest.mark.asyncio
async def test_notice_persists_a_tenant_visible_record_with_explicit_recipients(repo):
    notifier = _RecordingNotifier()
    service = _service(repo, notifier)
    tenant = await _tenant(service)
    now = datetime.now(UTC)
    await _set_expiry(repo, tenant, now + timedelta(hours=23))

    result = await service.run_expiry_tick(now)

    assert result["notified"] == [tenant.tenant_id]
    assert len(notifier.delivered) == 1
    notice = notifier.delivered[0]
    assert notice["notice_type"] == "idle_expiry_warning"
    assert notice["coordinator_oid"] == "user-001"
    assert notice["recipients"] == ["user-001", "user-observer"]
    assert notice["document_type"] == NOTICE_DOCUMENT_TYPE


@pytest.mark.asyncio
async def test_outbox_notifier_persists_notice_document_by_default(repo):
    service = _service(repo)
    tenant = await _tenant(service)
    now = datetime.now(UTC)
    tenant = await _set_expiry(repo, tenant, now + timedelta(hours=1))

    await service.run_expiry_tick(now)

    documents = await repo.list_tenant_documents(tenant.tenant_id)
    notices = [doc for doc in documents if doc.get("document_type") == NOTICE_DOCUMENT_TYPE]
    assert len(notices) == 1
    assert notices[0]["delivery_state"] == "delivered"
    assert notices[0]["recipients"] == ["user-001", "user-observer"]


@pytest.mark.asyncio
async def test_notice_boundary_fires_at_24_hours_and_not_before(repo):
    notifier = _RecordingNotifier()
    service = _service(repo, notifier)
    tenant = await _tenant(service)
    now = datetime.now(UTC)
    tenant = await _set_expiry(repo, tenant, now + timedelta(hours=24, seconds=1))

    outside = await service.run_expiry_tick(now)
    assert outside["notified"] == []

    await _set_expiry(repo, await repo.get_by_tenant_id(tenant.tenant_id), now + timedelta(hours=24))
    inside = await service.run_expiry_tick(now)

    assert inside["notified"] == [tenant.tenant_id]
    assert notifier.delivered[0]["advance_notice_met"] is True


@pytest.mark.asyncio
async def test_short_ttl_tenant_is_noticed_before_archive(repo):
    notifier = _RecordingNotifier()
    service = _service(repo, notifier)
    tenant = await _tenant(service)
    now = datetime.now(UTC)
    await _set_expiry(repo, tenant, now - timedelta(minutes=5))

    result = await service.run_expiry_tick(now)

    assert result["notified"] == [tenant.tenant_id]
    assert result["archived"] == [tenant.tenant_id]
    assert notifier.delivered[0]["advance_notice_met"] is False
    assert (await repo.get_by_tenant_id(tenant.tenant_id)).status == "Archived"


@pytest.mark.asyncio
async def test_failed_notice_blocks_archive_and_retries_next_tick(repo):
    notifier = _RecordingNotifier(failures=1)
    service = _service(repo, notifier)
    tenant = await _tenant(service)
    now = datetime.now(UTC)
    await _set_expiry(repo, tenant, now - timedelta(minutes=5))

    first = await service.run_expiry_tick(now)

    assert first["notified"] == []
    assert first["notice_failures"] == [tenant.tenant_id]
    assert first["archived"] == []
    persisted = await repo.get_by_tenant_id(tenant.tenant_id)
    assert persisted.status == "Active"
    assert persisted.expiry_notice_sent_at is None

    second = await service.run_expiry_tick(now + timedelta(minutes=1))

    assert second["notified"] == [tenant.tenant_id]
    assert second["archived"] == [tenant.tenant_id]


@pytest.mark.asyncio
async def test_paused_tenant_keeps_idle_expiry_policy(repo):
    notifier = _RecordingNotifier()
    service = _service(repo, notifier)
    tenant = await _tenant(service)
    now = datetime.now(UTC)
    paused = await _set_expiry(repo, tenant, now - timedelta(minutes=1), status="Paused")
    assert paused.status == "Paused"

    result = await service.run_expiry_tick(now)

    assert result["notified"] == [tenant.tenant_id]
    assert result["archived"] == [tenant.tenant_id]
    assert (await repo.get_by_tenant_id(tenant.tenant_id)).status == "Archived"


@pytest.mark.asyncio
async def test_competing_workers_archive_expired_tenant_once(repo):
    worker_a = _service(repo, _RecordingNotifier())
    worker_b = _service(repo, _RecordingNotifier())
    tenant = await _tenant(worker_a)
    now = datetime.now(UTC)
    await _set_expiry(repo, tenant, now - timedelta(minutes=10))

    first = await worker_a.run_expiry_tick(now)
    second = await worker_b.run_expiry_tick(now)

    assert first["archived"] == [tenant.tenant_id]
    assert second["archived"] == []
    assert second["notified"] == []


@pytest.mark.asyncio
async def test_expiry_claim_is_conditional_across_replicas(repo):
    service = _service(repo)
    tenant = await _tenant(service)
    now = datetime.now(UTC)

    assert await repo.claim_expiry(tenant.tenant_id, "worker-a", now) is True
    assert await repo.claim_expiry(tenant.tenant_id, "worker-b", now + timedelta(seconds=1)) is False
    # The lease is stored on the tenant document, so any replica observes it.
    persisted = await repo.get_by_tenant_id(tenant.tenant_id)
    assert persisted.expiry_lease_owner == "worker-a"
    assert persisted.expiry_lease_until > now
    assert await repo.claim_expiry(tenant.tenant_id, "worker-b", now + timedelta(seconds=400)) is True
