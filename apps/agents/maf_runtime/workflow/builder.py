"""MAF Workflow builder (T043, FR-006).

Constructs the multi-agent workflow that replaces the legacy handoff graph:

::

  Monitoring → RiskAssessment → { Evacuation || ResourceAllocation } → Communication → HitlGate

The builder uses the public MAF API surface (``WorkflowBuilder``,
``Workflow``) plus our shared executor base. Checkpoints are persisted to the
SDK-backed Cosmos checkpoint storage from ``checkpoint.cosmos_checkpoint_storage``
(ADR-033-02). HITL is wired via the ``HitlGateExecutor`` from
``hitl_request_port`` (ADR-033-03).

For development / smoke testing the builder accepts overrides:
- ``checkpoint_storage`` — defaults to in-memory if Cosmos endpoint is missing.
- ``hitl_gate``           — defaults to a no-publish stub so unit tests don't
                             require Service Bus.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from agent_framework import InMemoryCheckpointStorage
from apps.console_logging import configure_console_logging

from ..repositories.workflow_run_repository import WorkflowRunRepository
from .executors import (
    CommunicationExecutor,
    EvacuationExecutor,
    MonitoringExecutor,
    ResourceExecutor,
    RiskExecutor,
)
from .hitl_request_port import HitlGateExecutor
from .run_state import WorkflowRunStatus

logger = logging.getLogger(__name__)


def _build_checkpoint_storage() -> Any:
    """Return Cosmos-backed storage if configured, else in-memory (for tests / dev)."""
    if os.environ.get("AZURE_COSMOS_ENDPOINT"):
        try:
            from ..checkpoint.cosmos_checkpoint_storage import build_checkpoint_storage

            return build_checkpoint_storage()
        except Exception:  # noqa: BLE001
            logger.warning("Cosmos checkpoint init failed; falling back to in-memory storage")
    return InMemoryCheckpointStorage()


class AmaWorkflow:
    """Lightweight orchestrator over the five executors + HITL gate.

    The MAF SDK ``WorkflowBuilder`` is used for graph definition, but for the
    Phase-4 smoke surface we drive the steps directly so the test environment
    does not require a live AOAI deployment to exercise the durable-run path.
    """

    def __init__(
        self,
        *,
        repo: WorkflowRunRepository | None = None,
        checkpoint_storage: Any | None = None,
        hitl_gate: HitlGateExecutor | None = None,
    ) -> None:
        self._repo = repo or WorkflowRunRepository()
        self._checkpoints = checkpoint_storage or _build_checkpoint_storage()
        self._hitl = hitl_gate or HitlGateExecutor(repo=self._repo)
        self._monitoring = MonitoringExecutor()
        self._risk = RiskExecutor()
        self._evac = EvacuationExecutor()
        self._resource = ResourceExecutor()
        self._communication = CommunicationExecutor()

    @property
    def repository(self) -> WorkflowRunRepository:
        return self._repo

    async def run_incident(
        self,
        *,
        incident: dict[str, Any],
        tenant_id: str,
        created_by: str = "smoke-test",
    ) -> dict[str, Any]:
        """End-to-end durable run for one incident. Returns the final run document.

        The run is automatically created and reaches one of the terminal states
        ``Completed`` (no HITL — only when communication is skipped) or
        ``AwaitingApproval`` (HITL pause at the public-alert step).
        """
        incident_id = incident.get("incident_id") or f"incident-{uuid.uuid4().hex[:8]}"
        incident_clean = {**incident, "incident_id": incident_id, "tenant_id": tenant_id}
        run_doc = self._repo.create(
            incident_id=incident_id,
            current_step="monitoring",
            created_by=created_by,
            tenant_id=tenant_id,
        )
        run_id = run_doc["id"]
        correlation_id = uuid.uuid4().hex
        steps_completed: list[str] = []

        try:
            # 1. Monitoring
            monitoring_out = await self._monitoring.execute_step(
                _DuckEnvelope(incident_clean),
                correlation_id=correlation_id,
                run_id=run_id,
            )
            steps_completed.append("monitoring")
            await self._save_checkpoint(
                run_id,
                "monitoring",
                {"tenant_id": tenant_id, "output": _to_jsonable(monitoring_out)},
            )

            # 2. Risk Assessment
            risk_out = await self._risk.execute_step(
                {**incident_clean, "monitoring": _to_jsonable(monitoring_out)},
                correlation_id=correlation_id,
                run_id=run_id,
            )
            steps_completed.append("risk_assessment")
            await self._save_checkpoint(
                run_id,
                "risk_assessment",
                {"tenant_id": tenant_id, "output": _to_jsonable(risk_out)},
            )

            # 3. Evacuation || Resource Allocation (parallel)
            evac_task = self._evac.execute_step(
                {**incident_clean, "risk": _to_jsonable(risk_out)},
                correlation_id=correlation_id,
                run_id=run_id,
            )
            res_task = self._resource.execute_step(
                {**incident_clean, "risk": _to_jsonable(risk_out)},
                correlation_id=correlation_id,
                run_id=run_id,
            )
            evac_out, res_out = await asyncio.gather(evac_task, res_task)
            steps_completed.extend(["evacuation", "resource_allocation"])
            await self._save_checkpoint(
                run_id,
                "evacuation_resource",
                {
                    "tenant_id": tenant_id,
                    "evacuation": _to_jsonable(evac_out),
                    "resource_allocation": _to_jsonable(res_out),
                },
            )

            # 4. Communication (draft only — never published)
            comm_out = await self._communication.execute_step(
                {**incident_clean, "evacuation": _to_jsonable(evac_out), "resource": _to_jsonable(res_out)},
                correlation_id=correlation_id,
                run_id=run_id,
            )
            steps_completed.append("communication")
            await self._save_checkpoint(
                run_id,
                "communication",
                {"tenant_id": tenant_id, "output": _to_jsonable(comm_out)},
            )

            # 5. HITL gate — pauses workflow with status=AwaitingApproval
            hitl_out = await self._hitl.run(
                draft_alert=comm_out,
                incident_id=incident_id,
                run_id=run_id,
                step_index=len(steps_completed),
                correlation_id=correlation_id,
                tenant_id=tenant_id,
            )
            final_doc = dict(self._repo.get(run_id, tenant_id=tenant_id) or run_doc)
            final_doc["workflow_outputs"] = {
                "correlation_id": correlation_id,
                "monitoring": _to_jsonable(monitoring_out),
                "risk_assessment": _to_jsonable(risk_out),
                "evacuation": _to_jsonable(evac_out),
                "resource_allocation": _to_jsonable(res_out),
                "communication": _to_jsonable(comm_out),
                "hitl": _to_jsonable(hitl_out),
            }
            return final_doc

        except Exception:  # noqa: BLE001
            logger.exception("workflow run failed run_id=%s steps_completed=%s", run_id, steps_completed)
            self._repo.update_status(
                run_id,
                WorkflowRunStatus.FAILED,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                failure_reason={
                    "reason_code": "workflow_step_failure",
                    "last_completed_step": steps_completed[-1] if steps_completed else "monitoring",
                    "details": "see Application Insights trace via correlation_id",
                },
            )
            raise

    async def _save_checkpoint(self, run_id: str, step_name: str, payload: dict[str, Any]) -> None:
        """Best-effort checkpoint write — skips when storage is in-memory test mode."""
        try:
            from agent_framework import WorkflowCheckpoint

            checkpoint = WorkflowCheckpoint(
                checkpoint_id=f"{run_id}-{step_name}-{uuid.uuid4().hex[:8]}",
                workflow_id=run_id,
                executor_states={"step": step_name, "payload": payload},
            )
            await self._checkpoints.save_checkpoint(checkpoint)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            logger.debug("checkpoint save skipped/failed step=%s", step_name, exc_info=True)


class _DuckEnvelope:
    """Minimal duck-typed SignalEnvelope for the legacy MonitoringAgent path."""

    def __init__(self, incident: dict[str, Any]) -> None:
        from types import SimpleNamespace

        self.envelope_id = incident.get("envelope_id") or f"env-{uuid.uuid4().hex[:8]}"
        self.incidentId = incident.get("incident_id")
        self.signalId = self.envelope_id
        self.category = incident.get("category", "fire")
        self.confidenceScore = float(incident.get("confidenceScore", 0.85))
        self.freshnessScore = float(incident.get("freshnessScore", 1.0))
        self.source = SimpleNamespace(kind=incident.get("source_kind", "social_media"))
        self.payload = incident.get("payload", {})


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    return value


# ---- CLI entrypoint --------------------------------------------------------


async def _amain(args: argparse.Namespace) -> int:
    incident: dict[str, Any] = {}
    if args.incident_fixture:
        incident = json.loads(Path(args.incident_fixture).read_text(encoding="utf-8"))
    workflow = AmaWorkflow()
    final_doc = await workflow.run_incident(incident=incident, tenant_id=args.tenant_id)
    print(json.dumps(final_doc, indent=2, sort_keys=True, default=str))
    return (
        0
        if final_doc["status"] in {WorkflowRunStatus.AWAITING_APPROVAL.value, WorkflowRunStatus.COMPLETED.value}
        else 1
    )


def main() -> int:  # pragma: no cover
    configure_console_logging()
    p = argparse.ArgumentParser()
    p.add_argument("--incident-fixture", type=str, default=None)
    p.add_argument("--tenant-id", type=str, default="live")
    args = p.parse_args()
    return asyncio.run(_amain(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["AmaWorkflow", "main"]
