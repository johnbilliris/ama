from uuid import uuid4

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.repositories.signal_repository import SignalRepository
from app.services.tenant_partitioning import TenantPartitioningService

pytestmark = pytest.mark.spec007_isolation


def test_tenant_scope_differs_across_agencies() -> None:
    service = TenantPartitioningService()
    nsw_fire = TenantContext(agency_id="nsw-rfs", jurisdiction_ids=("nsw",))
    vic_ses = TenantContext(agency_id="vic-ses", jurisdiction_ids=("vic",))

    nsw_scope = service.build_scope(nsw_fire, "incident")
    vic_scope = service.build_scope(vic_ses, "incident")

    assert nsw_scope["partition_key"] != vic_scope["partition_key"]
    assert nsw_scope["event_channel"] != vic_scope["event_channel"]


class TestSimulationTenantIsolation:
    """Cross-tenant leakage tests for simulation feature."""

    @pytest.fixture
    def signal_repo(self):
        return SignalRepository()

    @pytest.mark.asyncio
    async def test_simulation_signals_invisible_to_live(self, signal_repo):
        sim_tenant = f"sim-{uuid4()}"
        await signal_repo.create_signal(sim_tenant, {"signal_id": "sig-sim-001", "scope": sim_tenant})

        live_signals, _ = await signal_repo.list_by_tenant("live")
        sim_ids = [s.get("signal_id") for s in live_signals]
        assert "sig-sim-001" not in sim_ids

    @pytest.mark.asyncio
    async def test_live_signals_invisible_to_simulation(self, signal_repo):
        sim_tenant = f"sim-{uuid4()}"
        await signal_repo.create_signal("live", {"signal_id": "sig-live-001", "scope": "live"})

        sim_signals, _ = await signal_repo.list_by_tenant(sim_tenant)
        live_ids = [s.get("signal_id") for s in sim_signals]
        assert "sig-live-001" not in live_ids

    @pytest.mark.asyncio
    async def test_cross_simulation_isolation(self, signal_repo):
        sim_a = f"sim-{uuid4()}"
        sim_b = f"sim-{uuid4()}"
        await signal_repo.create_signal(sim_a, {"signal_id": "sig-a", "scope": sim_a})
        await signal_repo.create_signal(sim_b, {"signal_id": "sig-b", "scope": sim_b})

        sigs_a, _ = await signal_repo.list_by_tenant(sim_a)
        sigs_b, _ = await signal_repo.list_by_tenant(sim_b)

        ids_a = [s.get("signal_id") for s in sigs_a]
        ids_b = [s.get("signal_id") for s in sigs_b]

        assert "sig-a" in ids_a and "sig-b" not in ids_a
        assert "sig-b" in ids_b and "sig-a" not in ids_b

    @pytest.mark.asyncio
    async def test_partition_key_enforces_scope(self, signal_repo):
        sim_tenant = f"sim-{uuid4()}"
        await signal_repo.create_signal(sim_tenant, {"signal_id": "sig-pk", "scope": sim_tenant})

        signal = await signal_repo.get_signal(sim_tenant, "sig-pk")
        assert signal is not None
        assert signal.get("scope") == sim_tenant

    @pytest.mark.asyncio
    async def test_request_context_rejects_caller_supplied_foreign_scope(self, signal_repo):
        token = set_current_tenant(
            TenantContext(
                agency_id="ses-nsw",
                jurisdiction_ids=("nsw",),
                tenant_id="sim-authorized",
            )
        )
        try:
            with pytest.raises(PermissionError, match="authenticated tenant"):
                await signal_repo.create_signal("live", {"signal_id": "sig-forged"})
        finally:
            reset_current_tenant(token)

    @pytest.mark.asyncio
    async def test_constructor_binding_rejects_foreign_scope(self):
        repo = SignalRepository(tenant_id="sim-authorized")

        with pytest.raises(PermissionError, match="tenant binding"):
            await repo.list_by_tenant("sim-foreign")

    @pytest.mark.asyncio
    async def test_cosmos_point_read_propagates_service_failure(self):
        class _Container:
            def read_item(self, item, partition_key):  # noqa: ANN001, ANN201, ARG002
                raise RuntimeError("cosmos unavailable")

        class _Database:
            def get_container_client(self, name):  # noqa: ANN001, ANN201, ARG002
                return _Container()

        class _Client:
            def get_database_client(self, name):  # noqa: ANN001, ANN201, ARG002
                return _Database()

        repo = SignalRepository(cosmos_client=_Client(), tenant_id="live")

        with pytest.raises(RuntimeError, match="cosmos unavailable"):
            await repo.get_signal("live", "sig-missing", "live/nsw/source")
