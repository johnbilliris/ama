"""Resource Allocation Agent — demand prioritisation, resource matching, and deployment planning.

Provides:
- ResourceAllocationAgent class (subclasses LLMCallMixin)
- FastAPI app factory ``create_app()`` with:
  - GET /health  (health checks)
  - POST /override (plan status transitions and resource overrides)
- ``__main__`` entrypoint on port 8083
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from common.handoffs import AgentHandoffEvent

if TYPE_CHECKING:
    from apps.agents.common.llm_mixin import LLMCallMixin
else:
    from common.llm_mixin import LLMCallMixin
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel as _BaseModel
from resource_allocation.audit import AuditWriter
from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.dedup import HandoffDeduplicator
from resource_allocation.inventory import ResourceInventoryManager
from resource_allocation.matcher import ResourceMatcher
from resource_allocation.models import (
    AllocationDecisionRecord,
    DecisionType,
    PlanStatus,
    ResourceDeploymentPlan,
    ResourceStatus,
)
from resource_allocation.pipeline import AllocationProcessingPipeline
from resource_allocation.versioning import VersionCounter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid status transitions for plan overrides
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.proposed: {
        PlanStatus.approved,
        PlanStatus.rejected,
        PlanStatus.cancelled,
        PlanStatus.superseded,
    },
    PlanStatus.approved: {
        PlanStatus.superseded,
        PlanStatus.cancelled,
    },
}

# Override action → target status mapping
_ACTION_STATUS_MAP: dict[str, PlanStatus] = {
    "approve": PlanStatus.approved,
    "reject": PlanStatus.rejected,
    "cancel": PlanStatus.cancelled,
    "reassign": PlanStatus.proposed,  # creates new version
    "add_resource": PlanStatus.proposed,
    "remove_resource": PlanStatus.proposed,
    "change_priority": PlanStatus.proposed,
}

_VALID_ACTIONS = set(_ACTION_STATUS_MAP.keys())
_AUTHORIZED_OVERRIDE_ROLES = {
    "incident_commander",
    "state_controller",
    "operations_officer",
    "logistics_officer",
}


# ---------------------------------------------------------------------------
# API models (at module level for PEP 563 compatibility)
# ---------------------------------------------------------------------------


class HealthCheck(_BaseModel):
    name: str
    status: str
    details: dict[str, object] | None = None


class HealthResponse(_BaseModel):
    status: str
    agent_version: str
    timestamp: str
    checks: list[HealthCheck]


class OverrideRequest(_BaseModel):
    plan_id: str
    action: str
    user_id: str
    role: str
    justification: str
    details: dict[str, object] | None = None


class OverrideResponse(_BaseModel):
    success: bool
    new_plan_id: str | None = None
    new_version: int | None = None
    action_applied: str
    override_record_id: str | None = None
    message: str


class ResourceAllocationAgent(LLMCallMixin):
    """Resource Allocation Agent with full pipeline and override support.

    Subclasses ``LLMCallMixin`` to get ``_generate_with_fallback()``.
    """

    def __init__(
        self,
        config: ResourceAllocationConfig | None = None,
        cosmos_plans_container: Any = None,
        cosmos_decisions_container: Any = None,
        cosmos_assessments_container: Any = None,
        cosmos_version_container: Any = None,
        inventory_path: str | None = None,
    ) -> None:
        super().__init__()  # initialises LLMCallMixin (_llm_client, _content_safety)
        self._config = config or ResourceAllocationConfig()

        # Audit writer
        self._audit = AuditWriter(
            config=self._config,
            cosmos_client=cosmos_decisions_container,
        )

        # Dedup
        self._dedup = HandoffDeduplicator(
            window_minutes=self._config.handoff_dedup_window_minutes,
        )

        # Inventory manager
        self._inventory = ResourceInventoryManager(config=self._config)
        if inventory_path:
            self._inventory.load_from_json(inventory_path)

        # Matcher
        self._matcher = ResourceMatcher(config=self._config)

        # Version counter
        self._version_counter = VersionCounter(
            cosmos_container=cosmos_version_container,
            max_retries=self._config.version_conflict_max_retries,
        )

        # Build processing pipeline
        self._pipeline = AllocationProcessingPipeline(
            config=self._config,
            dedup=self._dedup,
            inventory=self._inventory,
            matcher=self._matcher,
            version_counter=self._version_counter,
            audit_writer=self._audit,
            llm_generate_fn=self._generate_with_fallback,
            cosmos_plans_container=cosmos_plans_container,
            cosmos_assessments_container=cosmos_assessments_container,
        )

        # Cosmos refs for override endpoint
        self._cosmos_plans = cosmos_plans_container

        # Runtime metrics
        self._last_llm_latency_ms: int | None = None
        self._last_cosmos_write_ok: bool | None = None
        self._processing_queue_depth: int = 0

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process_handoff(self, handoff: AgentHandoffEvent) -> ResourceDeploymentPlan | None:
        """Delegate to the 9-stage processing pipeline."""
        return self._pipeline.process_handoff(handoff)

    def process_status_update(self, signal: dict[str, object]) -> bool:
        """Process a resource status update signal.

        Updates resource status via state machine and creates audit record.
        """
        resource_id = signal.get("resource_id")
        new_status_str = signal.get("new_status")
        location = signal.get("location")
        remaining_capacity = signal.get("remaining_capacity")

        if (
            not isinstance(resource_id, str)
            or not resource_id
            or not isinstance(new_status_str, str)
            or not new_status_str
        ):
            logger.warning("Invalid status update signal: missing or invalid resource_id or new_status")
            return False

        try:
            new_status = ResourceStatus(new_status_str)
        except ValueError:
            logger.warning("Invalid resource status: %s", new_status_str)
            return False

        resource = self._inventory.get_resource(resource_id)
        if resource is None:
            logger.warning("Resource not found: %s", resource_id)
            return False

        old_status = resource.status
        success = self._inventory.transition_status(
            resource_id=resource_id,
            new_status=new_status,
        )

        if success:
            # Update location if provided
            if location and isinstance(location, dict):
                resource.location = location

            # Update capacity if provided
            if remaining_capacity is not None:
                if not isinstance(remaining_capacity, (int, float, str)):
                    logger.warning("Invalid resource remaining_capacity: %s", remaining_capacity)
                    return False
                self._inventory.update_capacity(resource_id, int(remaining_capacity))

            # Check operational flags
            self._inventory.flag_operational_limits([resource])

            # Audit the transition
            config_hash = self._config.compute_config_hash()
            incident_id = resource.assigned_incident_id or "unknown"
            scope_key = f"live:{incident_id}"
            self._audit.write(
                AllocationDecisionRecord(
                    handoff_id=f"status-update-{resource_id}",
                    resource_id=resource_id,
                    decision_type=DecisionType.resource_status_updated,
                    decision_rationale=(
                        f"Resource {resource_id} transitioned: {old_status.value} → {new_status.value}"
                    ),
                    agent_version=self._config.agent_version,
                    configuration_version=config_hash,
                    incident_scope_key=scope_key,
                )
            )

        return success

    # ------------------------------------------------------------------
    # Properties for health endpoint
    # ------------------------------------------------------------------

    @property
    def inventory(self) -> ResourceInventoryManager:
        """Access to inventory manager."""
        return self._inventory

    @property
    def audit_writer(self) -> AuditWriter:
        """Access to audit writer."""
        return self._audit

    @property
    def config(self) -> ResourceAllocationConfig:
        """Access to configuration."""
        return self._config


# ---------------------------------------------------------------------------
# FastAPI App Factory
# ---------------------------------------------------------------------------


def create_app(
    agent: ResourceAllocationAgent | None = None,
    config: ResourceAllocationConfig | None = None,
) -> Any:
    """Create the FastAPI application with health and override endpoints."""

    cfg = config or ResourceAllocationConfig()
    app = FastAPI(
        title="Resource Allocation Agent",
        version=cfg.agent_version,
    )

    # Store agent on app state
    app.state.agent = agent
    app.state.config = cfg

    # ------------------------------------------------------------------
    # Health endpoint
    # ------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        agent_instance: ResourceAllocationAgent | None = app.state.agent
        checks = []
        overall = "healthy"

        # Inventory loaded check
        if agent_instance:
            inv_loaded = agent_instance.inventory.resource_count > 0
            checks.append(
                HealthCheck(
                    name="inventory_loaded",
                    status="healthy" if inv_loaded else "degraded",
                    details={"resource_count": agent_instance.inventory.resource_count},
                )
            )
            if not inv_loaded:
                overall = "degraded"
        else:
            checks.append(
                HealthCheck(
                    name="inventory_loaded",
                    status="unhealthy",
                    details={"error": "Agent not initialised"},
                )
            )
            overall = "unhealthy"

        # LLM connectivity (optimistic — check last status)
        checks.append(
            HealthCheck(
                name="llm_connectivity",
                status="healthy",
                details={"note": "Not actively checked — relies on fallback"},
            )
        )

        # Cosmos connectivity (check via audit status)
        if agent_instance:
            audit_status = agent_instance.audit_writer.get_status()
            cosmos_status = "healthy" if audit_status == "healthy" else "degraded"
            checks.append(
                HealthCheck(
                    name="cosmos_connectivity",
                    status=cosmos_status,
                    details={"audit_tier": audit_status},
                )
            )
            if cosmos_status != "healthy":
                overall = "degraded"
        else:
            checks.append(
                HealthCheck(
                    name="cosmos_connectivity",
                    status="unhealthy",
                )
            )
            overall = "unhealthy"

        # Audit store
        if agent_instance:
            audit_status = agent_instance.audit_writer.get_status()
            checks.append(
                HealthCheck(
                    name="audit_store",
                    status=audit_status if audit_status != "buffering" else "degraded",
                    details={
                        "tier": audit_status,
                        "buffer_depth": agent_instance.audit_writer.buffer_depth,
                    },
                )
            )

        # Utilisation metrics
        if agent_instance:
            util = agent_instance.inventory.compute_utilisation()
            checks.append(
                HealthCheck(
                    name="resource_utilisation",
                    status="healthy",
                    details=util,
                )
            )

        return HealthResponse(
            status=overall,
            agent_version=cfg.agent_version,
            timestamp=datetime.now(UTC).isoformat(),
            checks=checks,
        )

    # ------------------------------------------------------------------
    # Override endpoint
    # ------------------------------------------------------------------

    @app.post("/override", response_model=OverrideResponse)
    async def override(body: OverrideRequest) -> OverrideResponse:
        if body.action not in _VALID_ACTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {body.action}. Valid: {sorted(_VALID_ACTIONS)}",
            )

        if not body.justification.strip():
            raise HTTPException(
                status_code=400,
                detail="Justification is mandatory for all overrides",
            )
        if body.role not in _AUTHORIZED_OVERRIDE_ROLES:
            raise HTTPException(status_code=403, detail="Role is not authorized to override plans")

        agent_instance: ResourceAllocationAgent | None = app.state.agent
        if agent_instance is None:
            raise HTTPException(status_code=503, detail="Agent not initialised")
        if agent_instance._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")

        try:
            current_doc = agent_instance._cosmos_plans.read_item(
                item=body.plan_id,
                partition_key=body.plan_id,
            )
        except Exception as exc:
            exc_str = str(exc)
            if "NotFound" in exc_str or "404" in exc_str:
                raise HTTPException(status_code=404, detail=f"Plan {body.plan_id} not found")
            raise HTTPException(status_code=503, detail="Failed to load plan")

        previous_status = current_doc.get("status", "proposed")
        target_status = _ACTION_STATUS_MAP[body.action].value
        try:
            previous_status_enum = PlanStatus(previous_status)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=f"Unknown persisted status '{previous_status}'") from exc

        if target_status != previous_status:
            allowed = _VALID_TRANSITIONS.get(previous_status_enum, set())
            if PlanStatus(target_status) not in allowed:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Invalid transition: {previous_status} -> {target_status}. "
                        f"Allowed: {sorted(s.value for s in allowed)}"
                    ),
                )

        material_change = target_status != previous_status or bool(body.details)
        if not material_change:
            return OverrideResponse(
                success=False,
                action_applied=body.action,
                message="No material change; plan left unchanged",
            )

        updated_doc = dict(current_doc)
        updated_doc["status"] = target_status
        updated_doc["updated_at"] = datetime.now(UTC).isoformat()
        if body.details:
            updated_doc["override_details"] = body.details
        current_version = int(current_doc.get("version", 1))
        updated_doc["version"] = current_version + 1

        etag = current_doc.get("_etag")
        try:
            if etag is not None:
                agent_instance._cosmos_plans.replace_item(
                    item=body.plan_id,
                    body=updated_doc,
                    etag=etag,
                    match_condition="IfNotModified",
                )
            else:
                agent_instance._cosmos_plans.replace_item(
                    item=body.plan_id,
                    body=updated_doc,
                )
        except Exception as exc:
            exc_str = str(exc)
            if "PreconditionFailed" in exc_str or "412" in exc_str:
                raise HTTPException(status_code=409, detail="Stale plan version; reload and retry")
            raise HTTPException(status_code=503, detail="Failed to persist override")

        # Write audit record for override
        config_hash = cfg.compute_config_hash()
        record = AllocationDecisionRecord(
            handoff_id=f"override-{body.plan_id}",
            plan_id=body.plan_id,
            decision_type=DecisionType.override_applied,
            decision_rationale=f"Override: {body.action} by {body.user_id} ({body.role})",
            override_by_user_id=body.user_id,
            override_by_role=body.role,
            override_justification=body.justification,
            agent_version=cfg.agent_version,
            configuration_version=config_hash,
            version=updated_doc["version"],
        )
        agent_instance.audit_writer.write(record)

        return OverrideResponse(
            success=True,
            new_plan_id=body.plan_id,
            new_version=updated_doc["version"],
            action_applied=body.action,
            override_record_id=record.id,
            message=f"Override '{body.action}' applied to plan {body.plan_id}",
        )

    return app


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    from apps.console_logging import configure_console_logging, uvicorn_log_config

    configure_console_logging()
    config = ResourceAllocationConfig()
    agent = ResourceAllocationAgent(
        config=config,
        inventory_path=os.getenv(
            "INVENTORY_PATH",
            "data/resource-inventories/sample-inventory.json",
        ),
    )
    app = create_app(agent=agent, config=config)
    uvicorn.run(app, host="0.0.0.0", port=config.port, log_config=uvicorn_log_config())
