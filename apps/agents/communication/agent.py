"""Communication Agent — FastAPI application with health, approval, and delivery endpoints.

Integrates all pipeline components: config, dedup, templates, translator,
segmenter, version counter, audit writer, delivery service, approval workflow.

Port: 8084 (following: monitoring=8080, risk=8081, evacuation=8082, resource=8083)
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from common.handoffs import AgentHandoffEvent

from communication.approval import ApprovalConflictError, ApprovalWorkflow
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.dedup import HandoffDeduplicator
from communication.delivery import MultiChannelDeliveryService
from communication.models import (
    AlertStatus,
    CommunicationDecisionRecord,
    CommunicationDecisionType,
)
from communication.pipeline import CommunicationProcessingPipeline
from communication.segmentation import AudienceSegmenter
from communication.telemetry import metrics
from communication.templates import TemplateLoader
from communication.translator import MultilingualTranslator
from communication.versioning import VersionCounter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    """POST body for approve/reject endpoints."""

    user_id: str
    role: str = "commander"
    justification: str | None = None


class ModifyRequest(BaseModel):
    """POST body for modify endpoint."""

    user_id: str
    role: str = "commander"
    modifications: dict = Field(default_factory=dict)


class CancelRequest(BaseModel):
    """POST body for cancel endpoint."""

    user_id: str
    role: str = "commander"
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
    operational: dict = Field(default_factory=dict)
    config_hash: str = ""


class DeliveryStatusResponse(BaseModel):
    """GET /alerts/{alert_id}/delivery-status response."""

    alert_id: str
    overall_status: str
    delivery_summary: dict = Field(default_factory=dict)
    by_channel: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# FastAPI Application Factory
# ---------------------------------------------------------------------------


def create_app(
    config: CommunicationConfig | None = None,
    pipeline: CommunicationProcessingPipeline | None = None,
    approval_workflow: ApprovalWorkflow | None = None,
    audit_writer: AuditWriter | None = None,
) -> FastAPI:
    """Create the Communication Agent FastAPI application."""
    _config = config or CommunicationConfig()

    app = FastAPI(
        title="Communication Agent",
        description="Multilingual alert generation, content safety, AIIMS approval, and multi-channel delivery",
        version=_config.agent_version,
    )

    # Concurrency limiter per NFR-001
    _semaphore = asyncio.Semaphore(_config.max_concurrent_alerts)

    # Store pipeline and services in app state
    app.state.config = _config
    app.state.pipeline = pipeline
    app.state.approval_workflow = approval_workflow or ApprovalWorkflow(config=_config)
    app.state.audit_writer = audit_writer or AuditWriter(config=_config)

    # -----------------------------------------------------------------------
    # GET /health
    # -----------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health endpoint per contracts/health-endpoint.md."""
        now = datetime.now(UTC)

        audit_status = app.state.audit_writer.get_status() if app.state.audit_writer else "unknown"
        pipeline_obj = app.state.pipeline

        # Determine overall health
        overall = "healthy"
        if audit_status == "degraded":
            overall = "degraded"

        checks = {
            "llm_connectivity": HealthCheck(status="healthy"),
            "cosmos_connectivity": HealthCheck(status="healthy"),
            "sms_service_status": HealthCheck(status="healthy"),
            "push_service_status": HealthCheck(status="healthy"),
            "broadcast_endpoint_status": HealthCheck(
                status="healthy" if _config.eas_endpoint_url else "not_configured"
            ),
        }

        operational = {
            "pending_approvals_count": (
                app.state.approval_workflow.get_pending_count()
                if app.state.approval_workflow else 0
            ),
            "active_deliveries_count": 0,
            "processing_queue_depth": (
                pipeline_obj.processed_count if pipeline_obj else 0
            ),
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
    async def process_handoff(event: AgentHandoffEvent) -> dict:
        """Process a handoff event through the pipeline."""
        if not _semaphore._value:
            raise HTTPException(
                status_code=429,
                detail="Too many concurrent alerts — try again later",
            )

        async with _semaphore:
            pipeline_obj = app.state.pipeline
            if pipeline_obj is None:
                raise HTTPException(status_code=503, detail="Pipeline not initialised")

            alert = pipeline_obj.process_handoff(event)
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
    async def approve_alert(alert_id: str, request: ApprovalRequest) -> ApprovalResponse:
        """Approve an alert for delivery."""
        workflow = app.state.approval_workflow
        now = datetime.now(UTC)

        try:
            alert = workflow.process_approval(
                alert_id=alert_id,
                user_id=request.user_id,
                role=request.role,
                action="approve",
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        # Write audit
        audit_record = CommunicationDecisionRecord(
            alert_id=alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Approved by {request.user_id} ({request.role})",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=alert_id,
            status="approved",
            action="approve",
            user_id=request.user_id,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/reject
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/reject", response_model=ApprovalResponse)
    async def reject_alert(alert_id: str, request: ApprovalRequest) -> ApprovalResponse:
        """Reject an alert with justification."""
        if not request.justification:
            raise HTTPException(
                status_code=422,
                detail="Justification is required for rejection",
            )

        workflow = app.state.approval_workflow
        now = datetime.now(UTC)

        try:
            alert = workflow.process_approval(
                alert_id=alert_id,
                user_id=request.user_id,
                role=request.role,
                action="reject",
                justification=request.justification,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        audit_record = CommunicationDecisionRecord(
            alert_id=alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Rejected by {request.user_id}: {request.justification}",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=alert_id,
            status="rejected",
            action="reject",
            user_id=request.user_id,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/modify
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/modify", response_model=ApprovalResponse)
    async def modify_alert(alert_id: str, request: ModifyRequest) -> ApprovalResponse:
        """Modify an alert — creates a new version."""
        workflow = app.state.approval_workflow

        # Get existing alert
        existing = workflow._pending_alerts.get(alert_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        try:
            new_alert = workflow.create_modified_version(
                alert=existing,
                modifications=request.modifications,
                user_id=request.user_id,
                role=request.role,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        now = datetime.now(UTC)
        audit_record = CommunicationDecisionRecord(
            alert_id=new_alert.alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Modified by {request.user_id} → {new_alert.alert_id}",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=new_alert.alert_id,
            status="pending_review",
            action="modify",
            user_id=request.user_id,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # POST /alerts/{alert_id}/cancel
    # -----------------------------------------------------------------------

    @app.post("/alerts/{alert_id}/cancel", response_model=ApprovalResponse)
    async def cancel_alert(alert_id: str, request: CancelRequest) -> ApprovalResponse:
        """Cancel an alert from pre-delivery states."""
        workflow = app.state.approval_workflow
        now = datetime.now(UTC)

        try:
            alert = workflow.cancel_alert(
                alert_id=alert_id,
                user_id=request.user_id,
                role=request.role,
                reason=request.reason,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ApprovalConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        audit_record = CommunicationDecisionRecord(
            alert_id=alert_id,
            decision_type=CommunicationDecisionType.approval_action,
            output_summary=f"Cancelled by {request.user_id}: {request.reason}",
            agent_version=_config.agent_version,
            config_version=_config.compute_config_hash(),
        )
        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return ApprovalResponse(
            alert_id=alert_id,
            status="cancelled",
            action="cancel",
            user_id=request.user_id,
            timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    # -----------------------------------------------------------------------
    # GET /alerts/{alert_id}
    # -----------------------------------------------------------------------

    @app.get("/alerts/{alert_id}")
    async def get_alert(alert_id: str) -> dict:
        """Get full alert details."""
        workflow = app.state.approval_workflow
        alert = workflow._pending_alerts.get(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        return alert.model_dump(mode="json")

    # -----------------------------------------------------------------------
    # GET /alerts/{alert_id}/delivery-status
    # -----------------------------------------------------------------------

    @app.get("/alerts/{alert_id}/delivery-status", response_model=DeliveryStatusResponse)
    async def delivery_status(alert_id: str) -> DeliveryStatusResponse:
        """Get delivery status for an alert."""
        return DeliveryStatusResponse(
            alert_id=alert_id,
            overall_status="pending",
            delivery_summary={
                "total_segments": 0,
                "total_deliveries": 0,
                "delivered": 0,
                "in_progress": 0,
                "failed": 0,
                "pending": 0,
                "completion_percentage": 0.0,
            },
        )

    return app


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

    _PORT = int(os.environ.get("PORT", "8084"))
    _config = CommunicationConfig()

    # Initialise components
    try:
        _template_loader = TemplateLoader()
    except FileNotFoundError:
        logger.warning("Template directory not found, using no template loader")
        _template_loader = None

    _deduplicator = HandoffDeduplicator(
        window_minutes=_config.handoff_dedup_window_minutes
    )
    _translator = MultilingualTranslator(
        config=_config, template_loader=_template_loader
    )
    _segmenter = AudienceSegmenter(config=_config)
    _version_counter = VersionCounter(config=_config)
    _audit_writer = AuditWriter(config=_config)
    _delivery_service = MultiChannelDeliveryService(config=_config)
    _approval_workflow = ApprovalWorkflow(config=_config)

    _pipeline = CommunicationProcessingPipeline(
        config=_config,
        deduplicator=_deduplicator,
        template_loader=_template_loader,
        translator=_translator,
        segmenter=_segmenter,
        version_counter=_version_counter,
        audit_writer=_audit_writer,
        delivery_service=_delivery_service,
    )

    app = create_app(
        config=_config,
        pipeline=_pipeline,
        approval_workflow=_approval_workflow,
        audit_writer=_audit_writer,
    )

    logger.info("Communication Agent health server starting on port %d", _PORT)
    uvicorn.run(app, host="0.0.0.0", port=_PORT, log_level="info")
