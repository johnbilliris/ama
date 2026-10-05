"""Assessment Processing Pipeline — 9-stage orchestrator per contracts/assessment-pipeline.md.

Stages:
1. Handoff Intake and Validation
2. Signal Retrieval
3. Multi-Source Correlation
4. Contradiction Detection
5. Trend Extrapolation (predictive lead time estimation)
6. Assessment Generation (version, severity, summary, persistence)
7. Recommendation Generation
8. Downstream Escalation (Communication, Evacuation, Resource Allocation)
9. Audit Finalisation

Each stage produces audit records (RiskAssessmentDecisionRecord) and emits metrics.
"""

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Protocol

from common.async_bridge import run_async
from common.handoffs import AgentHandoffEvent, deliver_handoff_with_retry
from risk_assessment.agent import RiskAssessmentAgent
from risk_assessment.audit import AuditWriter
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.correlation import (
    ContradictionDetector,
    ContradictionResult,
    CorrelationResult,
    RiskSignal,
    SignalCorrelator,
)
from risk_assessment.dedup import HandoffDeduplicator
from risk_assessment.extrapolation import ExtrapolationResult, extrapolate_hazard_trend
from risk_assessment.models import DecisionType, RiskAssessmentDecisionRecord
from risk_assessment.severity import SeverityComputer
from risk_assessment.telemetry import CustomEventEmitter, metrics, pipeline_span
from risk_assessment.versioning import VersionCounter

from packages.domain.src.domain.models.hazard_assessment import HazardAssessment
from packages.domain.src.domain.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class RiskAssessmentContainer(Protocol):
    def read_item(self, *, item: str, partition_key: str) -> dict[str, object]: ...

    def create_item(self, *, body: dict[str, object]) -> object: ...


def _persist_dead_letter_entry(handoff: AgentHandoffEvent) -> str:
    from app.services.dead_letter_service import DeadLetterService

    entry = DeadLetterService().create_entry(
        entry_type="handoff_failure",
        correlation_id=f"handoff:{handoff.handoff_id}",
        original_payload=handoff.model_dump(mode="json"),
        failure_reason=handoff.failure_reason or "handoff delivery exhausted",
        failure_code="MAX_RETRIES_EXCEEDED",
        source_service=handoff.source_agent,
        target_service=handoff.target_agent,
        tenant_scope_key=handoff.scope_key,
        incident_id=handoff.incident_id,
        retry_count=max(handoff.retry_count, 0),
    )
    return entry.entry_id


def _build_scope_key(tenant_id: str, incident_id: str) -> str:
    """Build the Cosmos DB partition key."""
    return f"{tenant_id}:{incident_id}"


def _signal_float(raw: dict[str, object], field: str, alternate: str, default: float) -> float:
    value = raw.get(field, raw.get(alternate, default))
    if isinstance(value, (int, float, str, bytes)):
        return float(value)
    raise TypeError(f"Signal field '{field}' must be numeric")


class AssessmentProcessingPipeline:
    """Orchestrates the 8-stage assessment processing pipeline."""

    def __init__(
        self,
        config: RiskAssessmentConfig | None = None,
        deduplicator: HandoffDeduplicator | None = None,
        correlator: SignalCorrelator | None = None,
        contradiction_detector: ContradictionDetector | None = None,
        severity_computer: SeverityComputer | None = None,
        version_counter: VersionCounter | None = None,
        audit_writer: AuditWriter | None = None,
        agent: RiskAssessmentAgent | None = None,
        signal_store: RiskAssessmentContainer | None = None,
        assessment_store: RiskAssessmentContainer | None = None,
        recommendation_store: RiskAssessmentContainer | None = None,
        deliver_fn: Callable[[AgentHandoffEvent], Awaitable[None]] | None = None,
        on_dead_letter_fn: Callable[[AgentHandoffEvent], str] | None = None,
    ) -> None:
        self._config = config or RiskAssessmentConfig()
        self._deduplicator = deduplicator or HandoffDeduplicator(
            window_minutes=self._config.handoff_dedup_window_minutes
        )
        self._correlator = correlator or SignalCorrelator(self._config)
        self._contradiction_detector = contradiction_detector or ContradictionDetector(self._config)
        self._severity_computer = severity_computer or SeverityComputer()
        self._version_counter = version_counter or VersionCounter()
        self._audit_writer = audit_writer or AuditWriter(self._config)
        self._agent = agent or RiskAssessmentAgent(self._config)
        self._signal_store = signal_store
        self._assessment_store = assessment_store
        self._recommendation_store = recommendation_store
        self._deliver_fn = deliver_fn
        self._on_dead_letter_fn = on_dead_letter_fn or _persist_dead_letter_entry

        # Counters for metrics
        self._handoff_count = 0
        self._assessment_count = 0
        self._recommendation_count = 0
        self._escalation_count = 0
        self._rejection_count = 0
        self._dedup_discard_count = 0
        self._dead_letter_count = 0
        self._sla_breach_count = 0
        self._contradiction_count = 0
        self._fallback_count = 0

    # ------------------------------------------------------------------
    # Stage 1: Handoff Intake and Validation
    # ------------------------------------------------------------------

    def _validate_handoff(
        self,
        handoff: AgentHandoffEvent,
        tenant_id: str,
    ) -> bool:
        """Stage 1: Validate incoming handoff."""
        scope_key = _build_scope_key(tenant_id, handoff.incident_id)

        # Check target agent
        if handoff.target_agent != "risk_assessment":
            self._rejection_count += 1
            metrics.inc_handoff_rejected()
            self._write_audit(
                RiskAssessmentDecisionRecord(
                    handoff_id=handoff.handoff_id,
                    decision_type=DecisionType.handoff_rejected,
                    confidence_raw=handoff.confidence,
                    confidence_adjusted=handoff.confidence,
                    decision_rationale=(
                        f"Handoff rejected: target_agent={handoff.target_agent}, expected risk_assessment"
                    ),
                    generation_method="n/a",
                    agent_version=self._config.agent_version,
                    configuration_version=self._config.compute_config_hash(),
                    incident_scope_key=scope_key,
                    tenant_id=tenant_id,
                )
            )
            return False

        # Check idempotency
        if self._deduplicator.is_duplicate(handoff.handoff_id):
            self._dedup_discard_count += 1
            metrics.inc_duplicate_discard()
            self._write_audit(
                RiskAssessmentDecisionRecord(
                    handoff_id=handoff.handoff_id,
                    decision_type=DecisionType.duplicate_discarded,
                    confidence_raw=handoff.confidence,
                    confidence_adjusted=handoff.confidence,
                    decision_rationale=f"Duplicate handoff discarded: {handoff.handoff_id}",
                    generation_method="n/a",
                    agent_version=self._config.agent_version,
                    configuration_version=self._config.compute_config_hash(),
                    incident_scope_key=scope_key,
                    tenant_id=tenant_id,
                )
            )
            return False

        # Record handoff received
        self._handoff_count += 1
        self._write_audit(
            RiskAssessmentDecisionRecord(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.handoff_received,
                confidence_raw=handoff.confidence,
                confidence_adjusted=handoff.confidence,
                decision_rationale=(f"Handoff received from {handoff.source_agent} for incident {handoff.incident_id}"),
                generation_method="n/a",
                agent_version=self._config.agent_version,
                configuration_version=self._config.compute_config_hash(),
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
        )
        return True

    # ------------------------------------------------------------------
    # Stage 2: Signal Retrieval
    # ------------------------------------------------------------------

    def _retrieve_signals(
        self,
        handoff: AgentHandoffEvent,
        tenant_id: str,
    ) -> list[RiskSignal]:
        # RAG-OPTOUT [FR-RAG-NS-03]: GA seismic-feed signals are authoritative; doctrine grounding moves to the downstream assessment call. ADR: docs/decisions/036-foundry-rag-grounding/03-rag-optout-ga-live.md  # noqa: E501
        """Stage 2: Retrieve signals from signal store.

        Handles partial unavailability by proceeding with available signals.
        """
        scope_key = _build_scope_key(tenant_id, handoff.incident_id)
        payload = handoff.payload or {}

        # Extract signal IDs from payload
        signal_summary = payload.get("signalSummary", {})
        signal_ids: list[str] = []
        if isinstance(signal_summary, dict):
            signal_ids = signal_summary.get("signal_ids", [])
        if not signal_ids:
            signal_ids = payload.get("signal_ids", [])
        stored_signal_refs = payload.get("stored_signal_refs", [])
        if not isinstance(stored_signal_refs, list):
            stored_signal_refs = []
        evidence_snapshot = payload.get("evidence_snapshot", {})
        snapshot_signals = evidence_snapshot.get("signals", []) if isinstance(evidence_snapshot, dict) else []

        # Extract signal info directly from the handoff payload for immediate use
        category = str(payload.get("category", signal_summary.get("category", "fire")))
        source_kind = str(payload.get("sourceKind", signal_summary.get("sourceKind", "authoritative")))

        signals: list[RiskSignal] = []
        missing_count = 0

        if self._signal_store is not None:
            used_hpk_refs = False
            if hasattr(self._signal_store, "get_by_hpk") and stored_signal_refs:
                used_hpk_refs = True
                for ref in stored_signal_refs:
                    if not isinstance(ref, dict):
                        continue
                    sid = str(ref.get("signal_id") or "").strip()
                    scope = str(ref.get("scope") or tenant_id).strip() or tenant_id
                    jurisdiction_id = str(ref.get("jurisdiction_id") or "national").strip() or "national"
                    data_source_id = str(ref.get("data_source_id") or "").strip()
                    if not sid or not data_source_id:
                        missing_count += 1
                        continue
                    try:
                        maybe_sig = self._signal_store.get_by_hpk(
                            signal_id=sid,
                            scope=scope,
                            jurisdiction_id=jurisdiction_id,
                            data_source_id=data_source_id,
                        )
                        sig = run_async(maybe_sig) if inspect.isawaitable(maybe_sig) else maybe_sig
                        if sig is None:
                            raise KeyError(sid)
                        signals.append(self._normalize_signal(sig))
                    except Exception:
                        missing_count += 1
                        logger.warning("Signal %s not retrievable via exact reference", sid)

            if not used_hpk_refs:
                for sid in signal_ids:
                    try:
                        sig = self._signal_store.read_item(item=sid, partition_key=handoff.incident_id)
                        signals.append(self._normalize_signal(sig))
                    except Exception:
                        missing_count += 1
                        logger.warning("Signal %s not retrievable", sid)
        elif signal_ids:
            # No signal store — use bounded handoff snapshot evidence for traceability.
            snapshot_by_id = {
                str(item.get("signal_id")): item
                for item in snapshot_signals
                if isinstance(item, dict) and item.get("signal_id")
            }
            for sid in signal_ids:
                snapshot = snapshot_by_id.get(sid, {})
                signals.append(
                    {
                        "signal_id": sid,
                        "confidence_score": handoff.confidence,
                        "freshness_score": 1.0,
                        "source_kind": snapshot.get("source_kind", source_kind),
                        "category": snapshot.get("category", category),
                        "risk_direction": "increasing",
                        "hazard_parameter": "general",
                        "payload": snapshot.get("payload", {}),
                        "provenance": snapshot.get("provenance", {}),
                        "evidence_state": "snapshot",
                    }
                )
        else:
            # No signal IDs provided — explicit unevidenced state (never a synthetic signal id).
            signals.append(
                {
                    "signal_id": "unevidenced",
                    "confidence_score": handoff.confidence,
                    "freshness_score": 1.0,
                    "source_kind": source_kind,
                    "category": category,
                    "risk_direction": "increasing",
                    "hazard_parameter": "general",
                    "payload": payload,
                    "provenance": {},
                    "evidence_state": "unevidenced",
                }
            )

        signal_ids_retrieved = [s["signal_id"] for s in signals]
        total = len(signal_ids) if signal_ids else len(signals)

        self._write_audit(
            RiskAssessmentDecisionRecord(
                handoff_id=handoff.handoff_id,
                input_signal_ids=signal_ids_retrieved,
                decision_type=DecisionType.signals_retrieved,
                confidence_raw=handoff.confidence,
                confidence_adjusted=handoff.confidence,
                decision_rationale=(f"Retrieved {len(signals)}/{total} signals (missing: {missing_count})"),
                generation_method="n/a",
                agent_version=self._config.agent_version,
                configuration_version=self._config.compute_config_hash(),
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
        )

        return signals

    def _normalize_signal(self, raw: dict[str, object]) -> RiskSignal:
        """Normalize a raw signal document to the expected dict format."""
        provenance_value = raw.get("provenance", {})
        if not isinstance(provenance_value, dict):
            raise TypeError("Signal provenance must be a mapping")
        disaster_type = raw.get("disaster_type")
        return {
            "signal_id": str(raw.get("signal_id", raw.get("id", "unknown"))),
            "confidence_score": _signal_float(raw, "confidence_score", "confidenceScore", 0.0),
            "freshness_score": _signal_float(raw, "freshness_score", "freshnessScore", 1.0),
            "source_kind": str(raw.get("source_kind", raw.get("sourceKind", "social"))),
            "category": str(raw.get("category", "fire")),
            "risk_direction": str(raw.get("risk_direction", raw.get("riskDirection", "increasing"))),
            "hazard_parameter": str(raw.get("hazard_parameter", "general")),
            "payload": raw.get("payload", {}),
            "provenance": {str(key): value for key, value in provenance_value.items()},
            "disaster_type": disaster_type if isinstance(disaster_type, str) else None,
            "evidence_state": str(raw.get("evidence_state", "retrieved")),
        }

    # ------------------------------------------------------------------
    # Stage 3: Multi-Source Correlation
    # ------------------------------------------------------------------

    def _correlate_signals(
        self,
        signals: list[RiskSignal],
    ) -> CorrelationResult:
        """Stage 3: Compute weighted confidence from multi-source signals."""
        return self._correlator.compute_weighted_confidence(signals)

    # ------------------------------------------------------------------
    # Stage 4: Contradiction Detection
    # ------------------------------------------------------------------

    def _detect_contradictions(
        self,
        signals: list[RiskSignal],
        handoff_id: str,
        tenant_id: str,
        incident_id: str,
    ) -> ContradictionResult:
        """Stage 4: Detect contradictory signals."""
        result = self._contradiction_detector.detect(signals)

        if result.detected:
            self._contradiction_count += 1
            scope_key = _build_scope_key(tenant_id, incident_id)
            self._write_audit(
                RiskAssessmentDecisionRecord(
                    handoff_id=handoff_id,
                    input_signal_ids=[s.get("signal_id", "") for s in signals],
                    decision_type=DecisionType.contradiction_detected,
                    confidence_raw=0.0,
                    confidence_adjusted=0.0,
                    decision_rationale=(
                        f"Contradictory signals detected: {len(result.pairs)} pair(s). "
                        f"Confidence will be reduced by "
                        f"{(1 - self._config.contradiction_reduction_factor) * 100:.0f}%."
                    ),
                    generation_method="n/a",
                    agent_version=self._config.agent_version,
                    configuration_version=self._config.compute_config_hash(),
                    incident_scope_key=scope_key,
                    tenant_id=tenant_id,
                )
            )

        return result

    # ------------------------------------------------------------------
    # Stage 5: Trend Extrapolation
    # ------------------------------------------------------------------

    def _extrapolate_trend(
        self,
        signals: list[RiskSignal],
        handoff_id: str,
        tenant_id: str,
        incident_id: str,
    ) -> ExtrapolationResult:
        """Stage 5: Extrapolate hazard trend to estimate predictive lead time."""
        if not self._config.extrapolation_enabled:
            return ExtrapolationResult()

        category = signals[0].get("category", "fire") if signals else "fire"
        result = extrapolate_hazard_trend(
            signals=signals,
            category=category,
            min_points=self._config.extrapolation_min_points,
        )

        if result.trend_detected:
            scope_key = _build_scope_key(tenant_id, incident_id)
            lead_time_msg = f"Trend extrapolation: {result.trend_direction} at {result.slope_per_hour:.4f}/hr. "
            if result.hours_to_warning_threshold is not None:
                lead_time_msg += f"Warning threshold breach in ~{result.hours_to_warning_threshold:.1f}h. "
            if result.hours_to_emergency_threshold is not None:
                lead_time_msg += f"Emergency threshold breach in ~{result.hours_to_emergency_threshold:.1f}h. "
            lead_time_msg += f"Predictive lead time: {result.predictive_lead_time_hours:.1f}h."

            logger.info(lead_time_msg)
            self._write_audit(
                RiskAssessmentDecisionRecord(
                    handoff_id=handoff_id,
                    input_signal_ids=[s.get("signal_id", "") for s in signals],
                    decision_type=DecisionType.assessment_generated,
                    confidence_raw=result.current_value,
                    confidence_adjusted=result.extrapolation_confidence,
                    decision_rationale=lead_time_msg,
                    generation_method="extrapolation",
                    agent_version=self._config.agent_version,
                    configuration_version=self._config.compute_config_hash(),
                    incident_scope_key=scope_key,
                    tenant_id=tenant_id,
                )
            )

        return result

    # ------------------------------------------------------------------
    # Stage 6: Assessment Generation
    # ------------------------------------------------------------------

    def _generate_assessment(
        self,
        handoff: AgentHandoffEvent,
        signals: list[RiskSignal],
        correlation: CorrelationResult,
        contradiction: ContradictionResult,
        tenant_id: str,
        extrapolation: ExtrapolationResult | None = None,
    ) -> HazardAssessment:
        """Stage 5: Generate versioned hazard assessment."""
        scope_key = _build_scope_key(tenant_id, handoff.incident_id)
        signal_category = signals[0].get("category", "fire") if signals else "fire"
        assessment_type = self._severity_computer.derive_assessment_type(signal_category)

        # Assign version via optimistic concurrency
        version = run_async(
            self._version_counter.assign_version(
                incident_id=handoff.incident_id,
                assessment_type=assessment_type,
                incident_scope_key=scope_key,
            )
        )

        config_hash = self._config.compute_config_hash()

        assessment = self._agent.generate_assessment(
            incident_id=handoff.incident_id,
            signals=signals,
            correlation=correlation,
            contradiction=contradiction,
            assessment_type=assessment_type,
            version=version,
            config_hash=config_hash,
            tenant_id=tenant_id,
            extrapolation=extrapolation,
        )

        # Persist assessment
        if self._assessment_store is not None:
            try:
                doc = assessment.model_dump(mode="json")
                doc["id"] = assessment.hazard_assessment_id
                self._assessment_store.create_item(body=doc)
            except Exception:
                logger.error("Failed to persist assessment %s", assessment.hazard_assessment_id)

        self._assessment_count += 1
        self._write_audit(
            RiskAssessmentDecisionRecord(
                handoff_id=handoff.handoff_id,
                input_signal_ids=assessment.input_signal_ids,
                assessment_id=assessment.hazard_assessment_id,
                hazard_type=signal_category,
                severity_level=assessment.severity_level,
                confidence_raw=correlation.weighted_confidence,
                confidence_adjusted=assessment.confidence_adjusted,
                version=assessment.version,
                decision_type=DecisionType.assessment_generated,
                model_id=assessment.model_deployment_id,
                processing_duration_ms=0.0,
                decision_rationale=(
                    f"Assessment {assessment.hazard_assessment_id} generated: "
                    f"type={assessment_type}, severity={assessment.severity_level}, "
                    f"confidence={assessment.confidence_adjusted:.3f}, "
                    f"version={assessment.version}, "
                    f"method={assessment.generation_method}"
                ),
                generation_method=assessment.generation_method,
                agent_version=self._config.agent_version,
                configuration_version=config_hash,
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
        )

        if assessment.generation_method == "template_fallback":
            self._fallback_count += 1

        return assessment

    # ------------------------------------------------------------------
    # Stage 7: Recommendation Generation
    # ------------------------------------------------------------------

    def _generate_recommendations(
        self,
        handoff: AgentHandoffEvent,
        assessment: HazardAssessment,
        signals: list[RiskSignal],
        tenant_id: str,
    ) -> list[Recommendation]:
        """Stage 7: Generate recommendations from assessment."""
        scope_key = _build_scope_key(tenant_id, handoff.incident_id)
        recommendations = self._agent.generate_recommendations(assessment, signals)

        for rec in recommendations:
            # Persist recommendation
            if self._recommendation_store is not None:
                try:
                    doc = rec.model_dump(mode="json")
                    doc["id"] = rec.recommendation_id
                    self._recommendation_store.create_item(body=doc)
                except Exception:
                    logger.error("Failed to persist recommendation %s", rec.recommendation_id)

            self._recommendation_count += 1
            self._write_audit(
                RiskAssessmentDecisionRecord(
                    handoff_id=handoff.handoff_id,
                    input_signal_ids=rec.supporting_signal_ids,
                    assessment_id=assessment.hazard_assessment_id,
                    recommendation_id=rec.recommendation_id,
                    severity_level=rec.severity_level,
                    confidence_raw=assessment.confidence_score,
                    confidence_adjusted=rec.confidence_score,
                    decision_type=DecisionType.recommendation_generated,
                    decision_rationale=(
                        f"Recommendation {rec.recommendation_id} generated: "
                        f"type={rec.type}, confidence={rec.confidence_score:.3f}, "
                        f"method={rec.generation_method}"
                    ),
                    generation_method=rec.generation_method,
                    agent_version=self._config.agent_version,
                    configuration_version=self._config.compute_config_hash(),
                    incident_scope_key=scope_key,
                    tenant_id=tenant_id,
                )
            )

        return recommendations

    # ------------------------------------------------------------------
    # Stage 8: Downstream Escalation
    # ------------------------------------------------------------------

    def _evaluate_escalation(
        self,
        handoff: AgentHandoffEvent,
        assessment: HazardAssessment,
        recommendations: list[Recommendation],
        tenant_id: str,
        *,
        all_stale: bool = False,
    ) -> list[AgentHandoffEvent]:
        """Stage 8: Evaluate and deliver downstream escalation handoffs.

        Simulation tenants do NOT trigger live downstream handoffs.
        """
        scope_key = _build_scope_key(tenant_id, handoff.incident_id)
        handoffs: list[AgentHandoffEvent] = []

        if all_stale:
            logger.info(
                "Suppressing downstream escalation for all-stale assessment %s", assessment.hazard_assessment_id
            )
            return handoffs

        # Block simulation → live escalation
        if tenant_id != "live" and tenant_id.startswith("sim"):
            logger.info("Simulation tenant %s — skipping live escalation", tenant_id)
            return handoffs

        for rec in recommendations:
            downstream_handoffs = []

            # Communication Agent escalation (public_alert, confidence ≥ 0.7)
            comm_handoff = self._agent.build_communication_handoff(rec)
            if comm_handoff:
                downstream_handoffs.append(("communication", comm_handoff))

            # Evacuation Agent escalation (severity ≥ high AND confidence ≥ 0.6)
            evac_handoff = self._agent.build_evacuation_handoff(rec)
            if evac_handoff:
                downstream_handoffs.append(("evacuation", evac_handoff))

            # Resource Allocation Agent escalation (coordination tasks)
            ra_handoff = self._agent.build_resource_allocation_handoff(rec)
            if ra_handoff:
                downstream_handoffs.append(("resource_allocation", ra_handoff))

            for target_name, downstream in downstream_handoffs:
                # Record handoff created
                self._write_audit(
                    RiskAssessmentDecisionRecord(
                        handoff_id=handoff.handoff_id,
                        assessment_id=assessment.hazard_assessment_id,
                        recommendation_id=rec.recommendation_id,
                        decision_type=DecisionType.handoff_created,
                        confidence_raw=rec.confidence_score,
                        confidence_adjusted=rec.confidence_score,
                        escalation_targets=[target_name],
                        decision_rationale=(
                            f"Handoff created for {target_name}: "
                            f"rec={rec.recommendation_id}, "
                            f"confidence={rec.confidence_score:.3f}"
                        ),
                        generation_method="n/a",
                        agent_version=self._config.agent_version,
                        configuration_version=self._config.compute_config_hash(),
                        incident_scope_key=scope_key,
                        tenant_id=tenant_id,
                    )
                )

                # Deliver handoff
                if self._deliver_fn is not None:
                    delivered = run_async(
                        deliver_handoff_with_retry(
                            handoff=downstream,
                            deliver=self._deliver_fn,
                            on_dead_letter=self._on_dead_letter_fn,
                        )
                    )

                    if delivered.status == "delivered":
                        self._escalation_count += 1
                        metrics.inc_escalation(target_name)
                        CustomEventEmitter.escalation_triggered(
                            target_agent=target_name,
                            recommendation_id=rec.recommendation_id,
                            confidence=rec.confidence_score,
                        )
                        self._write_audit(
                            RiskAssessmentDecisionRecord(
                                handoff_id=handoff.handoff_id,
                                assessment_id=assessment.hazard_assessment_id,
                                recommendation_id=rec.recommendation_id,
                                decision_type=DecisionType.handoff_delivered,
                                confidence_raw=rec.confidence_score,
                                confidence_adjusted=rec.confidence_score,
                                escalation_targets=[target_name],
                                decision_rationale=(f"Handoff delivered to {target_name}: {delivered.handoff_id}"),
                                generation_method="n/a",
                                agent_version=self._config.agent_version,
                                configuration_version=self._config.compute_config_hash(),
                                incident_scope_key=scope_key,
                                tenant_id=tenant_id,
                            )
                        )
                    else:
                        self._dead_letter_count += 1
                        metrics.inc_dead_letter()
                        self._write_audit(
                            RiskAssessmentDecisionRecord(
                                handoff_id=handoff.handoff_id,
                                assessment_id=assessment.hazard_assessment_id,
                                recommendation_id=rec.recommendation_id,
                                decision_type=DecisionType.handoff_dead_lettered,
                                confidence_raw=rec.confidence_score,
                                confidence_adjusted=rec.confidence_score,
                                escalation_targets=[target_name],
                                decision_rationale=(
                                    f"Handoff dead-lettered for {target_name} after "
                                    f"{delivered.retry_count} retries: "
                                    f"{delivered.failure_reason}"
                                ),
                                generation_method="n/a",
                                agent_version=self._config.agent_version,
                                configuration_version=self._config.compute_config_hash(),
                                incident_scope_key=scope_key,
                                tenant_id=tenant_id,
                            )
                        )

                handoffs.append(downstream)

            # No-escalation path: store for human review only
            if not downstream_handoffs:
                logger.info(
                    "Recommendation %s below all escalation thresholds — stored for human review",
                    rec.recommendation_id,
                )

        return handoffs

    # ------------------------------------------------------------------
    # Top-level orchestrator
    # ------------------------------------------------------------------

    def process_handoff(
        self,
        handoff: AgentHandoffEvent,
        tenant_id: str | None = None,
    ) -> dict[str, object]:
        """Process a handoff through all 9 pipeline stages.

        Returns a result dict with assessment, recommendations, and handoffs.
        Instrumented with OpenTelemetry spans, metrics, and custom events.
        """
        start = time.perf_counter()
        effective_tenant = tenant_id or handoff.tenant_id

        result: dict[str, object] = {
            "handoff_id": handoff.handoff_id,
            "assessment": None,
            "recommendations": [],
            "handoffs": [],
            "status": "pending",
        }

        with pipeline_span("risk_assessment.process_handoff", handoff.handoff_id) as root_span:
            # Stage 1: Validation
            with pipeline_span("risk_assessment.validate_handoff", handoff.handoff_id):
                if not self._validate_handoff(handoff, effective_tenant):
                    result["status"] = "rejected"
                    return result
                # Emit custom event + metric
                CustomEventEmitter.handoff_received(
                    handoff.handoff_id,
                    handoff.incident_id,
                    effective_tenant,
                )
                metrics.inc_handoff_intake()

            # Stage 2: Signal Retrieval
            with pipeline_span("risk_assessment.retrieve_signals", handoff.handoff_id):
                signals = self._retrieve_signals(handoff, effective_tenant)

                if not signals:
                    self._write_audit(
                        RiskAssessmentDecisionRecord(
                            handoff_id=handoff.handoff_id,
                            decision_type=DecisionType.degradation_detected,
                            decision_rationale="All signals missing — degraded assessment",
                            generation_method="n/a",
                            agent_version=self._config.agent_version,
                            configuration_version=self._config.compute_config_hash(),
                            incident_scope_key=_build_scope_key(effective_tenant, handoff.incident_id),
                            tenant_id=effective_tenant,
                        )
                    )
                    CustomEventEmitter.degradation_event("signal_store", 1)

            # Stage 3: Multi-Source Correlation
            with pipeline_span("risk_assessment.correlate_signals", handoff.handoff_id):
                correlation = self._correlator.compute_weighted_confidence(signals)

            # Stage 4: Contradiction Detection
            with pipeline_span("risk_assessment.detect_contradictions", handoff.handoff_id):
                contradiction = self._detect_contradictions(
                    signals,
                    handoff.handoff_id,
                    effective_tenant,
                    handoff.incident_id,
                )
                if contradiction.detected:
                    signal_ids = [s.get("signal_id", "") for s in signals]
                    sources = set()
                    for pair in contradiction.pairs:
                        sources.add(pair.source_a)
                        sources.add(pair.source_b)
                    CustomEventEmitter.contradiction_detected(
                        signal_ids=signal_ids,
                        source_names=sorted(sources),
                        confidence_reduction=1 - self._config.contradiction_reduction_factor,
                    )

            # Stage 5: Trend Extrapolation
            with pipeline_span("risk_assessment.extrapolate_trend", handoff.handoff_id):
                extrapolation = self._extrapolate_trend(
                    signals,
                    handoff.handoff_id,
                    effective_tenant,
                    handoff.incident_id,
                )
                result["extrapolation"] = extrapolation
                if extrapolation.trend_detected:
                    CustomEventEmitter.assessment_generated(
                        assessment_id=f"extrap-{handoff.handoff_id}",
                        confidence=extrapolation.extrapolation_confidence,
                        severity="n/a",
                        generation_method="extrapolation",
                    )

            # Stage 6: Assessment Generation
            with pipeline_span("risk_assessment.generate_assessment", handoff.handoff_id):
                assessment = self._generate_assessment(
                    handoff,
                    signals,
                    correlation,
                    contradiction,
                    effective_tenant,
                    extrapolation=extrapolation,
                )
                result["assessment"] = assessment
                metrics.inc_assessment_count()
                metrics.record_confidence(assessment.confidence_adjusted)
                metrics.record_severity(assessment.severity_level)
                CustomEventEmitter.assessment_generated(
                    assessment_id=assessment.hazard_assessment_id,
                    confidence=assessment.confidence_adjusted,
                    severity=assessment.severity_level,
                    generation_method=assessment.generation_method,
                )
                if assessment.generation_method == "template_fallback":
                    metrics.inc_fallback()
                    CustomEventEmitter.degradation_event("llm", 1)

            # Stage 7: Recommendation Generation
            with pipeline_span("risk_assessment.generate_recommendations", handoff.handoff_id):
                recommendations = self._generate_recommendations(
                    handoff,
                    assessment,
                    signals,
                    effective_tenant,
                )
                result["recommendations"] = recommendations

            # Stage 8: Downstream Escalation
            with pipeline_span("risk_assessment.evaluate_escalation", handoff.handoff_id):
                downstream_handoffs = self._evaluate_escalation(
                    handoff,
                    assessment,
                    recommendations,
                    effective_tenant,
                    all_stale=correlation.all_stale,
                )
                result["handoffs"] = downstream_handoffs

            # Stage 9: Audit Finalisation
            with pipeline_span("risk_assessment.write_audit", handoff.handoff_id):
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                metrics.record_assessment_latency(elapsed_ms)

                if elapsed_ms > 10_000:
                    self._sla_breach_count += 1
                    metrics.inc_sla_breach()
                    CustomEventEmitter.sla_breach(handoff.handoff_id, elapsed_ms)
                    logger.warning(
                        "SLA BREACH: handoff %s processed in %.2fms (>10s SLA)",
                        handoff.handoff_id,
                        elapsed_ms,
                    )

            result["status"] = "completed"
            result["elapsed_ms"] = elapsed_ms

            root_span.set_attribute("status", "completed")
            root_span.set_attribute("elapsed_ms", elapsed_ms)
            root_span.set_attribute("assessment_id", assessment.hazard_assessment_id)
            root_span.set_attribute("recommendation_count", len(recommendations))
            root_span.set_attribute("escalation_count", len(downstream_handoffs))

        logger.info(
            "Pipeline completed for handoff %s in %.2fms: assessment=%s, recommendations=%d, escalations=%d",
            handoff.handoff_id,
            elapsed_ms,
            assessment.hazard_assessment_id,
            len(recommendations),
            len(downstream_handoffs),
        )

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_audit(self, record: RiskAssessmentDecisionRecord) -> None:
        """Write an audit record through the audit writer."""
        self._audit_writer.write(record)

    # ------------------------------------------------------------------
    # Metrics accessors
    # ------------------------------------------------------------------

    @property
    def handoff_count(self) -> int:
        return self._handoff_count

    @property
    def assessment_count(self) -> int:
        return self._assessment_count

    @property
    def recommendation_count(self) -> int:
        return self._recommendation_count

    @property
    def escalation_count(self) -> int:
        return self._escalation_count

    @property
    def rejection_count(self) -> int:
        return self._rejection_count

    @property
    def dedup_discard_count(self) -> int:
        return self._dedup_discard_count

    @property
    def dead_letter_count(self) -> int:
        return self._dead_letter_count

    @property
    def sla_breach_count(self) -> int:
        return self._sla_breach_count

    @property
    def contradiction_count(self) -> int:
        return self._contradiction_count

    @property
    def fallback_count(self) -> int:
        return self._fallback_count
