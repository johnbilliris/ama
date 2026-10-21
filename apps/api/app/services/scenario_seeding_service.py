import json
import logging
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.core.async_io import gather_bounded, run_blocking
from app.repositories.signal_repository import SignalRepository
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_signal_adapter import template_entry_to_signal

from packages.domain.src.domain.models.scenario_template import ScenarioTemplate

logger = logging.getLogger(__name__)

_CURATED_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[4]
    / "packages"
    / "domain"
    / "src"
    / "domain"
    / "seed"
    / "scenario_templates_australia.json"
)


class ScenarioSeedingService:
    def __init__(
        self,
        signal_repository: SignalRepository,
        audit_writer: SimulationAuditWriter | None = None,
        cosmos_client: Any = None,
        simulation_repository: Any = None,
        replay_source_repository: Any = None,
        warp_scheduler: Any = None,
        event_recorder: Any = None,
    ):
        if signal_repository is None:
            raise ValueError("ScenarioSeedingService requires a signal_repository")
        self._signals = signal_repository
        self._audit = audit_writer
        self._cosmos = cosmos_client
        self._simulation_repository = simulation_repository
        self._replay_source = replay_source_repository or signal_repository
        self._scheduler = warp_scheduler
        self._recorder = event_recorder

    async def _start_delivery_loop(self, tenant_id: str) -> bool:
        """Start scheduled delivery without a blocking store read on the loop.

        ``asyncio.create_task`` needs the caller's running loop, so only the
        cache-miss timeline read is offloaded; schedulers without the async
        entry point (test doubles) keep the direct call.
        """
        starter = getattr(self._scheduler, "start_delivery_loop_async", None)
        if starter is not None:
            return bool(await starter(tenant_id))
        return bool(self._scheduler.start_delivery_loop(tenant_id))

    async def seed_from_template(self, tenant_id: str, template_id: str, warp_speed: float = 1.0) -> dict[str, object]:
        template = await self._load_template(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' not found")

        injected = 0
        timeline: list[dict[str, Any]] = []
        exercise_start = datetime.now(UTC)
        for entry in template.signal_timeline:
            signal = template_entry_to_signal(
                entry.signal_envelope,
                tenant_id=tenant_id,
                offset_seconds=entry.offset_seconds,
                exercise_start=exercise_start,
            )
            timeline.append(
                {
                    "offset_seconds": entry.offset_seconds,
                    "signal_envelope": signal.model_dump(mode="json"),
                }
            )
            injected += 1

        if self._scheduler is not None:
            await run_blocking(self._scheduler.initialize, tenant_id, timeline, warp_speed=warp_speed)
            await self._start_delivery_loop(tenant_id)

        await self._persist_template_context(tenant_id, template)

        if self._audit:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="signal_write",
                actor_id="system",
                resource_id=template_id,
                details={
                    "action": "seed_from_template",
                    "signals_scheduled": injected,
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
        return {
            "template_id": template_id,
            "signals_injected": 0,
            "signals_scheduled": injected,
            "organisations_seeded": len(template.seed_organisations),
            "frameworks_seeded": len(template.seed_framework_ids),
            "jurisdictions_seeded": len(template.seed_jurisdictions),
        }

    async def seed_for_hazard(self, tenant_id: str, hazard: str, warp_speed: float = 1.0) -> dict[str, object]:
        expected_type = {
            "storm": "severe storm",
            "heat": "heatwave",
        }.get(hazard.lower(), hazard.lower())
        template = next(
            (
                candidate
                for candidate in self._load_curated_templates()
                if candidate.scenario_type.lower() == expected_type
            ),
            None,
        )
        if template is None:
            raise ValueError(f"No curated scenario template for hazard '{hazard}'")
        return await self.seed_from_template(tenant_id, template.template_id, warp_speed=warp_speed)

    async def seed_from_replay(
        self,
        tenant_id: str,
        incident_id: str,
        start: str,
        end: str,
        time_compression: float = 1.0,
    ) -> dict[str, object]:
        """Copy historical signals from the live partition into the simulation partition."""
        if time_compression <= 0:
            raise ValueError("time_compression must be > 0")
        start_dt = _parse_iso(start, field="start")
        end_dt = _parse_iso(end, field="end")
        if end_dt < start_dt:
            raise ValueError("end must be greater than or equal to start")

        source_signals: list[dict[str, Any]] = []
        offset = 0
        page_size = 1000
        max_snapshot_signals = 10_000
        while offset < max_snapshot_signals:
            page, total = await self._replay_source.list_by_tenant(
                "live",
                limit=min(page_size, max_snapshot_signals - offset),
                offset=offset,
            )
            if not page:
                break
            for signal in page:
                if str(signal.get("incident_id", "")) != incident_id:
                    continue
                signal_time = _resolve_signal_time(signal)
                if signal_time is None:
                    continue
                if signal_time < start_dt or signal_time > end_dt:
                    continue
                source_signals.append(deepcopy(signal))
            offset += len(page)
            if offset >= total:
                break

        source_signals.sort(key=lambda row: _resolve_signal_time(row) or start_dt)

        remapped_incident_id = f"siminc-{uuid5(NAMESPACE_URL, f'{tenant_id}:{incident_id}')}"
        timeline = await run_blocking(
            _remap_replay_timeline,
            source_signals,
            tenant_id=tenant_id,
            remapped_incident_id=remapped_incident_id,
            start_dt=start_dt,
            time_compression=time_compression,
        )
        injected = len(timeline)

        replay_status = "full"
        if injected == 0:
            replay_status = "none"
        elif injected < len(source_signals):
            replay_status = "partial"

        if self._scheduler is not None and timeline:
            await run_blocking(self._scheduler.initialize, tenant_id, timeline, warp_speed=time_compression)
            await self._start_delivery_loop(tenant_id)

        if self._audit:
            await self._audit.write_event(
                tenant_id=tenant_id,
                action="signal_write",
                actor_id="system",
                resource_id=incident_id,
                details={
                    "action": "seed_from_replay",
                    "signals_scheduled": injected,
                    "window_start": start_dt.isoformat(),
                    "window_end": end_dt.isoformat(),
                    "time_compression": time_compression,
                    "replay_status": replay_status,
                },
            )

        logger.info("seeded_from_replay tenant_id=%s incident=%s signals=%d", tenant_id, incident_id, injected)
        return {
            "incident_id": incident_id,
            "signals_injected": 0,
            "signals_scheduled": injected,
            "window_start": start_dt.isoformat(),
            "window_end": end_dt.isoformat(),
            "time_compression": time_compression,
            "replay_status": replay_status,
            "remapped_incident_id": remapped_incident_id,
        }

    async def replay_realtime(
        self,
        tenant_id: str,
        template_id: str,
        time_multiplier: float = 1.0,
    ) -> dict[str, object]:
        """Schedule signal injection following real-time offsets with optional compression."""
        template = await self._load_template(template_id)
        if template is None:
            raise ValueError(f"Template '{template_id}' not found")

        scheduled = 0
        timeline: list[dict[str, Any]] = []
        exercise_start = datetime.now(UTC)
        for entry in template.signal_timeline:
            signal = template_entry_to_signal(
                entry.signal_envelope,
                tenant_id=tenant_id,
                offset_seconds=entry.offset_seconds,
                exercise_start=exercise_start,
            )
            timeline.append(
                {
                    "offset_seconds": entry.offset_seconds,
                    "signal_envelope": signal.model_dump(mode="json"),
                }
            )
            scheduled += 1

        if self._scheduler is None:
            raise RuntimeError("ScenarioSeedingService requires a scheduler for realtime replay")
        await run_blocking(self._scheduler.initialize, tenant_id, timeline, warp_speed=time_multiplier)
        await self._start_delivery_loop(tenant_id)

        logger.info(
            "replay_realtime_complete tenant_id=%s template=%s signals=%d multiplier=%s",
            tenant_id,
            template_id,
            scheduled,
            time_multiplier,
        )
        return {
            "template_id": template_id,
            "signals_injected": 0,
            "signals_scheduled": scheduled,
            "mode": "scheduled",
        }

    async def _load_template(self, template_id: str) -> ScenarioTemplate | None:
        if self._cosmos:
            try:
                db = self._cosmos.get_database_client("disaster-hub")
                container = db.get_container_client("seed")
                query = "SELECT * FROM c WHERE c.template_id = @tid AND c.document_type = 'scenario_template'"
                items = await run_blocking(
                    lambda: list(
                        container.query_items(
                            query,
                            parameters=[{"name": "@tid", "value": template_id}],
                            enable_cross_partition_query=True,
                        )
                    )
                )
                if items:
                    return ScenarioTemplate.model_validate(items[0])
            except Exception as exc:
                raise RuntimeError(f"Template storage unavailable for '{template_id}'") from exc
        templates = await run_blocking(self._load_curated_templates)
        return next(
            (template for template in templates if template.template_id == template_id),
            None,
        )

    @staticmethod
    def _load_curated_templates() -> list[ScenarioTemplate]:
        payload = json.loads(_CURATED_TEMPLATE_PATH.read_text(encoding="utf-8"))
        return [ScenarioTemplate.model_validate(item) for item in payload]

    async def _persist_template_context(self, tenant_id: str, template: ScenarioTemplate) -> None:
        if self._simulation_repository is None:
            return
        scenario_id = tenant_id.removeprefix("sim-")
        documents: list[dict[str, Any]] = []
        for organisation in template.seed_organisations:
            documents.append(
                {
                    "id": f"{tenant_id}:organisation:{organisation.org_id}",
                    "document_type": "simulation_seed_organisation",
                    "scenario_id": scenario_id,
                    "tenant_id": tenant_id,
                    **organisation.model_dump(mode="json"),
                }
            )
        for framework_id in template.seed_framework_ids:
            documents.append(
                {
                    "id": f"{tenant_id}:framework:{framework_id}",
                    "document_type": "simulation_seed_framework",
                    "scenario_id": scenario_id,
                    "tenant_id": tenant_id,
                    "framework_id": framework_id,
                }
            )
        documents.append(
            {
                "id": f"{tenant_id}:jurisdictions",
                "document_type": "simulation_seed_jurisdictions",
                "scenario_id": scenario_id,
                "tenant_id": tenant_id,
                "jurisdiction_ids": template.seed_jurisdictions,
            }
        )
        documents.append(
            {
                "id": f"{tenant_id}:template",
                "document_type": "simulation_seed_template",
                "scenario_id": scenario_id,
                "tenant_id": tenant_id,
                "template_id": template.template_id,
                "benchmark_targets": template.benchmark_targets.model_dump(mode="json"),
            }
        )
        await gather_bounded([self._simulation_repository.upsert_document(document) for document in documents])


def _remap_replay_timeline(
    source_signals: list[dict[str, Any]],
    *,
    tenant_id: str,
    remapped_incident_id: str,
    start_dt: datetime,
    time_compression: float,
) -> list[dict[str, Any]]:
    """Rewrite live signals into simulation-scoped timeline entries off the event loop."""
    timeline: list[dict[str, Any]] = []
    for sig in source_signals:
        new_sig = deepcopy(sig)
        new_sig["signal_id"] = f"sig-{uuid4().hex[:12]}"
        new_sig["incident_id"] = remapped_incident_id
        new_sig["incidentId"] = remapped_incident_id
        new_sig.pop("_rid", None)
        new_sig.pop("_self", None)
        new_sig.pop("_etag", None)
        new_sig.pop("_ts", None)
        occurred_dt = _resolve_signal_time(sig) or start_dt
        offset_seconds = int(max(0.0, (occurred_dt - start_dt).total_seconds() / time_compression))
        domain_signal = template_entry_to_signal(
            new_sig,
            tenant_id=tenant_id,
            offset_seconds=offset_seconds,
            exercise_start=start_dt,
        )
        timeline.append(
            {
                "offset_seconds": offset_seconds,
                "signal_envelope": domain_signal.model_dump(mode="json"),
            }
        )
    return timeline


def _parse_iso(value: str, *, field: str) -> datetime:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} must be a non-empty ISO timestamp")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc


def _resolve_signal_time(signal: dict[str, Any]) -> datetime | None:
    for field in ("occurred_at", "occurredAt", "received_at", "receivedAt"):
        raw = signal.get(field)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            continue
    return None
