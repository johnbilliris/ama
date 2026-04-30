import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.repositories.signal_repository import SignalRepository
from app.services.simulation_audit_writer import SimulationAuditWriter

from packages.domain.src.domain.models.scenario_template import ScenarioTemplate

logger = logging.getLogger(__name__)


class ScenarioSeedingService:
    def __init__(
        self,
        signal_repository: SignalRepository,
        audit_writer: SimulationAuditWriter | None = None,
        cosmos_client: Any = None,
        warp_scheduler: Any = None,
        event_recorder: Any = None,
    ):
        self._signals = signal_repository
        self._audit = audit_writer
        self._cosmos = cosmos_client
        self._scheduler = warp_scheduler
        self._recorder = event_recorder

    async def seed_from_template(self, tenant_id: str, template_id: str, warp_speed: float = 1.0) -> dict:
        template = await self._load_template(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' not found")

        injected = 0
        timeline: list[dict[str, Any]] = []
        for entry in template.signal_timeline:
            envelope = dict(entry.signal_envelope)
            envelope["signal_id"] = f"sig-{uuid4().hex[:12]}"
            envelope["scope"] = tenant_id
            envelope["source_context"] = "simulation"
            envelope["offset_seconds"] = entry.offset_seconds
            await self._signals.create_signal(tenant_id, envelope)
            timeline.append(
                {
                    "offset_seconds": entry.offset_seconds,
                    "signal_envelope": envelope,
                }
            )
            injected += 1

        if self._scheduler is not None:
            self._scheduler.initialize(tenant_id, timeline, warp_speed=warp_speed)

        if self._audit:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="signal_write",
                actor_id="system",
                resource_id=template_id,
                details={
                    "action": "seed_from_template",
                    "signals_injected": injected,
                    "warp_speed": warp_speed,
                },
            )

        logger.info(
            "seeded_from_template tenant_id=%s template=%s signals=%d warp=%s",
            tenant_id,
            template_id,
            injected,
            warp_speed,
        )
        return {"template_id": template_id, "signals_injected": injected}

    async def seed_from_replay(
        self,
        tenant_id: str,
        incident_id: str,
        start: str,
        end: str,
        time_compression: float = 1.0,
    ) -> dict:
        """Copy historical signals from the live partition into the simulation partition."""
        live_signals = await self._signals.list_by_tenant("live", limit=10_000)
        source_signals = [s for s in live_signals[0] if s.get("incident_id") == incident_id]

        injected = 0
        for sig in source_signals:
            new_sig = dict(sig)
            new_sig["signal_id"] = f"sig-{uuid4().hex[:12]}"
            new_sig["scope"] = tenant_id
            new_sig["source_context"] = "simulation"
            new_sig.pop("_rid", None)
            new_sig.pop("_self", None)
            new_sig.pop("_etag", None)
            new_sig.pop("_ts", None)
            await self._signals.create_signal(tenant_id, new_sig)
            injected += 1

        if self._audit:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="signal_write",
                actor_id="system",
                resource_id=incident_id,
                details={"action": "seed_from_replay", "signals_injected": injected},
            )

        logger.info("seeded_from_replay tenant_id=%s incident=%s signals=%d", tenant_id, incident_id, injected)
        return {"incident_id": incident_id, "signals_injected": injected}

    async def replay_realtime(
        self,
        tenant_id: str,
        template_id: str,
        time_multiplier: float = 1.0,
    ) -> dict:
        """Schedule signal injection following real-time offsets with optional compression."""
        template = await self._load_template(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' not found")

        injected = 0
        datetime.now(UTC)
        for entry in template.signal_timeline:
            delay = entry.offset_seconds / time_multiplier if time_multiplier > 0 else 0
            if delay > 0:
                await asyncio.sleep(delay)
            envelope = dict(entry.signal_envelope)
            envelope["signal_id"] = f"sig-{uuid4().hex[:12]}"
            envelope["scope"] = tenant_id
            envelope["source_context"] = "simulation"
            await self._signals.create_signal(tenant_id, envelope)
            injected += 1

        logger.info(
            "replay_realtime_complete tenant_id=%s template=%s signals=%d multiplier=%s",
            tenant_id,
            template_id,
            injected,
            time_multiplier,
        )
        return {"template_id": template_id, "signals_injected": injected, "mode": "realtime"}

    async def _load_template(self, template_id: str) -> ScenarioTemplate | None:
        if self._cosmos:
            try:
                db = self._cosmos.get_database_client("disaster-hub")
                container = db.get_container_client("seed")
                query = "SELECT * FROM c WHERE c.template_id = @tid AND c.document_type = 'scenario_template'"
                items = list(container.query_items(query, parameters=[{"name": "@tid", "value": template_id}]))
                if items:
                    return ScenarioTemplate.model_validate(items[0])
            except Exception:
                logger.warning("template_load_failed template_id=%s", template_id, exc_info=True)
        return None
