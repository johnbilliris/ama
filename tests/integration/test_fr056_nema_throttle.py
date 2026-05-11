"""T-J21 — FR-056 Level-3 NEMA throttle integration test (CX-036-011).

When a Level-3 NEMA real-event is active, the simulation realm MUST
inherit spec-024's throttle behaviour (rate-limit injections, defer
cascade fan-out, etc.) per FR-056. This test asserts inheritance is
honoured end-to-end against the spec-024 throttle infrastructure
(``ResourceGovernor.declare_incident()``).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import ResourceGovernor

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant


@pytest.fixture
def repo() -> SimulationRepository:
    return SimulationRepository()


@pytest.fixture
def governor(repo: SimulationRepository) -> ResourceGovernor:
    return ResourceGovernor(simulation_repository=repo)


async def _make_tenant(repo: SimulationRepository, *, status: str = "Active") -> SimulationTenant:
    tenant_id = f"sim-{uuid4()}"
    tenant = SimulationTenant(
        tenant_id=tenant_id,
        scenario_id=str(uuid4()),
        scenario_run_id=str(uuid4()),
        scenario_type="Bushfire",
        created_by="user-001",
        participants=["user-001"],
        status=status,
    )
    await repo.create(tenant)
    return tenant


@pytest.mark.asyncio
async def test_fr056_nema_level3_throttles_active_simulations(
    governor: ResourceGovernor, repo: SimulationRepository
) -> None:
    """Declaring a NEMA Level-3 real event flips active sims to incident-throttled mode."""
    tenant = await _make_tenant(repo)
    affected = await governor.declare_incident()
    assert affected >= 1

    updated = await repo.get_by_tenant_id(tenant.tenant_id)
    assert updated is not None
    assert updated.throttle_mode == "incident-throttled"
    assert updated.throttle_quota_pct == 20  # FR-056 quota inheritance


@pytest.mark.asyncio
async def test_fr056_nema_throttle_throttles_paused_simulations_too(
    governor: ResourceGovernor, repo: SimulationRepository
) -> None:
    paused = await _make_tenant(repo, status="Paused")
    affected = await governor.declare_incident()
    assert affected >= 1

    after = await repo.get_by_tenant_id(paused.tenant_id)
    assert after is not None and after.throttle_mode == "incident-throttled"


@pytest.mark.asyncio
async def test_fr056_nema_throttle_resolution_restores_normal_quota(
    governor: ResourceGovernor, repo: SimulationRepository
) -> None:
    tenant = await _make_tenant(repo)
    await governor.declare_incident()
    restored = await governor.resolve_incident()
    assert restored >= 1
    after = await repo.get_by_tenant_id(tenant.tenant_id)
    assert after is not None
    assert after.throttle_mode == "normal"
    assert after.throttle_quota_pct == 100


@pytest.mark.asyncio
async def test_fr056_nema_throttle_blocks_writes_under_token_pressure(
    governor: ResourceGovernor, repo: SimulationRepository
) -> None:
    """Once incident-throttled, repeated writes consume 5 tokens each — bucket exhausts → False."""
    tenant = await _make_tenant(repo)
    await governor.declare_incident()
    # Drain the 1000-token bucket: 5 tokens × ~200 writes.
    allowed = 0
    blocked = 0
    for _ in range(250):
        ok = await governor.check_write_allowed(tenant.tenant_id)
        if ok:
            allowed += 1
        else:
            blocked += 1
    # Under incident-throttled, the bucket exhausts → at least some writes blocked.
    assert blocked > 0, "FR-056 NEMA throttle did NOT block any writes under sustained load"


@pytest.mark.asyncio
async def test_fr056_real_tenant_passthrough_unaffected_by_nema_throttle(
    governor: ResourceGovernor,
) -> None:
    """Live tenants (not sim-prefixed) MUST pass through regardless of NEMA throttle state."""
    await governor.declare_incident()
    assert await governor.check_write_allowed("real-NSW-RFS-001") is True
