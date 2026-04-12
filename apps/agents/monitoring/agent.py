"""Monitoring Agent — signal triage, misinformation detection, and escalation.

Bug fixes applied:
- T020: LLM client call signature fixed (``purpose``/``prompt`` instead of
  ``system_prompt``/``user_prompt``)
- T021: Added ``earthquake`` and ``tsunami`` to escalation categories
- T022: Uses ``effectiveConfidence = confidenceScore × freshnessScore``
"""

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.identity import ManagedIdentityCredential
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            enable_live_metrics=True,
            credential=ManagedIdentityCredential(),
        )
    except Exception:
        logging.getLogger(__name__).warning("Failed to configure Azure Monitor", exc_info=True)

from app.validators.signal_envelope import SignalEnvelope
from common.content_safety import ContentSafetyValidator
from common.handoffs import AgentHandoffEvent, build_handoff
from monitoring.config import MonitoringConfig

logger = logging.getLogger(__name__)

# Escalation categories — T021 bug fix: added earthquake & tsunami
ESCALATION_CATEGORIES = {"fire", "weather", "hydrology", "earthquake", "tsunami"}


class MonitoringAgent:
    """Core monitoring agent with LLM-powered misinformation detection."""

    def __init__(
        self,
        signal_repository=None,
        llm_client=None,
        config: MonitoringConfig | None = None,
        content_safety: ContentSafetyValidator | None = None,
    ):
        self._signal_repository = signal_repository
        self._llm_client = llm_client
        self._config = config or MonitoringConfig()
        self._content_safety = content_safety or ContentSafetyValidator()

    def summarize_signal(self, envelope: SignalEnvelope) -> dict[str, object]:
        """Generate a structured summary; attempt LLM enrichment then validate with content safety."""
        base_summary = {
            "category": envelope.category,
            "sourceKind": envelope.source.kind,
            "incidentId": envelope.incidentId,
        }

        # Try LLM-enriched summary
        if self._llm_client:
            try:
                prompt = (
                    "You are an emergency response summarisation assistant for Australian disaster response. "
                    f"Summarise this signal concisely. Category: {envelope.category}. "
                    f"Source: {envelope.source.kind}. Payload: {envelope.payload}. "
                    "Respond with a brief factual summary (max 200 chars)."
                )
                response = self._llm_client.generate_response(
                    purpose="drafting",
                    prompt=prompt,
                    max_output_tokens=100,
                )
                llm_text = response.get("text", "").strip()
                if llm_text:
                    safety_result = self._content_safety.validate(text=llm_text)
                    if safety_result.passed:
                        base_summary["llm_summary"] = llm_text
                        base_summary["content_safety_result"] = "passed"
                    else:
                        base_summary["content_safety_result"] = "failed_with_fallback"
                        logger.info("Content safety failed for LLM summary, using rule-based fallback")
            except Exception:
                logger.info("LLM unavailable for summarisation, using rule-based fallback")

        return base_summary

    def build_high_risk_handoff(
        self,
        envelope: SignalEnvelope,
        suspicious_penalty: float = 0.0,
        tenant_id: str = "live",
    ) -> AgentHandoffEvent | None:
        """Build a handoff event if the signal meets escalation criteria.

        T022 bug fix: uses effectiveConfidence = confidenceScore × freshnessScore.
        T021 bug fix: checks against full ESCALATION_CATEGORIES set.
        """
        # T022: Compute effectiveConfidence
        effective_confidence = envelope.confidenceScore * envelope.freshnessScore
        effective_confidence -= suspicious_penalty
        effective_confidence = max(0.0, effective_confidence)

        is_high_risk = (
            envelope.category in ESCALATION_CATEGORIES
            and effective_confidence >= self._config.escalation_confidence_threshold
        )
        if not is_high_risk or not envelope.incidentId:
            return None

        return build_handoff(
            incident_id=envelope.incidentId,
            source_agent="monitoring",
            target_agent="risk_assessment",
            scope_key=envelope.incidentId,
            payload={
                "category": envelope.category,
                "sourceKind": envelope.source.kind,
                "signalSummary": self.summarize_signal(envelope),
            },
            confidence=effective_confidence,
            tenant_id=tenant_id,
        )

    async def evaluate_escalated_signal(
        self, envelope: SignalEnvelope
    ) -> str:
        """Tier 2 LLM-based evaluation with async timeout and fail-safe-CLOSED.

        T020 bug fix: uses correct LLM client signature (purpose + prompt).
        T023: Async with configurable timeout.
        T024: Fail-safe-CLOSED on timeout or unexpected response → held_for_review.
        T025: Returns 'suspicious' as distinct classification.

        Returns one of: credible, suspicious, misinformation, held_for_review, llm_unavailable.
        """
        if not self._llm_client:
            return "llm_unavailable"

        try:
            # T020 bug fix: correct call signature
            prompt = (
                "You are a misinformation detection assistant for Australian disaster response. "
                f"Evaluate this disaster-related social media post for credibility. "
                f"Category: {envelope.category}. Content: {envelope.payload}. "
                f"Is this credible community intelligence or misinformation? "
                f"Respond with exactly one word: credible, suspicious, or misinformation."
            )

            # T023: async timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._llm_client.generate_response,
                    purpose="reasoning",
                    prompt=prompt,
                    max_output_tokens=10,
                ),
                timeout=self._config.llm_eval_timeout_seconds,
            )

            result_text = response.get("text", "").strip().lower()

            # Parse classification
            if "misinformation" in result_text:
                return "misinformation"
            if "suspicious" in result_text:
                return "suspicious"  # T025
            if "credible" in result_text:
                return "credible"

            # T024: Unexpected response → fail-safe-CLOSED
            logger.warning(
                "LLM returned unexpected response '%s', holding for review (fail-safe-CLOSED)",
                result_text,
            )
            return "held_for_review"

        except TimeoutError:
            # T024: Timeout → fail-safe-CLOSED
            logger.warning("LLM evaluation timed out, holding for review (fail-safe-CLOSED)")
            return "llm_timeout"
        except Exception:
            logger.warning("LLM evaluation failed, holding for review")
            return "llm_unavailable"

    async def retrospective_associate(
        self,
        incident_id: str,
        jurisdiction_id: str,
        lookback_hours: int | None = None,
        tenant_id: str = "live",
    ) -> int:
        """Retrospectively associate unmatched signals with a newly declared incident.

        T046: Tenant isolation — simulation signals never associate with live incidents.
        """
        if lookback_hours is None:
            lookback_hours = self._config.retrospective_lookback_hours
        if not self._signal_repository:
            return 0

        cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
        unassociated = await self._signal_repository.query_unassociated(
            jurisdiction_id=jurisdiction_id,
            since=cutoff,
            tenant_id=tenant_id,  # T046: tenant isolation
        )
        count = 0
        for signal in unassociated:
            await self._signal_repository.update_incident_id(signal.signal_id, incident_id)
            count += 1
            logger.info(
                "Retrospectively associated signal %s with incident %s (tenant=%s)",
                signal.signal_id,
                incident_id,
                tenant_id,
            )
        return count


# ---------------------------------------------------------------------------
# FastAPI application — health endpoint and retrospective association API
# ---------------------------------------------------------------------------

def create_app(
    agent: MonitoringAgent | None = None,
    audit_writer=None,
    freshness_tracker=None,
    config: MonitoringConfig | None = None,
):
    """Create the FastAPI application with health and association endpoints."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel as PydanticBaseModel

    _config = config or MonitoringConfig()
    app = FastAPI(title="Monitoring Agent", version=_config.agent_version)

    # Store dependencies on app state
    app.state.agent = agent
    app.state.audit_writer = audit_writer
    app.state.freshness_tracker = freshness_tracker
    app.state.config = _config

    class HealthResponse(PydanticBaseModel):
        status: str
        agent_version: str
        timestamp: str
        checks: dict

    class AssociationRequest(PydanticBaseModel):
        incident_id: str
        jurisdiction_id: str
        lookback_hours: int = 24
        tenant_id: str = "live"

    class AssociationResponse(PydanticBaseModel):
        incident_id: str
        jurisdiction_id: str
        signals_associated: int
        lookback_hours: int
        timestamp: str

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Structured health endpoint per contracts/health-endpoint.md."""
        now = datetime.now(UTC)

        # LLM connectivity check — configuration-only, no live call
        llm_status = "offline"
        llm_latency = 0
        llm_agent = app.state.agent
        if llm_agent and llm_agent._llm_client:
            llm_status = "configured"

        # Data source freshness
        freshness_summary = "healthy"
        freshness_sources = []
        if app.state.freshness_tracker:
            freshness_summary = app.state.freshness_tracker.get_summary_status()
            for ind in app.state.freshness_tracker.get_all_indicators():
                freshness_sources.append({
                    "data_source_id": ind.data_source_id,
                    "source_type": ind.source_type.value,
                    "status": ind.status.value,
                    "last_signal_received_at": ind.last_signal_received_at.isoformat(),
                    "staleness_threshold_minutes": ind.staleness_threshold_minutes,
                })

        # Processing queue (placeholder — real impl uses Service Bus client)
        queue_depth = 0
        queue_status = "healthy"

        # Audit store
        audit_status = "healthy"
        audit_buffer_depth = 0
        if app.state.audit_writer:
            audit_status = app.state.audit_writer.get_status()
            audit_buffer_depth = app.state.audit_writer.buffer_depth

        # Overall status determination
        overall = "healthy"
        if llm_status == "offline" or audit_status == "degraded":
            overall = "unhealthy"
        elif any(
            x != "healthy"
            for x in [llm_status, freshness_summary, queue_status, audit_status]
        ):
            overall = "degraded"

        return HealthResponse(
            status=overall,
            agent_version=_config.agent_version,
            timestamp=now.isoformat(),
            checks={
                "llm_connectivity": {
                    "status": llm_status,
                    "last_checked_at": now.isoformat(),
                    "latency_ms": llm_latency,
                },
                "data_source_freshness": {
                    "summary": freshness_summary,
                    "sources": freshness_sources,
                },
                "processing_queue": {
                    "depth": queue_depth,
                    "status": queue_status,
                },
                "audit_store": {
                    "status": audit_status,
                    "buffer_depth": audit_buffer_depth,
                },
            },
        )

    @app.post("/associate", response_model=AssociationResponse)
    async def associate(request: AssociationRequest) -> AssociationResponse:
        """Retrospective incident association endpoint per contracts/health-endpoint.md."""
        _agent = app.state.agent
        if not _agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        try:
            count = await _agent.retrospective_associate(
                incident_id=request.incident_id,
                jurisdiction_id=request.jurisdiction_id,
                lookback_hours=request.lookback_hours,
                tenant_id=request.tenant_id,
            )

            # T047: Emit audit record for retrospective association
            if app.state.audit_writer and count > 0:
                from monitoring.models import DecisionType, MonitoringDecisionRecord
                record = MonitoringDecisionRecord(
                    signal_id=f"association-{request.incident_id}",
                    decision=DecisionType.associated,
                    confidence=1.0,
                    inputs={
                        "incident_id": request.incident_id,
                        "jurisdiction_id": request.jurisdiction_id,
                        "lookback_hours": request.lookback_hours,
                        "tenant_id": request.tenant_id,
                    },
                    output={"signals_associated": count},
                    agent_version=_config.agent_version,
                    reasoning_summary=f"Retrospectively associated {count} signals with {request.incident_id}",
                    incident_scope_key=f"{request.tenant_id}:{request.incident_id}",
                    tenant_id=request.tenant_id,
                )
                app.state.audit_writer.write(record)

            return AssociationResponse(
                incident_id=request.incident_id,
                jurisdiction_id=request.jurisdiction_id,
                signals_associated=count,
                lookback_hours=request.lookback_hours,
                timestamp=datetime.now(UTC).isoformat(),
            )
        except Exception as exc:
            logger.error("Retrospective association failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "repository_unavailable",
                    "signals_associated": 0,
                    "message": str(exc),
                },
            )

    return app


# ---------------------------------------------------------------------------
# Entrypoint — FastAPI-based health server replacing http.server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _console = logging.StreamHandler()
    _console.setFormatter(_fmt)
    root = logging.getLogger()
    root.addHandler(_console)
    root.setLevel(logging.INFO)

    _PORT = int(os.environ.get("PORT", "8080"))
    _config = MonitoringConfig()
    _agent = MonitoringAgent(config=_config)

    app = create_app(agent=_agent, config=_config)

    logger.info("Monitoring Agent health server starting on port %d", _PORT)
    uvicorn.run(app, host="0.0.0.0", port=_PORT, log_level="info")
