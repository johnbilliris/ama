"""Risk Assessment Agent — hazard prediction, recommendation generation, and multi-agent escalation.

Fixes applied from plan.md Identified Issues:
- Issue #1: Hardcoded confidence=0.9 → uses recommendation.confidence_score
- Issue #2: Categorical confidence_level check → numeric confidence_score >= threshold
- Issue #3: Missing assessment_id, confidence_score, severity_level on recommendations
- Issue #4: Only public_alert → all 5 recommendation types
- Issue #5: No signal retrieval/correlation → full pipeline
"""

from __future__ import annotations

import logging
import os
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from common.handoffs import AgentHandoffEvent, build_handoff

if TYPE_CHECKING:
    from fastapi import FastAPI

    from apps.agents.common.llm_mixin import LLMCallMixin
else:
    from common.llm_mixin import LLMCallMixin
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.correlation import ContradictionResult, CorrelationResult, RiskSignal
from risk_assessment.extrapolation import ExtrapolationResult
from risk_assessment.models import (
    DecisionType,
    RiskAssessmentDecisionRecord,
    confidence_to_level,
)
from risk_assessment.severity import SeverityComputer
from risk_assessment.templates import (
    generate_assessment_summary,
    generate_recommendation_explanation,
)

from packages.domain.src.domain.models.hazard_assessment import (
    AssessmentGenerationMethod,
    AssessmentType,
    HazardAssessment,
)
from packages.domain.src.domain.models.recommendation import (
    Recommendation,
    RecommendationGenerationMethod,
    RecommendationType,
)

logger = logging.getLogger(__name__)

# Assessment type → recommendation types mapping per contracts/assessment-pipeline.md §Stage 6
ASSESSMENT_TO_RECOMMENDATION_TYPES: dict[AssessmentType, list[RecommendationType]] = {
    "spread_prediction": ["public_alert", "evacuation"],
    "impact_projection": ["public_alert", "resource_allocation"],
    "route_risk": ["evacuation"],
    "infrastructure_risk": ["infrastructure_action", "resource_allocation"],
    "community_impact": ["public_alert", "resource_allocation"],
}

# Recommendation type abbreviations for ID generation
REC_TYPE_ABBREV: dict[str, str] = {
    "public_alert": "pa",
    "evacuation": "ev",
    "resource_allocation": "ra",
    "coordination": "co",
    "infrastructure_action": "ia",
}


def _assessment_generation_method(value: object) -> AssessmentGenerationMethod:
    if value == "llm":
        return "llm"
    if value == "template_fallback":
        return "template_fallback"
    if value == "safety_fallback":
        return "safety_fallback"
    raise ValueError(f"Unsupported assessment generation method: {value!r}")


def _recommendation_generation_method(value: object) -> RecommendationGenerationMethod:
    if value == "llm":
        return "llm"
    if value == "template":
        return "template"
    if value == "template_fallback":
        return "template_fallback"
    if value == "safety_fallback":
        return "safety_fallback"
    raise ValueError(f"Unsupported recommendation generation method: {value!r}")


class RiskAssessmentAgent(LLMCallMixin):
    """Risk Assessment Agent with full assessment and recommendation generation."""

    def __init__(self, config: RiskAssessmentConfig | None = None) -> None:
        super().__init__()
        self._config = config or RiskAssessmentConfig()
        self._severity_computer = SeverityComputer()
        self._rec_counter: dict[str, int] = {}

    def _next_rec_seq(self, incident_id: str) -> int:
        """Generate next recommendation sequence number for an incident."""
        key = incident_id
        self._rec_counter[key] = self._rec_counter.get(key, 0) + 1
        return self._rec_counter[key]

    # ------------------------------------------------------------------
    # Assessment Generation
    # ------------------------------------------------------------------

    def generate_assessment(
        self,
        incident_id: str,
        signals: list[RiskSignal],
        correlation: CorrelationResult,
        contradiction: ContradictionResult,
        assessment_type: AssessmentType,
        version: int,
        config_hash: str,
        tenant_id: str = "live",
        extrapolation: ExtrapolationResult | None = None,
    ) -> HazardAssessment:
        """Generate a full HazardAssessment with LLM or template fallback.

        Implements reproducibility with temperature=0 and input snapshots.
        """
        incident_scope_key = f"{tenant_id}:{incident_id}"
        signal_ids = [s.get("signal_id", "unknown") for s in signals]
        signal_category = signals[0].get("category", "fire") if signals else "fire"

        # Apply penalty ordering: freshness (in averaging) → contradiction → fallback
        confidence = correlation.weighted_confidence
        if contradiction.detected:
            confidence *= self._config.contradiction_reduction_factor
        confidence = max(0.0, min(1.0, confidence))

        # Compute severity
        population = self._estimate_population(signals)
        severity = self._severity_computer.compute_severity(
            signal_category=signal_category,
            confidence_adjusted=confidence,
            population_estimate=population,
            disaster_type=signals[0].get("disaster_type") if signals else None,
        )

        # Compute validity
        validity_hours = self._config.validity_hours_for(signal_category)
        now = datetime.now(UTC)
        valid_until = now + timedelta(hours=validity_hours)

        # Generate summary via LLM or template
        cited_signals = ", ".join(signal_ids) if signal_ids else "no-signals"
        template_text = generate_assessment_summary(
            assessment_type=assessment_type,
            signals=signals,
            severity=severity.value,
            confidence=confidence,
            contradiction_detected=contradiction.detected,
            stale_signal_ids=correlation.stale_signal_ids,
        )

        response = self._generate_with_fallback(
            purpose="reasoning",
            prompt=(
                f"Generate a concise hazard assessment summary for a {assessment_type} assessment. "
                f"Incident: {incident_id}. Severity: {severity.value}. "
                f"Confidence: {confidence:.2f}. Signals: {cited_signals}. "
                f"Include all signal IDs in the summary."
            ),
            template_text=template_text,
            max_output_tokens=400,
            timeout_seconds=5.0,
        )

        summary = str(response["text"])
        generation_method = _assessment_generation_method(response["generation_method"])

        # Apply fallback penalty AFTER contradiction penalty
        if generation_method == "template_fallback":
            confidence *= self._config.fallback_reduction_factor
            confidence = max(0.0, min(1.0, confidence))
            # Re-compute severity with adjusted confidence
            severity = self._severity_computer.compute_severity(
                signal_category=signal_category,
                confidence_adjusted=confidence,
                population_estimate=population,
                disaster_type=signals[0].get("disaster_type") if signals else None,
            )

        # Ensure signal IDs appear in summary
        if signal_ids and not any(sid in summary for sid in signal_ids):
            summary = f"{summary} Signal references: {cited_signals}."

        # Add contradiction note to summary if detected
        if contradiction.detected and "contradiction" not in summary.lower():
            sources = set()
            for pair in contradiction.pairs:
                sources.add(pair.source_a)
                sources.add(pair.source_b)
            source_names = ", ".join(sorted(sources))
            summary += (
                f" WARNING: Contradictory signals detected from {source_names}. "
                "Both risk-increasing and risk-decreasing indicators present. "
                "Human review recommended."
            )

        confidence_level = confidence_to_level(confidence)

        # Enrich with predictive extrapolation if available
        if extrapolation and extrapolation.trend_detected:
            trend_parts = [f"PREDICTIVE OUTLOOK: Trend is {extrapolation.trend_direction}"]
            trend_parts.append(
                f"(slope {extrapolation.slope_per_hour:+.4f}/hr, R²={extrapolation.details.get('r_squared', 0):.2f})."
            )
            if extrapolation.hours_to_warning_threshold is not None:
                trend_parts.append(
                    f"Warning threshold breach projected in ~{extrapolation.hours_to_warning_threshold:.1f} hours."
                )
            if extrapolation.hours_to_emergency_threshold is not None:
                trend_parts.append(
                    f"Emergency threshold breach projected in ~{extrapolation.hours_to_emergency_threshold:.1f} hours."
                )
            trend_parts.append(
                f"24h projection: {extrapolation.projected_value_24h:.2f}; "
                f"48h projection: {extrapolation.projected_value_48h:.2f}."
            )
            if extrapolation.predictive_lead_time_hours > 0:
                trend_parts.append(f"Predictive lead time: {extrapolation.predictive_lead_time_hours:.1f}h.")
                # Boost confidence slightly when predictive data supports the assessment
                confidence += self._config.extrapolation_confidence_boost
                confidence = min(1.0, confidence)
                confidence_level = confidence_to_level(confidence)

            summary += " " + " ".join(trend_parts)

        # Build input snapshot for reproducibility
        input_snapshot = {
            "signals": [
                {
                    "signal_id": s.get("signal_id"),
                    "confidence_score": s.get("confidence_score"),
                    "freshness_score": s.get("freshness_score"),
                    "source_kind": s.get("source_kind"),
                    "category": s.get("category"),
                    "provenance": s.get("provenance", {}),
                }
                for s in signals
            ],
            "model_deployment_id": response.get("model_deployment_id"),
            "prompt_template_version": "1.0",
            "configuration_hash": config_hash,
            "extrapolation": {
                "trend_detected": extrapolation.trend_detected,
                "trend_direction": extrapolation.trend_direction,
                "slope_per_hour": extrapolation.slope_per_hour,
                "predictive_lead_time_hours": extrapolation.predictive_lead_time_hours,
                "projected_value_24h": extrapolation.projected_value_24h,
                "projected_value_48h": extrapolation.projected_value_48h,
                "extrapolation_confidence": extrapolation.extrapolation_confidence,
            }
            if extrapolation
            else None,
        }

        assessment_id = f"ha-{incident_id}-{assessment_type}-v{version}"

        return HazardAssessment(
            hazard_assessment_id=assessment_id,
            incident_id=incident_id,
            assessment_type=assessment_type,
            input_signal_ids=signal_ids,
            summary=summary,
            confidence_level=confidence_level.value,
            generated_at=now,
            version=version,
            confidence_score=correlation.weighted_confidence,
            confidence_adjusted=confidence,
            severity_level=severity.value,
            valid_until=valid_until,
            status="active",
            generation_method=generation_method,
            model_deployment_id=response.get("model_deployment_id"),
            prompt_template_version="1.0",
            configuration_version=config_hash,
            input_snapshot=input_snapshot,
            contradiction_detected=contradiction.detected,
            contradiction_details=contradiction.details if contradiction.detected else None,
            stale_signal_ids=correlation.stale_signal_ids or None,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
        )

    def _estimate_population(self, signals: list[RiskSignal]) -> int | None:
        """Extract population estimate from signals if available."""
        for sig in signals:
            payload = sig.get("payload", {})
            pop = payload.get("population_estimate") or payload.get("affected_population")
            if pop is not None:
                return int(pop)
        return None

    @staticmethod
    def _build_evidence_lines(signals: list[RiskSignal]) -> tuple[list[str], list[str], bool]:
        lines: list[str] = []
        signal_ids: list[str] = []
        has_unevidenced = False
        for signal in signals:
            sid = str(signal.get("signal_id", "")).strip()
            evidence_state = str(signal.get("evidence_state", "retrieved"))
            if evidence_state == "unevidenced" or sid in {"", "unevidenced"}:
                has_unevidenced = True
                continue
            payload = signal.get("payload", {}) if isinstance(signal.get("payload"), dict) else {}
            provenance = signal.get("provenance", {}) if isinstance(signal.get("provenance"), dict) else {}
            snippet = {
                "hazard_type": payload.get("hazard_type"),
                "severity": payload.get("severity"),
                "location_name": payload.get("location_name"),
                "summary": str(payload.get("summary", ""))[:180],
                "source_uri": provenance.get("sourceUri"),
                "source_timestamp": provenance.get("sourceTimestamp"),
            }
            lines.append(f"{sid}: {snippet}")
            signal_ids.append(sid)
        return lines, signal_ids, has_unevidenced

    @staticmethod
    def _validate_citations(explanation: str, allowed_signal_ids: list[str]) -> tuple[bool, list[str], list[str]]:
        if not allowed_signal_ids:
            return False, [], []
        found_allowed = [sid for sid in allowed_signal_ids if sid in explanation]
        found_signal_tokens = set(re.findall(r"\bsig-[A-Za-z0-9_-]+\b", explanation))
        invalid = sorted(found_signal_tokens - set(allowed_signal_ids))
        synthetic_like = re.findall(r"\b(?:synth-[A-Za-z0-9_-]*|unevidenced)\b", explanation)
        invalid.extend([token for token in synthetic_like if token not in invalid])
        return bool(found_allowed) and not invalid, sorted(set(found_allowed)), invalid

    # ------------------------------------------------------------------
    # Recommendation Generation — all 5 types
    # ------------------------------------------------------------------

    def generate_recommendations(
        self,
        assessment: HazardAssessment,
        signals: list[RiskSignal],
    ) -> list[Recommendation]:
        """Generate all applicable recommendations from an assessment.

        Maps assessment_type → recommendation types per contracts/assessment-pipeline.md §Stage 6.
        """
        rec_types = list(ASSESSMENT_TO_RECOMMENDATION_TYPES.get(assessment.assessment_type, ["public_alert"]))

        # Filter evacuation: only if severity ≥ high for spread_prediction
        if assessment.assessment_type == "spread_prediction":
            if assessment.severity_level not in ("high", "critical"):
                rec_types = [r for r in rec_types if r != "evacuation"]

        # Filter resource_allocation: only if coordination tasks present for impact_projection/community_impact
        if assessment.assessment_type in ("impact_projection", "community_impact"):
            has_coordination = self._has_coordination_tasks(signals)
            if not has_coordination:
                rec_types = [r for r in rec_types if r != "resource_allocation"]

        # Generate route_risk assessment type: derived when spread_prediction or
        # impact_projection assessments indicate threat to evacuation routes
        if assessment.assessment_type in ("spread_prediction", "impact_projection"):
            if self._threatens_evacuation_routes(signals, assessment):
                rec_types.append("evacuation")

        # Deduplicate
        rec_types = list(dict.fromkeys(rec_types))

        recommendations = []
        for rec_type in rec_types:
            rec = self._generate_recommendation(assessment, signals, rec_type)
            recommendations.append(rec)

        return recommendations

    def _generate_recommendation(
        self,
        assessment: HazardAssessment,
        signals: list[RiskSignal],
        rec_type: RecommendationType,
    ) -> Recommendation:
        """Generate a single recommendation of the given type."""
        signal_ids = assessment.input_signal_ids
        cited_signals = ", ".join(signal_ids) if signal_ids else "no-signals"
        seq = self._next_rec_seq(assessment.incident_id)
        abbrev = REC_TYPE_ABBREV.get(rec_type, "unk")
        rec_id = f"rec-{assessment.incident_id}-{abbrev}-{seq:03d}"

        summaries: dict[str, str] = {
            "public_alert": "Prepare multilingual community alert",
            "evacuation": "Initiate evacuation planning for affected zones",
            "resource_allocation": "Allocate resources for emergency response coordination",
            "coordination": "Coordinate multi-agency response operations",
            "infrastructure_action": "Protect or restore critical infrastructure",
        }

        template_explanation = generate_recommendation_explanation(
            rec_type=rec_type,
            signals=signals,
            assessment_summary=assessment.summary,
        )

        evidence_lines, allowed_signal_ids, has_unevidenced = self._build_evidence_lines(signals)
        if rec_type == "public_alert" and (has_unevidenced or not allowed_signal_ids):
            blocked_text = (
                "Insufficient retrieved source evidence for a public alert recommendation. "
                "Escalate to human review before publication."
            )
            return Recommendation(
                recommendation_id=rec_id,
                incident_id=assessment.incident_id,
                type=rec_type,
                summary=summaries.get(rec_type, f"Action required: {rec_type}"),
                explanation=blocked_text,
                supporting_signal_ids=allowed_signal_ids,
                required_approval_level="incident_commander",
                confidence_level=confidence_to_level(assessment.confidence_adjusted).value,
                status="under_review",
                proposed_by_agent="risk_assessment",
                generation_method="template_fallback",
                model_deployment_id=None,
                token_usage={"input_tokens": 0, "output_tokens": 0},
                assessment_id=assessment.hazard_assessment_id,
                confidence_score=assessment.confidence_adjusted,
                severity_level=assessment.severity_level,
                incident_scope_key=assessment.incident_scope_key,
                tenant_id=assessment.tenant_id,
            )

        evidence_block = "\n".join(evidence_lines) if evidence_lines else "NO_RETRIEVED_EVIDENCE"

        response = self._generate_with_fallback(
            purpose="reasoning",
            prompt=(
                f"Create a concise {rec_type} recommendation explanation "
                f"that includes only retrieved signal IDs. "
                f"Incident: {assessment.incident_id}; Signals: {cited_signals}. "
                f"Assessment summary: {assessment.summary[:200]}\n"
                f"Retrieved source evidence (bounded):\n{evidence_block}\n"
                "Do not invent signal identifiers."
            ),
            template_text=template_explanation,
            max_output_tokens=280,
            timeout_seconds=5.0,
        )

        explanation = str(response["text"])

        resolved_generation_method = _recommendation_generation_method(response["generation_method"])
        if resolved_generation_method == "llm":
            citations_valid, cited_subset, invalid_citations = self._validate_citations(
                explanation,
                allowed_signal_ids,
            )
            if not citations_valid:
                logger.warning(
                    "Invalid or missing LLM citations for recommendation %s: cited=%s invalid=%s",
                    rec_id,
                    cited_subset,
                    invalid_citations,
                )
                explanation = template_explanation
                resolved_generation_method = "template_fallback"

        retained_usage = response.get("token_usage")

        confidence_level = confidence_to_level(assessment.confidence_adjusted)

        return Recommendation(
            recommendation_id=rec_id,
            incident_id=assessment.incident_id,
            type=rec_type,
            summary=summaries.get(rec_type, f"Action required: {rec_type}"),
            explanation=explanation,
            supporting_signal_ids=allowed_signal_ids,
            required_approval_level="incident_commander",
            confidence_level=confidence_level.value,
            status="proposed",
            proposed_by_agent="risk_assessment",
            generation_method=resolved_generation_method,
            model_deployment_id=response.get("model_deployment_id"),
            token_usage=retained_usage,
            assessment_id=assessment.hazard_assessment_id,
            confidence_score=assessment.confidence_adjusted,
            severity_level=assessment.severity_level,
            incident_scope_key=assessment.incident_scope_key,
            tenant_id=assessment.tenant_id,
        )

    def _has_coordination_tasks(self, signals: list[RiskSignal]) -> bool:
        """Check if signals indicate coordination tasks are needed."""
        for sig in signals:
            payload = sig.get("payload", {})
            if payload.get("coordination_required"):
                return True
            if payload.get("multi_agency"):
                return True
            if sig.get("category") in ("infrastructure", "community_report"):
                return True
        return False

    def _threatens_evacuation_routes(
        self,
        signals: list[RiskSignal],
        assessment: HazardAssessment,
    ) -> bool:
        """Check if signals indicate threat to evacuation routes."""
        for sig in signals:
            payload = sig.get("payload", {})
            if payload.get("threatens_routes") or payload.get("route_blocked"):
                return True
            if payload.get("spread_direction") and payload.get("near_roads"):
                return True
        return False

    # ------------------------------------------------------------------
    # Backward-compatible API
    # ------------------------------------------------------------------

    def recommend_public_alert(
        self,
        incident_id: str,
        signal_ids: list[str],
        signal_evidence: dict[str, dict[str, object]] | None = None,
    ) -> Recommendation:
        """Generate a public_alert recommendation (backward-compatible API).

        Creates a minimal assessment context and delegates to _generate_recommendation.
        """
        cited_signals = ", ".join(signal_ids) if signal_ids else "no-signals"
        signal_evidence = signal_evidence or {}
        evidence_lines = [f"{sid}: {signal_evidence.get(sid, {})}" for sid in signal_ids]
        template_explanation = (
            "Authoritative and community signals indicate escalating community risk. "
            "Escalate to human review if citations are missing."
        )

        response = self._generate_with_fallback(
            purpose="reasoning",
            prompt=(
                "Create a concise public alert recommendation explanation"
                " that includes only retrieved signal IDs. "
                f"Incident: {incident_id}; Signals: {cited_signals}."
                f" Retrieved source evidence: {'; '.join(evidence_lines) if evidence_lines else 'none'}"
            ),
            template_text=template_explanation,
            max_output_tokens=280,
            timeout_seconds=5.0,
        )

        explanation = str(response["text"])
        resolved_generation_method = _recommendation_generation_method(response["generation_method"])
        if resolved_generation_method == "llm":
            citations_valid, _, invalid_citations = self._validate_citations(explanation, signal_ids)
            if not citations_valid:
                logger.warning(
                    "recommend_public_alert citation validation failed: invalid=%s",
                    invalid_citations,
                )
                explanation = template_explanation
                resolved_generation_method = "template_fallback"

        retained_usage = response.get("token_usage")

        return Recommendation(
            recommendation_id=f"rec-{incident_id}-pa-001",
            incident_id=incident_id,
            type="public_alert",
            summary="Prepare multilingual community alert",
            explanation=explanation,
            supporting_signal_ids=signal_ids,
            required_approval_level="incident_commander",
            confidence_level="high",
            generation_method=resolved_generation_method,
            model_deployment_id=response.get("model_deployment_id"),
            token_usage=retained_usage,
            assessment_id="",
            confidence_score=0.85,
            severity_level="high",
        )

    # ------------------------------------------------------------------
    # Escalation Logic (Fixed from plan.md issues #1, #2)
    # ------------------------------------------------------------------

    def build_communication_handoff(
        self,
        recommendation: Recommendation,
    ) -> AgentHandoffEvent | None:
        """Build handoff to Communication Agent for public_alert recommendations.

        Uses numeric confidence_score >= 0.7 threshold (not categorical).
        Uses recommendation.confidence_score (not hardcoded 0.9).
        """
        if recommendation.type != "public_alert":
            return None
        if recommendation.confidence_score < self._config.escalation_threshold_communication:
            return None

        return build_handoff(
            incident_id=recommendation.incident_id,
            source_agent="risk_assessment",
            target_agent="communication",
            scope_key=recommendation.incident_scope_key or recommendation.incident_id,
            payload={
                "recommendationId": recommendation.recommendation_id,
                "summary": recommendation.summary,
                "explanation": recommendation.explanation,
                "assessmentId": recommendation.assessment_id,
            },
            confidence=recommendation.confidence_score,
            tenant_id=recommendation.tenant_id,
        )

    def build_evacuation_handoff(
        self,
        recommendation: Recommendation,
    ) -> AgentHandoffEvent | None:
        """Build handoff to Evacuation Agent.

        Requires severity >= high AND confidence >= 0.6.
        """
        if recommendation.type != "evacuation":
            return None
        if recommendation.severity_level not in ("high", "critical"):
            return None
        if recommendation.confidence_score < self._config.escalation_threshold_evacuation:
            return None

        return build_handoff(
            incident_id=recommendation.incident_id,
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key=recommendation.incident_scope_key or recommendation.incident_id,
            payload={
                "recommendationId": recommendation.recommendation_id,
                "summary": recommendation.summary,
                "assessmentId": recommendation.assessment_id,
            },
            confidence=recommendation.confidence_score,
            tenant_id=recommendation.tenant_id,
        )

    def build_resource_allocation_handoff(
        self,
        recommendation: Recommendation,
    ) -> AgentHandoffEvent | None:
        """Build handoff to Resource Allocation Agent.

        Triggered when coordination tasks are present (no specific confidence threshold).
        """
        if recommendation.type not in ("resource_allocation", "coordination"):
            return None

        return build_handoff(
            incident_id=recommendation.incident_id,
            source_agent="risk_assessment",
            target_agent="resource_allocation",
            scope_key=recommendation.incident_scope_key or recommendation.incident_id,
            payload={
                "recommendationId": recommendation.recommendation_id,
                "summary": recommendation.summary,
                "assessmentId": recommendation.assessment_id,
            },
            confidence=recommendation.confidence_score,
            tenant_id=recommendation.tenant_id,
        )


# ---------------------------------------------------------------------------
# FastAPI application — health and override endpoints
# ---------------------------------------------------------------------------

# Pydantic response/request models are defined at module level so that
# ``from __future__ import annotations`` (PEP 563) can resolve them when
# FastAPI inspects endpoint signatures.

from pydantic import BaseModel as _PydanticBaseModel  # noqa: E402


class _HealthCheckDetail(_PydanticBaseModel):
    status: str
    last_checked_at: str | None = None
    latency_ms: int | None = None


class _ProcessingQueueDetail(_PydanticBaseModel):
    depth: int
    status: str


class _AuditStoreDetail(_PydanticBaseModel):
    status: str
    buffer_depth: int


class _HealthChecks(_PydanticBaseModel):
    llm_connectivity: _HealthCheckDetail
    signal_store: _HealthCheckDetail
    processing_queue: _ProcessingQueueDetail
    audit_store: _AuditStoreDetail


class _HealthResponse(_PydanticBaseModel):
    status: str
    agent_version: str
    timestamp: str
    checks: _HealthChecks


class _OverrideRequest(_PydanticBaseModel):
    recommendation_id: str
    action: str  # approve | reject | modify
    user_id: str
    role: str
    justification: str
    modifications: dict[str, object] | None = None


class _OverrideResponse(_PydanticBaseModel):
    recommendation_id: str
    previous_status: str
    new_status: str
    override_timestamp: str
    audit_record_id: str


def create_app(
    agent: RiskAssessmentAgent | None = None,
    audit_writer: object | None = None,
    pipeline: object | None = None,
    config: RiskAssessmentConfig | None = None,
    recommendation_store: object | None = None,
) -> FastAPI:
    """Create the FastAPI application with health and override endpoints.

    Follows the monitoring agent pattern: ``create_app`` as factory, deps on
    ``app.state``, Pydantic response models.
    """
    from fastapi import FastAPI, HTTPException

    _config = config or RiskAssessmentConfig()
    app = FastAPI(title="Risk Assessment Agent", version=_config.agent_version)

    # Store dependencies on app state
    app.state.agent = agent
    app.state.audit_writer = audit_writer
    app.state.pipeline = pipeline
    app.state.config = _config
    app.state.recommendation_store = recommendation_store

    # ------- GET /health -------

    @app.get("/health", response_model=_HealthResponse)
    async def health() -> _HealthResponse:
        """Structured health endpoint per contracts/health-endpoint.md.

        Status determination:
        - All checks healthy → healthy
        - Processing queue offline → unhealthy
        - Any other degradation → degraded
        """
        import time as _time

        now = datetime.now(UTC)

        # LLM connectivity check
        llm_status = "offline"
        llm_latency = 0
        llm_agent = app.state.agent
        if llm_agent and llm_agent._llm_client:
            try:
                t0 = _time.perf_counter()
                llm_agent._llm_client.generate_response(
                    purpose="reasoning",
                    prompt="health check ping",
                    max_output_tokens=5,
                )
                llm_latency = round((_time.perf_counter() - t0) * 1000)
                llm_status = "healthy" if llm_latency < 5000 else "degraded"
            except Exception:
                llm_status = "offline"

        # Signal store check
        signal_store_status = "healthy"
        _pipeline = app.state.pipeline
        if _pipeline and _pipeline._signal_store is not None:
            signal_store_status = "healthy"
        elif _pipeline and _pipeline._signal_store is None:
            signal_store_status = "degraded"

        # Processing queue depth (placeholder — real impl uses Service Bus client)
        queue_depth = 0
        queue_status = "healthy"

        # Audit store
        audit_status = "healthy"
        audit_buffer_depth = 0
        if app.state.audit_writer:
            audit_status = app.state.audit_writer.get_status()
            audit_buffer_depth = app.state.audit_writer.buffer_depth

        # Overall status determination per contracts/health-endpoint.md
        overall = "healthy"
        if queue_status == "offline":
            overall = "unhealthy"
        elif any(x != "healthy" for x in [llm_status, signal_store_status, queue_status, audit_status]):
            overall = "degraded"

        return _HealthResponse(
            status=overall,
            agent_version=_config.agent_version,
            timestamp=now.isoformat(),
            checks=_HealthChecks(
                llm_connectivity=_HealthCheckDetail(
                    status=llm_status,
                    last_checked_at=now.isoformat(),
                    latency_ms=llm_latency,
                ),
                signal_store=_HealthCheckDetail(
                    status=signal_store_status,
                    last_checked_at=now.isoformat(),
                ),
                processing_queue=_ProcessingQueueDetail(
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
        """Incident commander override of recommendation status.

        Per contracts/health-endpoint.md:
        - approve: recommendation approved for execution
        - reject: recommendation rejected
        - modify: create new version linked to original
        """
        request = override_request
        now = datetime.now(UTC)

        # Validate action
        valid_actions = {"approve", "reject", "modify"}
        if request.action not in valid_actions:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid action '{request.action}'. Must be one of: {valid_actions}",
            )

        # Map action to new status
        status_map = {
            "approve": "approved",
            "reject": "rejected",
            "modify": "modified",
        }
        new_status = status_map[request.action]

        # Attempt to retrieve existing recommendation from store
        rec_store = app.state.recommendation_store
        previous_status = "proposed"  # default assumption

        if rec_store is not None:
            try:
                doc = rec_store.read_item(
                    item=request.recommendation_id,
                    partition_key=request.recommendation_id,
                )
                previous_status = doc.get("status", "proposed")

                # Update recommendation status
                doc["status"] = new_status
                doc["override_by_user_id"] = request.user_id
                doc["override_by_role"] = request.role
                doc["override_justification"] = request.justification
                doc["override_timestamp"] = now.isoformat()
                if request.action == "modify" and request.modifications:
                    doc.update(request.modifications)

                rec_store.upsert_item(body=doc)
            except Exception as exc:
                error_str = str(exc)
                if "NotFound" in error_str or "404" in error_str:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Recommendation {request.recommendation_id} not found",
                    )
                if "PreconditionFailed" in error_str or "412" in error_str:
                    raise HTTPException(
                        status_code=409,
                        detail="Concurrent override conflict — retry",
                    )
                raise HTTPException(status_code=503, detail=str(exc))

        # Write audit record
        audit_record = RiskAssessmentDecisionRecord(
            handoff_id=f"override-{request.recommendation_id}",
            recommendation_id=request.recommendation_id,
            decision_type=DecisionType.recommendation_generated,
            decision_rationale=(
                f"Override by {request.user_id} ({request.role}): {request.action} — {request.justification}"
            ),
            generation_method="human_override",
            agent_version=_config.agent_version,
            configuration_version=_config.compute_config_hash(),
        )

        if app.state.audit_writer:
            app.state.audit_writer.write(audit_record)

        return _OverrideResponse(
            recommendation_id=request.recommendation_id,
            previous_status=previous_status,
            new_status=new_status,
            override_timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
        )

    return app


# ---------------------------------------------------------------------------
# Entrypoint — FastAPI-based health server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    from apps.console_logging import configure_console_logging, uvicorn_log_config

    configure_console_logging()

    _PORT = int(os.environ.get("PORT", "8081"))
    _config = RiskAssessmentConfig()
    _agent = RiskAssessmentAgent(config=_config)

    app = create_app(agent=_agent, config=_config)

    logger.info("Risk Assessment Agent health server starting on port %d", _PORT)
    uvicorn.run(app, host="0.0.0.0", port=_PORT, log_level="info", log_config=uvicorn_log_config())
