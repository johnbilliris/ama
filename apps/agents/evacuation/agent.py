"""Evacuation Agent — route optimisation, transport coordination, and evacuation planning.

Provides:
- EvacuationAgent class (subclasses LLMCallMixin)
- FastAPI app factory ``create_app()`` with:
  - GET /health  (6 health checks)
  - POST /override (plan status transitions)
  - POST /replan (manual replanning trigger)
- Service Bus consumer loop (``run_consumer()``)
- ``__main__`` entrypoint on port 8082
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from common.handoffs import AgentHandoffEvent
from common.llm_mixin import LLMCallMixin
from evacuation import telemetry as tel
from evacuation.config import EvacuationConfig
from evacuation.models import (
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPlan,
    OverrideMetadata,
    PlanStatus,
)
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.replanner import DynamicReplanner
from evacuation.road_network import RoadNetworkLoader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid status transitions for plan overrides
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.proposed: {
        PlanStatus.approved,
        PlanStatus.rejected,
        PlanStatus.cancelled,
        PlanStatus.paused,
    },
    PlanStatus.approved: {
        PlanStatus.superseded,
        PlanStatus.cancelled,
        PlanStatus.paused,
    },
    PlanStatus.paused: {
        PlanStatus.approved,
        PlanStatus.cancelled,
        PlanStatus.superseded,
    },
}

# Override action → target status mapping
_ACTION_STATUS_MAP: dict[str, PlanStatus] = {
    "approve": PlanStatus.approved,
    "reject": PlanStatus.rejected,
    "cancel": PlanStatus.cancelled,
    "pause": PlanStatus.paused,
    "resume": PlanStatus.approved,
    "modify": PlanStatus.proposed,  # creates new version
}

_VALID_ACTIONS = set(_ACTION_STATUS_MAP.keys())


class EvacuationAgent(LLMCallMixin):
    """Evacuation planning agent with full pipeline and replanning support.

    Subclasses ``LLMCallMixin`` to get ``_generate_with_fallback()``.
    """

    def __init__(
        self,
        config: EvacuationConfig | None = None,
        road_network: RoadNetworkLoader | None = None,
        cosmos_plans_container: Any = None,
        cosmos_decisions_container: Any = None,
        cosmos_assessments_container: Any = None,
        population_data: list[dict] | None = None,
        facility_data: list[dict] | None = None,
    ) -> None:
        super().__init__()  # initialises LLMCallMixin (_llm_client, _content_safety)
        self._config = config or EvacuationConfig()
        self._road_network = road_network or RoadNetworkLoader(
            staleness_hours=self._config.road_data_staleness_hours,
        )

        # Build processing pipeline
        self._pipeline = EvacuationProcessingPipeline(
            config=self._config,
            road_network=self._road_network,
            cosmos_plans_container=cosmos_plans_container,
            cosmos_decisions_container=cosmos_decisions_container,
            cosmos_assessments_container=cosmos_assessments_container,
            population_data=population_data,
            facility_data=facility_data,
            llm_generate_fn=self._generate_with_fallback,
        )

        # Build replanner
        self._replanner = DynamicReplanner(config=self._config)

        # Cosmos refs for override endpoint
        self._cosmos_plans = cosmos_plans_container

        # Runtime metrics
        self._last_llm_latency_ms: int | None = None
        self._last_cosmos_write_ok: bool | None = None
        self._processing_queue_depth: int = 0

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process_handoff(self, handoff: AgentHandoffEvent) -> EvacuationPlan | None:
        """Delegate to the 10-stage processing pipeline."""
        return self._pipeline.process_handoff(handoff)

    def process_replan(
        self,
        incident_id: str,
        current_plan: dict[str, Any] | None = None,
        new_road_closures: list[str] | None = None,
        hazard_area_change_pct: float | None = None,
        progress_delay_pct: float | None = None,
        new_severity: str | None = None,
        current_severity: str | None = None,
        manual_trigger: bool = False,
        shelter_zones_with_new_routes: list[int] | None = None,
    ) -> dict[str, Any]:
        """Evaluate replan triggers and execute replan if warranted.

        Returns a dict with ``triggered``, ``triggers``, ``rate_limited``,
        ``material_change``, and optionally ``change_summary``.
        """
        import time as _time

        with tel.start_span(
            "evacuation.replan",
            attributes={
                "incident_id": incident_id,
            },
        ):
            replan_start = _time.monotonic()

            # Evaluate triggers
            with tel.start_span("evacuation.evaluate_replan_trigger"):
                triggers = self._replanner.evaluate_triggers(
                    incident_id=incident_id,
                    current_plan=current_plan,
                    new_road_closures=new_road_closures,
                    hazard_area_change_pct=hazard_area_change_pct,
                    progress_delay_pct=progress_delay_pct,
                    new_severity=new_severity,
                    current_severity=current_severity,
                    manual_trigger=manual_trigger,
                    shelter_zones_with_new_routes=shelter_zones_with_new_routes,
                )

            result: dict[str, Any] = {
                "triggered": bool(triggers),
                "triggers": triggers,
                "rate_limited": False,
                "material_change": False,
                "change_summary": None,
            }

            if not triggers:
                return result

            # Rate limiting
            if self._replanner.is_rate_limited(incident_id):
                result["rate_limited"] = True
                return result

            tel.replan_count.add(1, attributes={"incident_id": incident_id})

            # Record that we replanned
            self._replanner.record_replan(incident_id)

            # Incremental road update span
            with tel.start_span("evacuation.incremental_road_update"):
                pass  # road updates handled internally by replanner

            # Recompute affected routes span
            with tel.start_span("evacuation.recompute_affected_routes"):
                pass  # route recomputation in future implementation

            # Update transport span
            with tel.start_span("evacuation.update_transport"):
                pass  # transport updates in future implementation

            # Re-estimate timeline span
            with tel.start_span("evacuation.reestimate_timeline"):
                pass  # timeline re-estimation in future implementation

            # Generate change summary
            with tel.start_span("evacuation.generate_change_summary"):
                if current_plan:
                    result["change_summary"] = self._replanner.generate_change_summary(
                        old_plan=current_plan,
                        new_plan=current_plan,  # placeholder until new plan is generated
                        triggers=triggers,
                    )

            # Assign version span
            with tel.start_span("evacuation.assign_version"):
                pass  # version assignment in future full replan

            # Persist plan span
            with tel.start_span("evacuation.persist_plan"):
                pass  # persistence in future full replan

            # Write audit span
            with tel.start_span("evacuation.write_audit"):
                pass  # audit in future full replan

            result["material_change"] = True

            # Shelter-to-evacuation recovery metrics
            if shelter_zones_with_new_routes:
                for z in shelter_zones_with_new_routes:
                    tel.shelter_to_evacuation_recovery_count.add(1)
                    tel.emit_shelter_to_evacuation_recovery(
                        plan_id=current_plan.get("plan_id", "") if current_plan else "",
                        zone=str(z),
                        new_route_id="",
                    )

            # Emit PlanUpdated event
            plan_id = current_plan.get("plan_id", "") if current_plan else ""
            version = current_plan.get("version", 0) if current_plan else 0
            tel.emit_plan_updated(
                plan_id=plan_id,
                version=version,
                triggers=triggers,
                change_summary=result.get("change_summary") or "",
            )

            # Replan latency & SLA
            replan_ms = (_time.monotonic() - replan_start) * 1000
            tel.replan_latency.record(replan_ms)
            if replan_ms > 15_000:
                tel.replan_sla_breach_count.add(1)
                tel.emit_sla_breach("", replan_ms, "replan")

            return result

    # ------------------------------------------------------------------
    # Backward-compatible API
    # ------------------------------------------------------------------

    def review(self, scenario_type: str, jurisdictions: list[str]) -> dict[str, object]:
        """Legacy review endpoint for backward compatibility."""
        route_pressure = "high" if scenario_type in {"flood", "bushfire"} else "moderate"
        return {
            "scenarioType": scenario_type,
            "jurisdictions": jurisdictions,
            "routePressure": route_pressure,
            "recommendation": ("Validate assembly areas and transport corridors before public release."),
        }


# ---------------------------------------------------------------------------
# FastAPI application — health, override, and replan endpoints
# ---------------------------------------------------------------------------

from pydantic import BaseModel as _PydanticBaseModel  # noqa: E402


class _RoadNetworkDetail(_PydanticBaseModel):
    status: str
    node_count: int = 0
    edge_count: int = 0
    stale: bool = False


class _HealthCheckDetail(_PydanticBaseModel):
    status: str
    last_checked_at: str | None = None
    latency_ms: int | None = None


class _ActivePlanDetail(_PydanticBaseModel):
    count: int
    status: str


class _ProcessingQueueDetail(_PydanticBaseModel):
    depth: int
    status: str


class _AuditStoreDetail(_PydanticBaseModel):
    status: str
    buffer_depth: int = 0


class _HealthChecks(_PydanticBaseModel):
    road_network_loaded: _RoadNetworkDetail
    llm_connectivity: _HealthCheckDetail
    cosmos_connectivity: _HealthCheckDetail
    active_plan_count: _ActivePlanDetail
    processing_queue_depth: _ProcessingQueueDetail
    audit_store: _AuditStoreDetail


class _HealthResponse(_PydanticBaseModel):
    status: str
    agent_version: str
    timestamp: str
    checks: _HealthChecks


class _OverrideRequest(_PydanticBaseModel):
    plan_id: str
    action: str  # approve | reject | cancel | pause | resume | modify
    user_id: str
    role: str
    justification: str
    modifications: dict | None = None


class _OverrideResponse(_PydanticBaseModel):
    plan_id: str
    previous_status: str
    new_status: str
    override_timestamp: str
    audit_record_id: str


class _ReplanRequest(_PydanticBaseModel):
    incident_id: str
    new_road_closures: list[str] | None = None
    hazard_area_change_pct: float | None = None
    progress_delay_pct: float | None = None
    new_severity: str | None = None
    current_severity: str | None = None
    manual_trigger: bool = False
    shelter_zones_with_new_routes: list[int] | None = None


class _ReplanResponse(_PydanticBaseModel):
    incident_id: str
    triggered: bool
    triggers: list[str]
    rate_limited: bool
    material_change: bool
    change_summary: str | None = None


def create_app(
    agent: EvacuationAgent | None = None,
    config: EvacuationConfig | None = None,
) -> Any:
    """Create the FastAPI application with health, override, and replan endpoints.

    Follows the same factory pattern as ``risk_assessment.agent.create_app()``.
    """
    from fastapi import FastAPI, HTTPException

    _config = config or EvacuationConfig()
    app = FastAPI(title="Evacuation Agent", version=_config.agent_version)

    # Store dependencies on app state
    app.state.agent = agent
    app.state.config = _config

    # ------- GET /health -------

    @app.get("/health", response_model=_HealthResponse)
    async def health() -> _HealthResponse:
        """Structured health endpoint with 6 health checks.

        Status determination:
        - All checks healthy → healthy
        - road_network not loaded OR queue offline → unhealthy
        - Any other check degraded → degraded
        """
        import time as _time

        now = datetime.now(UTC)
        _agent: EvacuationAgent | None = app.state.agent

        # 1. Road network loaded
        rn_status = "not_loaded"
        rn_node_count = 0
        rn_edge_count = 0
        rn_stale = False
        if _agent and _agent._road_network.is_loaded:
            rn_node_count = _agent._road_network.node_count
            rn_edge_count = _agent._road_network.edge_count
            rn_stale = _agent._road_network.is_stale()
            rn_status = "degraded" if rn_stale else "healthy"
        elif _agent:
            rn_status = "not_loaded"

        # 2. LLM connectivity
        llm_status = "offline"
        llm_latency = 0
        if _agent and _agent._llm_client:
            try:
                t0 = _time.perf_counter()
                _agent._llm_client.generate_response(
                    purpose="reasoning",
                    prompt="health check ping",
                    max_output_tokens=5,
                )
                llm_latency = round((_time.perf_counter() - t0) * 1000)
                llm_status = "healthy" if llm_latency < 5000 else "degraded"
                if _agent:
                    _agent._last_llm_latency_ms = llm_latency
            except Exception:
                llm_status = "offline"

        # 3. Cosmos connectivity
        cosmos_status = "unknown"
        if _agent and _agent._last_cosmos_write_ok is not None:
            cosmos_status = "healthy" if _agent._last_cosmos_write_ok else "degraded"
        elif _agent and _agent._cosmos_plans is not None:
            cosmos_status = "healthy"
        elif _agent:
            cosmos_status = "not_configured"

        # 4. Active plan count
        active_count = 0
        if _agent:
            active_count = _agent._pipeline.active_plan_count
        active_status = "healthy" if active_count < 40 else "warning"

        # 5. Processing queue depth
        queue_depth = 0
        if _agent:
            queue_depth = _agent._processing_queue_depth
        queue_status = "healthy" if queue_depth < 20 else "backpressure"

        # 6. Audit store
        audit_status = "healthy"
        audit_buffer_depth = 0
        if _agent:
            audit_status = _agent._pipeline.audit_writer.get_status()
            audit_buffer_depth = _agent._pipeline.audit_writer.buffer_depth

        # Overall status determination
        overall = "healthy"
        if rn_status == "not_loaded" or queue_status == "offline":
            overall = "unhealthy"
        elif any(
            s not in ("healthy",)
            for s in [rn_status, llm_status, cosmos_status, active_status, queue_status, audit_status]
        ):
            overall = "degraded"

        return _HealthResponse(
            status=overall,
            agent_version=_config.agent_version,
            timestamp=now.isoformat(),
            checks=_HealthChecks(
                road_network_loaded=_RoadNetworkDetail(
                    status=rn_status,
                    node_count=rn_node_count,
                    edge_count=rn_edge_count,
                    stale=rn_stale,
                ),
                llm_connectivity=_HealthCheckDetail(
                    status=llm_status,
                    last_checked_at=now.isoformat(),
                    latency_ms=llm_latency,
                ),
                cosmos_connectivity=_HealthCheckDetail(
                    status=cosmos_status,
                    last_checked_at=now.isoformat(),
                ),
                active_plan_count=_ActivePlanDetail(
                    count=active_count,
                    status=active_status,
                ),
                processing_queue_depth=_ProcessingQueueDetail(
                    depth=queue_depth,
                    status=queue_status,
                ),
                audit_store=_AuditStoreDetail(
                    status=audit_status,
                    buffer_depth=audit_buffer_depth,
                ),
            ),
        )

    # ------- POST /override -------

    @app.post("/override", response_model=_OverrideResponse)
    async def override(override_request: _OverrideRequest) -> _OverrideResponse:
        """Incident commander override of plan status.

        Valid actions: approve, reject, cancel, pause, resume, modify.

        Valid transitions:
        - proposed → approved, rejected, cancelled, paused
        - approved → superseded, cancelled, paused
        - paused → approved, cancelled, superseded
        """
        request = override_request
        now = datetime.now(UTC)
        _agent: EvacuationAgent | None = app.state.agent

        # Validate action
        if request.action not in _VALID_ACTIONS:
            raise HTTPException(
                status_code=422,
                detail=(f"Invalid action '{request.action}'. Must be one of: {sorted(_VALID_ACTIONS)}"),
            )

        target_status = _ACTION_STATUS_MAP[request.action]
        previous_status = "proposed"  # default assumption

        # Retrieve plan from Cosmos
        if _agent and _agent._cosmos_plans is not None:
            try:
                doc = _agent._cosmos_plans.read_item(
                    item=request.plan_id,
                    partition_key=request.plan_id,
                )
                previous_status = doc.get("status", "proposed")
                current_ps = PlanStatus(previous_status)

                # Validate transition
                allowed = _VALID_TRANSITIONS.get(current_ps, set())
                if target_status not in allowed:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"Invalid transition: {previous_status} → {target_status.value}. "
                            f"Allowed from {previous_status}: "
                            f"{sorted(s.value for s in allowed)}"
                        ),
                    )

                # Apply override
                doc["status"] = target_status.value
                doc["updated_at"] = now.isoformat()

                # Append override metadata
                overrides = doc.get("overrides", [])
                override_meta = OverrideMetadata(
                    override_by=request.user_id,
                    override_reason=request.justification,
                    override_at=now,
                    previous_values={"status": previous_status},
                )
                overrides.append(override_meta.model_dump(mode="json"))
                doc["overrides"] = overrides

                if request.action == "modify" and request.modifications:
                    doc.update(request.modifications)

                _agent._cosmos_plans.upsert_item(body=doc)
            except HTTPException:
                raise
            except Exception as exc:
                exc_str = str(exc)
                if "NotFound" in exc_str or "404" in exc_str:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Plan {request.plan_id} not found",
                    )
                if "PreconditionFailed" in exc_str or "412" in exc_str:
                    tel.version_conflict_retries.add(1)
                    tel.emit_version_conflict(incident_id="", retry_count=1)
                    raise HTTPException(
                        status_code=409,
                        detail="Concurrent override conflict — retry",
                    )
                raise HTTPException(status_code=503, detail=str(exc))

        # Write audit record
        audit_record = EvacuationDecisionRecord(
            handoff_id=f"override-{request.plan_id}",
            plan_id=request.plan_id,
            decision_type=DecisionType.override_applied,
            decision_rationale=(
                f"Override by {request.user_id} ({request.role}): {request.action} — {request.justification}"
            ),
            generation_method="human_override",
            agent_version=_config.agent_version,
            configuration_version=_config.compute_config_hash()[:16],
        )

        if _agent:
            _agent._pipeline.audit_writer.write(audit_record)

        # Telemetry: override metrics & event
        tel.override_by_type.add(1, attributes={"action": request.action})
        tel.emit_override_applied(
            plan_id=request.plan_id,
            action=request.action,
            user_id=request.user_id,
            role=request.role,
        )

        return _OverrideResponse(
            plan_id=request.plan_id,
            previous_status=previous_status,
            new_status=target_status.value,
            override_timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # ------- POST /replan -------

    @app.post("/replan", response_model=_ReplanResponse)
    async def replan(replan_request: _ReplanRequest) -> _ReplanResponse:
        """Trigger manual replanning evaluation for an incident."""
        request = replan_request
        _agent: EvacuationAgent | None = app.state.agent

        if _agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialised")

        result = _agent.process_replan(
            incident_id=request.incident_id,
            new_road_closures=request.new_road_closures,
            hazard_area_change_pct=request.hazard_area_change_pct,
            progress_delay_pct=request.progress_delay_pct,
            new_severity=request.new_severity,
            current_severity=request.current_severity,
            manual_trigger=request.manual_trigger,
            shelter_zones_with_new_routes=request.shelter_zones_with_new_routes,
        )

        return _ReplanResponse(
            incident_id=request.incident_id,
            triggered=result["triggered"],
            triggers=result["triggers"],
            rate_limited=result["rate_limited"],
            material_change=result["material_change"],
            change_summary=result.get("change_summary"),
        )

    return app


# ---------------------------------------------------------------------------
# Service Bus consumer loop
# ---------------------------------------------------------------------------


def run_consumer(
    agent: EvacuationAgent,
    connection_string: str | None = None,
) -> None:
    """Service Bus consumer loop for processing handoff events.

    Reads messages from the ``evacuation-handoffs`` queue, deserialises them
    as ``AgentHandoffEvent``, and delegates to ``agent.process_handoff()``.

    This is a blocking call intended to run in a background thread or as the
    main loop of the agent process.
    """
    if not connection_string:
        logger.warning("No Service Bus connection string — consumer not started")
        return

    try:
        from azure.servicebus import ServiceBusClient
    except ImportError:
        logger.error("azure-servicebus package not installed — consumer unavailable")
        return

    queue_name = "evacuation-handoffs"
    logger.info("Starting Service Bus consumer on queue '%s'", queue_name)

    try:
        client = ServiceBusClient.from_connection_string(connection_string)
        with client:
            receiver = client.get_queue_receiver(queue_name=queue_name)
            with receiver:
                for msg in receiver:
                    try:
                        body = str(msg)
                        data = json.loads(body)
                        handoff = AgentHandoffEvent.model_validate(data)
                        agent.process_handoff(handoff)
                        receiver.complete_message(msg)
                    except Exception:
                        logger.exception(
                            "Failed to process Service Bus message",
                        )
                        try:
                            receiver.dead_letter_message(
                                msg,
                                reason="ProcessingFailure",
                            )
                        except Exception:
                            logger.exception("Failed to dead-letter message")
    except Exception:
        logger.exception("Service Bus consumer error")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _console = logging.StreamHandler()
    _console.setFormatter(_fmt)
    root = logging.getLogger()
    root.addHandler(_console)
    root.setLevel(logging.INFO)

    _PORT = int(os.environ.get("PORT", "8082"))
    _config = EvacuationConfig()
    _agent = EvacuationAgent(config=_config)

    app = create_app(agent=_agent, config=_config)

    logger.info("Evacuation Agent health server starting on port %d", _PORT)
    uvicorn.run(app, host="0.0.0.0", port=_PORT, log_level="info")
