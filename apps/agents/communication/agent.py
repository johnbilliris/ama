"""Communication Agent — FastAPI application with health, approval, and delivery endpoints.

Integrates all pipeline components: config, dedup, templates, translator,
segmenter, version counter, audit writer, delivery service, approval workflow.

Port: 8084 (following: monitoring=8080, risk=8081, evacuation=8082, resource=8083)
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import ParamSpec, TypeVar

from common.entra_principal import (
    AuthenticatedPrincipal,
    EntraPrincipalResolver,
    require_commander,
    require_handoff_producer,
)
from common.handoffs import AgentHandoffEvent
from communication.approval import ApprovalConflictError, ApprovalNotificationError, ApprovalWorkflow
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.delivery import ApprovalRequiredError
from communication.health import DependencyHealthReporter
from communication.models import (
    CommunicationDecisionRecord,
    CommunicationDecisionType,
    PublicAlert,
)
from communication.pipeline import CommunicationProcessingPipeline
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_P = ParamSpec("_P")
_T = TypeVar("_T")


class AdmissionRejectedError(RuntimeError):
    """Raised when the bounded communication worker pool is full."""


class BoundedAdmissionController:
    """Reject excess work immediately and run admitted blocking work off-loop."""

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._active = 0
        self._lock = asyncio.Lock()

    @property
    def active(self) -> int:
        return self._active

    async def run(self, func: Callable[_P, _T], /, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        async with self._lock:
            if self._active >= self._limit:
                raise AdmissionRejectedError("Communication processing capacity is full")
            self._active += 1
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        finally:
            async with self._lock:
                self._active -= 1


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    """POST body for approve/reject endpoints."""

    user_id: str | None = None
    role: str | None = None
    justification: str | None = None


class ModifyRequest(BaseModel):
    """POST body for modify endpoint."""

    user_id: str | None = None
    role: str | None = None
    modifications: dict[str, object] = Field(default_factory=dict)


class CancelRequest(BaseModel):
    """POST body for cancel endpoint."""

    user_id: str | None = None
    role: str | None = None
    reason: str = ""


class ApprovalResponse(BaseModel):
    """Response for approval actions."""

    alert_id: str
    status: str
    action: str
    user_id: str
    timestamp: str
    audit_record_id: str = ""


class HealthCheck(BaseModel):
    """Health check sub-component."""

    status: str
    latency_ms: float | None = None
    last_checked: str | None = None


class HealthResponse(BaseModel):
    """GET /health response."""

    status: str
    agent: str = "communication"
    version: str = ""
    timestamp: str = ""
    checks: dict[str, HealthCheck] = Field(default_factory=dict)
    operational: dict[str, object] = Field(default_factory=dict)
    config_hash: str = ""


class DeliveryStatusResponse(BaseModel):
    """GET /alerts/{alert_id}/delivery-status response."""

    alert_id: str
    overall_status: str
    delivery_summary: dict[str, object] = Field(default_factory=dict)
    by_channel: dict[str, list[dict[str, object]]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# FastAPI Application Factory
# ---------------------------------------------------------------------------


def create_app(
    config: CommunicationConfig | None = None,
    pipeline: CommunicationProcessingPipeline | None = None,
    approval_workflow: ApprovalWorkflow | None = None,
    audit_writer: AuditWriter | None = None,
    principal_resolver: Callable[[Request], AuthenticatedPrincipal | Awaitable[AuthenticatedPrincipal]] | None = None,
    health_reporter: DependencyHealthReporter | None = None,
) -> FastAPI:
    """Create the Communication Agent FastAPI application."""
    _config = config or CommunicationConfig()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        workflow = _app.state.approval_workflow
        lifecycle_task: asyncio.Task[None] | None = None
        try:
            await workflow.retry_pending_notifications()
            await workflow.recover_escalation_deadlines()
        except Exception:
            logger.exception("Approval notification recovery failed during startup")

        async def lifecycle_worker() -> None:
            while True:
                await asyncio.to_thread(workflow.expire_due_alerts)
                if _app.state.audit_writer is not None:
                    await asyncio.to_thread(_app.state.audit_writer.flush)
                await asyncio.sleep(_config.lifecycle_sweep_seconds)

        lifecycle_task = asyncio.create_task(lifecycle_worker())
        try:
            yield
        finally:
            lifecycle_task.cancel()
            await asyncio.gather(lifecycle_task, return_exceptions=True)

    app = FastAPI(
        title="Communication Agent",
        description="Multilingual alert generation, content safety, AIIMS approval, and multi-channel delivery",
        version=_config.agent_version,
        lifespan=lifespan,
    )

    admission = BoundedAdmissionController(_config.max_concurrent_alerts)

    # Store pipeline and services in app state
    app.state.config = _config
    app.state.pipeline = pipeline
    app.state.approval_workflow = approval_workflow or ApprovalWorkflow(config=_config)
    app.state.audit_writer = audit_writer or AuditWriter(config=_config)
    app.state.admission = admission
    app.state.health_reporter = health_reporter or DependencyHealthReporter({})
    resolve_principal = principal_resolver or EntraPrincipalResolver()

    async def authenticated_commander(request: Request) -> AuthenticatedPrincipal:
        resolved = resolve_principal(request)
        principal = await resolved if inspect.isawaitable(resolved) else resolved
        return require_commander(principal)

    async def authenticated_producer(request: Request) -> AuthenticatedPrincipal:
        resolved = resolve_principal(request)
        principal = await resolved if inspect.isawaitable(resolved) else resolved
        return require_handoff_producer(principal)

    def authorized_alert(alert_id: str, principal: AuthenticatedPrincipal) -> PublicAlert:
        alert = app.state.approval_workflow.get_alert(principal.tenant_id, alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        return alert

    def assert_body_identity(
        user_id: str | None,
        role: str | None,
        principal: AuthenticatedPrincipal,
    ) -> None:
        if user_id is not None and user_id != principal.subject:
            raise HTTPException(status_code=403, detail="Body user_id must match authenticated identity")
        if role is not None and not principal.has_asserted_role(role):
            raise HTTPException(status_code=403, detail="Body role must match an authenticated role")

    # -----------------------------------------------------------------------
    # GET /health
    # -----------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse)
    async def health(response: Response) -> HealthResponse:
        """Health endpoint per contracts/health-endpoint.md."""
        now = datetime.now(UTC)

        audit_status = app.state.audit_writer.get_status() if app.state.audit_writer else "unknown"
        pipeline_obj = app.state.pipeline

        probe_results = await app.state.health_reporter.check_all()
        checks = {
            name: HealthCheck(
                status=result.status,
                latency_ms=result.latency_ms,
                last_checked=result.last_checked,
            )
            for name, result in probe_results.items()
        }
        checks["audit_store"] = HealthCheck(status=audit_status)
        critical_failure = any(result.critical and result.status == "unhealthy" for result in probe_results.values())
        degraded = audit_status in {"buffering", "degraded"} or any(
            result.status in {"unhealthy", "not_configured"} for result in probe_results.values()
        )
        overall = "unhealthy" if critical_failure else "degraded" if degraded else "healthy"
        if critical_failure:
            response.status_code = 503

        operational = {
            "pending_approvals_count": (
                app.state.approval_workflow.get_pending_count() if app.state.approval_workflow else 0
            ),
            "active_deliveries_count": admission.active,
            "processing_queue_depth": 0,
            "processed_count": pipeline_obj.processed_count if pipeline_obj else 0,
            "audit_store": audit_status,
            "dedup_cache_size": 0,
        }

        return HealthResponse(
            status=overall,
            version=_config.agent_version,
            timestamp=now.isoformat(),
            checks=checks,
            operational=operational,
            config_hash=_config.compute_config_hash(),
        )

    # -----------------------------------------------------------------------
    # POST /process-handoff (for testing / direct invocation)
    # -----------------------------------------------------------------------

    @app.post("/process-handoff")
    async def process_handoff(
        event: AgentHandoffEvent,
        principal: AuthenticatedPrincipal = Depends(authenticated_producer),
    ) -> dict[str, object]:
        """Process a handoff event through the pipeline."""
        if principal.tenant_id != event.tenant_id:
            raise HTTPException(status_code=403, detail="Handoff tenant must match authenticated tenant")
        pipeline_obj = app.state.pipeline
        if pipeline_obj is None:
            raise HTTPException(status_code=503, detail="Pipeline not initialised")
        try:
            alert = await admission.run(pipeline_obj.process_handoff, event)
        except AdmissionRejectedError as exc:
            raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "5"})
        if alert is None:
            return {"status": "discarded", "reason": "Handoff rejected or duplicate"}

        return {
            "status": "created",
            "alert_id": alert.alert_id,
            "version": alert.version,
            "alert_status": alert.status.value,
            "languages": list(alert.content_blocks.keys()),
            "confidence": alert.confidence,
        }

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/approve
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/approve", response_model=ApprovalResponse)
    async def approve_alert(
        alert_id: str,
        request: ApprovalRequest,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> ApprovalResponse:
        """Approve an alert for delivery."""
        workflow = app.state.approval_workflow
        now = datetime.now(UTC)
        alert = authorized_alert(alert_id, principal)
        assert_body_identity(request.user_id, request.role, principal)

        try:
            workflow.process_approval(
                alert_id=alert_id,
                user_id=principal.subject,
                role=principal.commander_role or "commander",
                action="approve",
                tenant_id=principal.tenant_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        # Write audit
        audit_record = CommunicationDecisionRecord(
            tenant_id=alert.tenant_id,
            correlation_id=alert_id,
            alert_id=alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Approved by {principal.subject} ({principal.commander_role})",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=alert_id,
            status="approved",
            action="approve",
            user_id=principal.subject,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/reject
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/reject", response_model=ApprovalResponse)
    async def reject_alert(
        alert_id: str,
        request: ApprovalRequest,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> ApprovalResponse:
        """Reject an alert with justification."""
        if not request.justification:
            raise HTTPException(
                status_code=422,
                detail="Justification is required for rejection",
            )

        workflow = app.state.approval_workflow
        now = datetime.now(UTC)
        alert = authorized_alert(alert_id, principal)
        assert_body_identity(request.user_id, request.role, principal)

        try:
            workflow.process_approval(
                alert_id=alert_id,
                user_id=principal.subject,
                role=principal.commander_role or "commander",
                action="reject",
                justification=request.justification,
                tenant_id=principal.tenant_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        audit_record = CommunicationDecisionRecord(
            tenant_id=alert.tenant_id,
            correlation_id=alert_id,
            alert_id=alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Rejected by {principal.subject}: {request.justification}",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=alert_id,
            status="rejected",
            action="reject",
            user_id=principal.subject,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/modify
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/modify", response_model=ApprovalResponse)
    async def modify_alert(
        alert_id: str,
        request: ModifyRequest,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> ApprovalResponse:
        """Modify an alert — creates a new version."""
        workflow = app.state.approval_workflow

        # Get existing alert
        existing = authorized_alert(alert_id, principal)
        assert_body_identity(request.user_id, request.role, principal)

        try:
            new_alert = workflow.create_modified_version(
                alert=existing,
                modifications=request.modifications,
                user_id=principal.subject,
                role=principal.commander_role or "commander",
            )
            await workflow.request_approval(new_alert)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except ApprovalNotificationError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        now = datetime.now(UTC)
        audit_record = CommunicationDecisionRecord(
            tenant_id=existing.tenant_id,
            correlation_id=new_alert.alert_id,
            alert_id=new_alert.alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Modified by {principal.subject} → {new_alert.alert_id}",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=new_alert.alert_id,
            status="pending_review",
            action="modify",
            user_id=principal.subject,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/cancel
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/cancel", response_model=ApprovalResponse)
    async def cancel_alert(
        alert_id: str,
        request: CancelRequest,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> ApprovalResponse:
        """Cancel an alert from pre-delivery states."""
        workflow = app.state.approval_workflow
        now = datetime.now(UTC)
        alert = authorized_alert(alert_id, principal)
        assert_body_identity(request.user_id, request.role, principal)

        try:
            workflow.cancel_alert(
                alert_id=alert_id,
                user_id=principal.subject,
                role=principal.commander_role or "commander",
                reason=request.reason,
                tenant_id=principal.tenant_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        audit_record = CommunicationDecisionRecord(
            tenant_id=alert.tenant_id,
            correlation_id=alert_id,
            alert_id=alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Cancelled by {principal.subject}: {request.reason}",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=alert_id,
            status="cancelled",
            action="cancel",
            user_id=principal.subject,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # GET /alerts/{alert_id}
    # -----------------------------------------------------------------------

    @app.get("/alerts/{alert_id}")
    async def get_alert(
        alert_id: str,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> dict[str, object]:
        """Get full alert details."""
        alert = authorized_alert(alert_id, principal)
        return alert.model_dump(mode="json")

    # -----------------------------------------------------------------------
    # GET /alerts/{alert_id}/delivery-status
    # -----------------------------------------------------------------------

    @app.get("/alerts/{alert_id}/delivery-status", response_model=DeliveryStatusResponse)
    async def delivery_status(
        alert_id: str,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> DeliveryStatusResponse:
        """Get delivery status for an alert."""
        alert = authorized_alert(alert_id, principal)
        records = app.state.approval_workflow.get_delivery_records(principal.tenant_id, alert_id)
        counts = {
            status: sum(1 for record in records if record.delivery_status.value == status)
            for status in ("delivered", "accepted", "in_progress", "failed", "unconfigured", "pending", "skipped")
        }
        completed = counts["delivered"] + counts["accepted"] + counts["failed"] + counts["unconfigured"]
        return DeliveryStatusResponse(
            alert_id=alert_id,
            overall_status=alert.status.value,
            delivery_summary={
                "total_segments": len({record.audience_segment_id for record in records}),
                "total_deliveries": len(records),
                **counts,
                "completion_percentage": (completed / len(records) * 100.0) if records else 0.0,
            },
            by_channel={
                channel: [record.model_dump(mode="json") for record in records if record.channel.value == channel]
                for channel in sorted({record.channel.value for record in records})
            },
        )

    @app.post("/alerts/{alert_id}/deliver")
    async def deliver_alert(
        alert_id: str,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> list[dict[str, object]]:
        alert = authorized_alert(alert_id, principal)
        if app.state.pipeline is None:
            raise HTTPException(status_code=503, detail="Pipeline is not initialised")
        segments = app.state.approval_workflow.get_segments(principal.tenant_id, alert_id)
        try:
            records = await asyncio.to_thread(app.state.pipeline.deliver_approved_alert, alert, segments)
        except ApprovalRequiredError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except Exception as exc:
            logger.exception("Alert delivery failed for %s", alert_id)
            raise HTTPException(status_code=503, detail="Alert delivery is unavailable") from exc
        return [record.model_dump(mode="json") for record in records]

    @app.get("/incidents/{incident_id}/alerts")
    async def alert_history(
        incident_id: str,
        principal: AuthenticatedPrincipal = Depends(authenticated_commander),
    ) -> list[dict[str, object]]:
        alerts = app.state.approval_workflow.get_version_history(principal.tenant_id, incident_id)
        return [alert.model_dump(mode="json") for alert in alerts]

    return app


def main() -> None:
    """Retained launcher for callers using ``communication.agent`` directly."""
    from communication.runtime import main as runtime_main

    runtime_main()


if __name__ == "__main__":
    main()
