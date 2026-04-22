import logging
from datetime import UTC, datetime
from uuid import uuid4

from app.core.settings import get_settings
from app.repositories.simulation_repository import SimulationRepository
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_clock_service import SimulationClockService
from app.services.simulation_event_recorder import SimulationEventRecorder
from app.validators.simulation_validators import SimulationValidators

from packages.domain.src.domain.models.simulation_tenant import (
    ResourceLimits,
    SimulationTenant,
)
from packages.domain.src.domain.models.warp_constants import (
    DEFAULT_WARP_SPEED,
    validate_warp_speed,
)

logger = logging.getLogger(__name__)


class SimulationService:
    def __init__(
        self,
        simulation_repository: SimulationRepository,
        audit_writer: SimulationAuditWriter | None = None,
        redis_client=None,
        clock_service: SimulationClockService | None = None,
        event_recorder: SimulationEventRecorder | None = None,
    ):
        self._repo = simulation_repository
        self._audit = audit_writer
        self._redis = redis_client
        self._validators = SimulationValidators(simulation_repository)
        self._clock = clock_service or SimulationClockService()
        self._recorder = event_recorder

    async def create_tenant(
        self,
        scenario_type: str,
        jurisdictions: list[str],
        participants: list[str],
        creator_oid: str,
        scenario_template_id: str | None = None,
        resource_limits: dict | None = None,
        warp_speed: float = DEFAULT_WARP_SPEED,
    ) -> SimulationTenant:
        self._validators.validate_scenario_type(scenario_type)
        self._validators.validate_participants(participants, creator_oid)
        validated_warp = validate_warp_speed(warp_speed)
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
            status="Provisioning",
            current_warp_speed=validated_warp,
            playback_status="full",
        )

        tenant = await self._repo.create(tenant)

        await self._provision_namespace(tenant_id)

        tenant = tenant.transition_to("Active")
        tenant = self._clock.start_clock(tenant, warp_speed=validated_warp)
        tenant = await self._repo.update(tenant)

        if self._recorder is not None:
            self._recorder.record_state_change(
                tenant_id,
                0.0,
                from_status="Provisioning",
                to_status="Active",
                trigger="create",
            )

        if self._audit:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="signal_write",
                actor_id=creator_oid,
                resource_id=tenant_id,
                details={
                    "action": "tenant_created",
                    "scenario_type": scenario_type,
                    "warp_speed": validated_warp,
                },
            )

        logger.info(
            "simulation_tenant_created tenant_id=%s scenario_type=%s warp=%s",
            tenant_id,
            scenario_type,
            validated_warp,
        )
        return tenant

    async def get_tenant(self, tenant_id: str) -> SimulationTenant | None:
        return await self._repo.get_by_tenant_id(tenant_id)

    async def list_tenants(
        self, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[SimulationTenant], int]:
        return await self._repo.list_by_status(status=status, limit=limit, offset=offset)

    async def pause_tenant(self, tenant_id: str) -> SimulationTenant:
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")
        if not tenant.can_transition_to("Paused"):
            raise ValueError(f"Cannot pause simulation in '{tenant.status}' status")
        tenant = self._clock.pause_clock(tenant)
        tenant = tenant.transition_to("Paused", elapsed_seconds=tenant.accumulated_sim_seconds)
        tenant = await self._repo.update(tenant)
        if self._recorder is not None:
            self._recorder.record_state_change(
                tenant_id,
                tenant.accumulated_sim_seconds,
                from_status="Active",
                to_status="Paused",
                trigger="pause",
            )
        return tenant

    async def resume_tenant(self, tenant_id: str) -> SimulationTenant:
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")
        if not tenant.can_transition_to("Active"):
            raise ValueError(f"Cannot resume simulation in '{tenant.status}' status")
        tenant = self._clock.resume_clock(tenant)
        tenant = tenant.transition_to("Active", elapsed_seconds=tenant.accumulated_sim_seconds)
        tenant = await self._repo.update(tenant)
        if self._recorder is not None:
            self._recorder.record_state_change(
                tenant_id,
                tenant.accumulated_sim_seconds,
                from_status="Paused",
                to_status="Active",
                trigger="resume",
            )
        return tenant

    async def change_warp_speed(
        self, tenant_id: str, new_speed: float, *, actor_oid: str
    ) -> tuple[SimulationTenant, float]:
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")
        if tenant.status != "Active":
            raise ValueError(f"Simulation is not in Active status (got '{tenant.status}')")
        if tenant.created_by != actor_oid:
            raise PermissionError("Only the simulation controller can change warp speed")
        previous = tenant.current_warp_speed
        tenant = self._clock.change_speed(tenant, new_speed)
        tenant = await self._repo.update(tenant)
        if self._recorder is not None:
            self._recorder.record_warp_speed_change(
                tenant_id,
                tenant.accumulated_sim_seconds,
                old_speed=previous,
                new_speed=tenant.current_warp_speed,
            )
        return tenant, previous

    async def archive_tenant(self, tenant_id: str) -> SimulationTenant:
        """Archive workflow: generate report, persist audit trail, clean up resources."""
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")

        if not tenant.can_transition_to("Archiving"):
            raise ValueError(f"Cannot archive simulation in '{tenant.status}' status")

        if not tenant.clock_paused:
            tenant = self._clock.pause_clock(tenant)

        tenant = tenant.transition_to("Archiving", elapsed_seconds=tenant.accumulated_sim_seconds)
        tenant = await self._repo.update(tenant)

        archive_uri = f"simulation/{tenant_id}/archive/"
        tenant = tenant.model_copy(update={"archive_uri": archive_uri})

        await self._cleanup_redis_namespace(tenant_id)

        tenant = tenant.transition_to("Archived")
        tenant = await self._repo.update(tenant)

        if self._recorder is not None:
            self._recorder.record_state_change(
                tenant_id,
                tenant.accumulated_sim_seconds,
                from_status="Archiving",
                to_status="Archived",
                trigger="archive",
            )

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
