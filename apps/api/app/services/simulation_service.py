import inspect
import logging
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.async_io import run_blocking
from app.core.settings import get_settings
from app.repositories.cosmos_scope import simulation_scope
from app.repositories.simulation_repository import SimulationRepository
from app.services import state_store
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_clock_service import SimulationClockService
from app.services.simulation_event_recorder import SimulationEventRecorder
from app.services.simulation_notifier import (
    OutboxSimulationNotifier,
    SimulationNotifier,
    build_expiry_notice,
)
from app.validators.simulation_validators import SimulationValidators
from fastapi import HTTPException

from packages.domain.src.domain.models.scenario_run import ScenarioRun
from packages.domain.src.domain.models.simulation_tenant import (
    ArchiveCleanupSummary,
    ResourceLimits,
    SimulationTenant,
)
from packages.domain.src.domain.models.warp_constants import (
    DEFAULT_WARP_SPEED,
    validate_warp_speed,
)

logger = logging.getLogger(__name__)

EXPIRY_NOTICE_LEAD_HOURS = 24
ARCHIVE_LEASE_SECONDS = 600


class SimulationService:
    def __init__(
        self,
        simulation_repository: SimulationRepository,
        audit_writer: SimulationAuditWriter | None = None,
        redis_client=None,
        clock_service: SimulationClockService | None = None,
        event_recorder: SimulationEventRecorder | None = None,
        report_service=None,
        signal_repository=None,
        event_repository=None,
        resource_governor=None,
        notifier: SimulationNotifier | None = None,
    ):
        self._repo = simulation_repository
        self._audit = audit_writer
        self._redis = redis_client
        self._validators = SimulationValidators(simulation_repository)
        self._clock = clock_service or SimulationClockService()
        self._recorder = event_recorder
        self._report_service = report_service
        self._signal_repository = signal_repository
        self._event_repository = event_repository
        self._resource_governor = resource_governor
        self._notifier = notifier or OutboxSimulationNotifier(simulation_repository)
        self._expiry_worker_id = f"expiry-{uuid4().hex[:12]}"
        self._archive_worker_id = f"archive-{uuid4().hex[:12]}"

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
        settings = get_settings()
        scenario_run_id = str(uuid4())
        scenario_id = scenario_run_id
        tenant_id = simulation_scope(scenario_run_id)
        created_at = datetime.now(UTC)

        if not await self._repo.reserve_capacity(tenant_id, settings.max_concurrent_simulations):
            active = await self._repo.list_active_tenants(limit=settings.max_concurrent_simulations)
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Maximum concurrent simulations ({settings.max_concurrent_simulations}) reached",
                    "activeSimulationIds": [tenant.tenant_id for tenant in active],
                },
            )

        limits = ResourceLimits(**(resource_limits or {}))
        throttle_mode = "normal"
        throttle_quota_pct = 100
        throttle_notice = None
        if self._resource_governor is not None:
            throttle_mode, throttle_quota_pct, throttle_notice = await self._resource_governor.initial_tenant_mode()

        tenant = SimulationTenant(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            scenario_run_id=scenario_run_id,
            scenario_type=scenario_type,
            scenario_template_id=scenario_template_id,
            created_by=creator_oid,
            created_at=created_at,
            ttl_hours=settings.simulation_ttl_hours,
            participants=participants,
            jurisdictions=jurisdictions,
            resource_limits=limits,
            status="Provisioning",
            current_warp_speed=validated_warp,
            playback_status="full",
            throttle_mode=throttle_mode,
            throttle_quota_pct=throttle_quota_pct,
            throttle_notice=throttle_notice,
        )

        run = ScenarioRun(
            scenario_run_id=scenario_run_id,
            scenario_name=scenario_type,
            scenario_type=scenario_type.lower().replace(" ", "_").replace("-", "_"),
            jurisdiction_ids=jurisdictions,
            status="running",
            started_at=created_at,
            tenant_id=tenant_id,
        )
        try:
            tenant = await self._repo.create_with_run(tenant, run)
        except Exception:
            await self._repo.release_capacity(tenant_id)
            raise

        provisioned_cache_keys = await self._provision_namespace(tenant_id)
        if provisioned_cache_keys is None:
            await self._mark_provisioning_failed(tenant_id)
            raise RuntimeError("Simulation namespace provisioning failed")

        consumption = tenant.resource_consumption.model_copy(update={"cache_keys": provisioned_cache_keys})
        tenant = tenant.model_copy(update={"resource_consumption": consumption})
        tenant = tenant.transition_to("Active")
        tenant = self._clock.start_clock(tenant, warp_speed=validated_warp)
        tenant = await self._repo.update(tenant)

        if self._recorder is not None:
            await run_blocking(
                self._recorder.record_state_change,
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
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
        participant_oid: str | None = None,
    ) -> tuple[list[SimulationTenant], int]:
        return await self._repo.list_by_status(
            status=status,
            limit=limit,
            offset=offset,
            participant_oid=participant_oid,
        )

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
            await run_blocking(
                self._recorder.record_state_change,
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
            await run_blocking(
                self._recorder.record_state_change,
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
        if tenant.status not in ("Active", "Paused"):
            raise ValueError(f"Simulation must be Active or Paused to change warp speed (got '{tenant.status}')")
        if tenant.created_by != actor_oid:
            raise PermissionError("Only the simulation controller can change warp speed")
        previous = tenant.current_warp_speed
        tenant = self._clock.change_speed(tenant, new_speed)
        tenant = await self._repo.update(tenant)
        if self._recorder is not None:
            await run_blocking(
                self._recorder.record_warp_speed_change,
                tenant_id,
                tenant.accumulated_sim_seconds,
                old_speed=previous,
                new_speed=tenant.current_warp_speed,
            )
        return tenant, previous

    async def archive_tenant(self, tenant_id: str) -> SimulationTenant:
        """Resume the durable archive workflow from its last completed stage.

        A conditional cross-replica lease guarantees that a route handler, the
        startup resume pass and the expiry worker cannot produce a second report
        or manifest for the same tenant.
        """
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")
        if tenant.status == "Archived" and tenant.archive_job_state == "completed":
            return tenant
        if tenant.status != "Archiving":
            tenant = await self.begin_archive(tenant_id)
        if self._report_service is None:
            raise RuntimeError("Simulation archive requires the report service")

        lease_owner = f"{self._archive_worker_id}:{uuid4().hex[:8]}"
        if not await self._repo.claim_archive(tenant_id, lease_owner, datetime.now(UTC), ARCHIVE_LEASE_SECONDS):
            logger.info("archive_already_leased tenant_id=%s", tenant_id)
            return await self._repo.get_by_tenant_id(tenant_id) or tenant

        try:
            tenant = await self._repo.get_by_tenant_id(tenant_id) or tenant
            return await self._run_archive_stages(tenant_id, tenant)
        finally:
            await self._repo.release_archive_claim(tenant_id, lease_owner)

    async def _run_archive_stages(self, tenant_id: str, tenant: SimulationTenant) -> SimulationTenant:
        if tenant.archive_job_state == "not_started":
            await self._report_service.generate_report(tenant_id)
            tenant = await self._repo.get_by_tenant_id(tenant_id)
            if tenant is None:
                raise RuntimeError("Simulation disappeared while report was persisted")
            tenant = await self._repo.update(tenant.model_copy(update={"archive_job_state": "report_written"}))

        if tenant.archive_job_state == "report_written":
            report = await self._report_service.get_report(tenant_id)
            if report is None:
                raise RuntimeError("Persisted exercise report is unavailable during archive")
            archive_uri = await self._persist_archive_manifest(tenant_id, report)
            tenant = await self._repo.update(
                tenant.model_copy(update={"archive_uri": archive_uri, "archive_job_state": "manifest_written"})
            )

        if tenant.archive_job_state == "manifest_written":
            cleanup = await self._purge_tenant_resources(tenant_id, tenant)
            await self._repo.release_capacity(tenant_id)
            consumption = tenant.resource_consumption.model_copy(update={"cache_keys": 0})
            tenant = await self._repo.update(
                tenant.model_copy(
                    update={
                        "archive_job_state": "resources_purged",
                        "archive_cleanup": cleanup,
                        "resource_consumption": consumption,
                    }
                )
            )

        if tenant.archive_job_state == "resources_purged":
            archived_at = datetime.now(UTC)
            tenant = tenant.transition_to("Archived")
            tenant = tenant.model_copy(
                update={
                    "archive_job_state": "completed",
                    "archived_at": archived_at,
                    "delete_after": archived_at + timedelta(days=get_settings().simulation_archive_retention_days),
                }
            )
            tenant = await self._repo.update(tenant)

        if self._recorder is not None:
            await run_blocking(
                self._recorder.record_state_change,
                tenant_id,
                tenant.accumulated_sim_seconds,
                from_status="Archiving",
                to_status="Archived",
                trigger="archive",
            )

        logger.info("simulation_archived tenant_id=%s", tenant_id)
        return tenant

    async def _persist_archive_manifest(self, tenant_id: str, report) -> str:
        persist = self._report_service.persist_archive_manifest
        try:
            accepts_audit_writer = len(inspect.signature(persist).parameters) >= 3
        except (TypeError, ValueError):
            accepts_audit_writer = False
        if accepts_audit_writer:
            return await persist(tenant_id, report, self._audit)
        return await persist(tenant_id, report)

    async def _purge_tenant_resources(self, tenant_id: str, tenant: SimulationTenant) -> ArchiveCleanupSummary:
        """Delete every operational resource, then re-read to prove removal."""
        signal_repository = self._bound_signal_repository(tenant_id)
        documents_before = await self._repo.count_operational_documents(tenant_id)

        cache_keys_removed = await self._cleanup_redis_namespace(tenant_id)
        if cache_keys_removed is None:
            raise RuntimeError("Simulation Redis cleanup failed")

        signals_removed = 0
        if signal_repository is not None:
            signals_removed = await signal_repository.delete_by_tenant(tenant_id)
        events_removed = 0
        if self._event_repository is not None:
            events_removed = int(await run_blocking(self._event_repository.delete_tenant, tenant_id) or 0)
        state_store.clear_tenant_state(tenant_id)
        documents_removed = await self._repo.purge_tenant_documents(tenant_id)

        residual_signals = await signal_repository.count_by_tenant(tenant_id) if signal_repository is not None else 0
        residual_documents = await self._repo.count_operational_documents(tenant_id)
        residual_events = 0
        list_events = getattr(self._event_repository, "list_events", None)
        if list_events is not None:
            residual_events = len(await run_blocking(list_events, tenant_id) or [])

        cleanup = ArchiveCleanupSummary(
            signals_removed=signals_removed,
            documents_removed=documents_removed,
            events_removed=events_removed,
            cache_keys_removed=cache_keys_removed,
            residual_signals=residual_signals,
            residual_documents=residual_documents,
            residual_events=residual_events,
            verified=residual_signals == 0 and residual_documents == 0 and residual_events == 0,
        )
        if not cleanup.verified:
            raise RuntimeError(
                "Simulation cleanup verification failed for "
                f"{tenant_id}: signals={residual_signals} documents={residual_documents} "
                f"events={residual_events}"
            )
        logger.info(
            "simulation_cleanup_verified tenant_id=%s signals=%d documents=%d events=%d cache_keys=%d "
            "documents_seen=%d",
            tenant_id,
            signals_removed,
            documents_removed,
            events_removed,
            cache_keys_removed,
            documents_before,
        )
        return cleanup

    def _bound_signal_repository(self, tenant_id: str):
        if self._signal_repository is None:
            return None
        if hasattr(self._signal_repository, "bind"):
            return self._signal_repository.bind(tenant_id)
        return self._signal_repository

    async def begin_archive(self, tenant_id: str) -> SimulationTenant:
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")
        if tenant.status == "Archiving":
            return tenant
        if not tenant.can_transition_to("Archiving"):
            raise ValueError(f"Cannot archive simulation in '{tenant.status}' status")
        if not tenant.clock_paused:
            tenant = self._clock.pause_clock(tenant)
        tenant = tenant.transition_to("Archiving", elapsed_seconds=tenant.accumulated_sim_seconds)
        return await self._repo.update(tenant)

    async def delete_archived_tenant(self, tenant_id: str, *, actor_id: str | None = None) -> dict:
        """Remove operational tenant metadata while retaining immutable evidence.

        The report and archive manifest are never destroyed here; an authorized
        lookup record replaces the tenant document so the evidence stays
        reachable after the operational resources are gone.
        """
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")
        if tenant.status != "Archived" or tenant.archive_job_state != "completed":
            raise ValueError("Simulation must complete archive before deletion")
        if tenant.delete_after is None or datetime.now(UTC) < tenant.delete_after:
            raise PermissionError("Simulation archive retention period has not elapsed")

        deleted_at = datetime.now(UTC)
        evidence = await self._repo.record_archive_evidence(
            {
                "id": f"{tenant_id}:archive-evidence",
                "tenant_id": tenant_id,
                "scenario_id": tenant.scenario_id,
                "scenario_run_id": tenant.scenario_run_id,
                "scenario_type": tenant.scenario_type,
                "exercise_report_id": tenant.exercise_report_id,
                "exercise_report_uri": tenant.exercise_report_uri,
                "archive_uri": tenant.archive_uri,
                "participants": list(tenant.participants),
                "created_by": tenant.created_by,
                "archived_at": tenant.archived_at.isoformat() if tenant.archived_at else None,
                "deleted_at": deleted_at.isoformat(),
                "deleted_by": actor_id,
                "evidence_retained": True,
            }
        )
        await self._repo.delete(tenant_id)

        if self._audit is not None:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="lifecycle",
                actor_id=actor_id or "simulation-administrator",
                resource_id=tenant_id,
                correlation_id=f"tenant-deleted-{tenant_id}",
                details={
                    "action": "tenant_deleted",
                    "reportUri": tenant.exercise_report_uri,
                    "archiveUri": tenant.archive_uri,
                },
            )
        logger.info("simulation_tenant_deleted tenant_id=%s actor=%s", tenant_id, actor_id)
        return evidence

    async def get_archive_evidence(self, tenant_id: str) -> dict | None:
        return await self._repo.get_archive_evidence(tenant_id)

    async def check_expired_tenants(self) -> list[str]:
        return (await self.run_expiry_tick())["archived"]

    async def run_expiry_tick(self, now: datetime | None = None) -> dict[str, list[str]]:
        """Deliver due notices, then archive expired tenants that were noticed.

        Paused tenants follow the same idle policy as active ones: their idle
        clock keeps running, so pausing never exempts an exercise from expiry.
        """
        now = now or datetime.now(UTC)
        notified: list[str] = []
        notice_failures: list[str] = []
        notice_deadline = now + timedelta(hours=EXPIRY_NOTICE_LEAD_HOURS)

        # Short-TTL and already-expired tenants are included: a notice must always
        # precede automatic archive, even when the full lead time is impossible.
        for tenant in await self._repo.list_expiring(notice_deadline):
            try:
                await self._deliver_expiry_notice(tenant, now)
            except Exception:
                logger.warning("expiry_notice_failed tenant_id=%s", tenant.tenant_id, exc_info=True)
                notice_failures.append(tenant.tenant_id)
                continue
            await self._repo.update(tenant.model_copy(update={"expiry_notice_sent_at": now}))
            notified.append(tenant.tenant_id)

        archived_ids: list[str] = []
        for tenant in await self._repo.list_expired(now):
            if tenant.tenant_id in notice_failures:
                continue
            try:
                current = await self._repo.get_by_tenant_id(tenant.tenant_id)
                if current is None or current.expiry_notice_sent_at is None:
                    continue
                if not await self._repo.claim_expiry(tenant.tenant_id, self._expiry_worker_id, now):
                    continue
                await self.archive_tenant(tenant.tenant_id)
                archived_ids.append(tenant.tenant_id)
            except Exception:
                logger.warning("auto_archive_failed tenant_id=%s", tenant.tenant_id, exc_info=True)
        return {"notified": notified, "archived": archived_ids, "notice_failures": notice_failures}

    async def _deliver_expiry_notice(self, tenant: SimulationTenant, now: datetime) -> None:
        lead_time_seconds = (tenant.expires_at - now).total_seconds() if tenant.expires_at else 0.0
        notice = build_expiry_notice(tenant, now=now, lead_time_seconds=lead_time_seconds)
        await self._notifier.deliver(notice)
        if self._audit is not None:
            await self._audit.write_event(
                tenant_id=tenant.tenant_id,
                action="lifecycle",
                actor_id="simulation-expiry-worker",
                resource_id=tenant.tenant_id,
                correlation_id=f"expiry-notice-{tenant.tenant_id}-{notice['expires_at']}",
                details={
                    "action": "expiry_notice",
                    "expiresAt": notice["expires_at"],
                    "recipients": notice["recipients"],
                    "advanceNoticeMet": notice["advance_notice_met"],
                },
            )

    async def _mark_provisioning_failed(self, tenant_id: str) -> None:
        """Free the concurrency slot held by a tenant whose namespace never came up."""
        await self._repo.release_capacity(tenant_id)
        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is not None and tenant.provisioning_failed_at is None:
            await self._repo.update(tenant.model_copy(update={"provisioning_failed_at": datetime.now(UTC)}))

    async def _provision_namespace(self, tenant_id: str) -> int | None:
        """Reserve the Redis namespace. Returns cache keys created, or ``None`` on failure."""
        if self._redis is None:
            environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev").lower()
            return 0 if environment not in {"production", "staging"} else None
        try:
            result = await self._redis.set(f"{tenant_id}:__provisioned", "1", ex=60 * 60 * 24 * 90)
        except Exception:
            logger.warning("redis_namespace_provision_failed tenant_id=%s", tenant_id, exc_info=True)
            return None
        return None if result is False else 1

    async def _cleanup_redis_namespace(self, tenant_id: str) -> int | None:
        """Remove all Redis keys for an archived tenant. Returns keys removed, or ``None``."""
        if self._redis:
            try:
                keys = []
                async for key in self._redis.scan_iter(match=f"{tenant_id}:*"):
                    keys.append(key)
                if keys:
                    await self._redis.delete(*keys)
                logger.info("redis_namespace_cleaned tenant_id=%s keys=%d", tenant_id, len(keys))
                return len(keys)
            except Exception:
                logger.warning("redis_namespace_cleanup_failed tenant_id=%s", tenant_id, exc_info=True)
                return None
        return 0
