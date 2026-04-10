import logging
from datetime import UTC, datetime
from uuid import uuid4

from packages.domain.src.domain.models.simulation_tenant import (
    ResourceLimits,
    SimulationTenant,
)

from app.core.settings import get_settings
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.validators.simulation_validators import SimulationValidators

logger = logging.getLogger(__name__)


class SimulationService:
    def __init__(
        self,
        simulation_repository: SimulationRepository,
        audit_writer: SimulationAuditWriter | None = None,
        redis_client=None,
    ):
        self._repo = simulation_repository
        self._audit = audit_writer
        self._redis = redis_client
        self._validators = SimulationValidators(simulation_repository)

    async def create_tenant(
        self,
        scenario_type: str,
        jurisdictions: list[str],
        participants: list[str],
        creator_oid: str,
        scenario_template_id: str | None = None,
        resource_limits: dict | None = None,
    ) -> SimulationTenant:
        self._validators.validate_scenario_type(scenario_type)
        self._validators.validate_participants(participants, creator_oid)
        if resource_limits:
            self._validators.validate_resource_limits(
                resource_limits.get("max_signals"),
                resource_limits.get("max_recommendations"),
                resource_limits.get("max_duration_hours"),
            )
        await self._validators.validate_concurrency_limit()

        settings = get_settings()
        tenant_id = f"sim-{uuid4()}"
        scenario_id = str(uuid4())
        scenario_run_id = str(uuid4())

        limits = ResourceLimits(**(resource_limits or {}))

        tenant = SimulationTenant(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            scenario_run_id=scenario_run_id,
            scenario_type=scenario_type,
            scenario_template_id=scenario_template_id,
            created_by=creator_oid,
            created_at=datetime.now(UTC),
            ttl_hours=settings.simulation_ttl_hours,
            participants=participants,
            jurisdictions=jurisdictions,
            resource_limits=limits,
            status="provisioning",
        )

        tenant = await self._repo.create(tenant)

        await self._provision_namespace(tenant_id)

        tenant = tenant.transition_to("active")
        tenant = await self._repo.update(tenant)

        if self._audit:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="signal_write",
                actor_id=creator_oid,
                resource_id=tenant_id,
                details={"action": "tenant_created", "scenario_type": scenario_type},
            )

        logger.info("simulation_tenant_created tenant_id=%s scenario_type=%s", tenant_id, scenario_type)
        return tenant

    async def get_tenant(self, tenant_id: str) -> SimulationTenant | None:
        return await self._repo.get_by_tenant_id(tenant_id)

    async def list_tenants(
        self, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[SimulationTenant], int]:
        return await self._repo.list_by_status(status=status, limit=limit, offset=offset)

    async def archive_tenant(self, tenant_id: str) -> SimulationTenant:
        """Archive workflow: generate report, persist audit trail, clean up resources."""
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")

        if not tenant.can_transition_to("archiving"):
            raise ValueError(f"Cannot archive simulation in '{tenant.status}' status")

        tenant = tenant.transition_to("archiving")
        tenant = await self._repo.update(tenant)

        archive_uri = f"simulation/{tenant_id}/archive/"
        tenant = tenant.model_copy(update={"archive_uri": archive_uri})

        await self._cleanup_redis_namespace(tenant_id)

        tenant = tenant.transition_to("archived")
        tenant = await self._repo.update(tenant)

        logger.info("simulation_archived tenant_id=%s", tenant_id)
        return tenant

    async def check_expired_tenants(self) -> list[str]:
        """Find and auto-archive tenants past their expires_at."""
        expired = await self._repo.list_expired()
        archived_ids: list[str] = []
        for tenant in expired:
            try:
                await self.archive_tenant(tenant.tenant_id)
                archived_ids.append(tenant.tenant_id)
            except Exception:
                logger.warning("auto_archive_failed tenant_id=%s", tenant.tenant_id, exc_info=True)
        return archived_ids

    async def _provision_namespace(self, tenant_id: str) -> None:
        """Create Redis namespace reservation so keys for this tenant are isolated."""
        if self._redis:
            try:
                await self._redis.set(f"{tenant_id}:__provisioned", "1", ex=60 * 60 * 24 * 90)
            except Exception:
                logger.warning("redis_namespace_provision_failed tenant_id=%s", tenant_id, exc_info=True)

    async def _cleanup_redis_namespace(self, tenant_id: str) -> None:
        """Remove all Redis keys for an archived simulation tenant."""
        if self._redis:
            try:
                keys = []
                async for key in self._redis.scan_iter(match=f"{tenant_id}:*"):
                    keys.append(key)
                if keys:
                    await self._redis.delete(*keys)
                logger.info("redis_namespace_cleaned tenant_id=%s keys=%d", tenant_id, len(keys))
            except Exception:
                logger.warning("redis_namespace_cleanup_failed tenant_id=%s", tenant_id, exc_info=True)
