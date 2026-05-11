"""Signal Processing Pipeline — 6-stage orchestrator per contracts/signal-processing.md.

Stages:
1. Input Validation
2. Deduplication Check
3. Freshness Assessment
4. Misinformation Evaluation (conditional)
5. Signal Summarisation
6. Confidence-Based Triage

Each stage produces audit records (MonitoringDecisionRecord) and emits metrics.
"""

from __future__ import annotations

import hashlib
import logging
import time

from app.validators.signal_envelope import SignalEnvelope
from common.async_bridge import run_async  # noqa: F401 — kept for downstream pipeline compatibility
from common.content_safety import ContentSafetyValidator
from common.handoffs import AgentHandoffEvent, deliver_handoff_with_retry
from monitoring.agent import MonitoringAgent
from monitoring.audit import AuditWriter
from monitoring.config import MonitoringConfig
from monitoring.dedup import SignalDeduplicator
from monitoring.freshness import DataFreshnessTracker
from monitoring.models import DecisionType, MonitoringDecisionRecord
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def _build_scope_key(tenant_id: str, incident_id: str | None, signal_id: str) -> str:
    """Build the Cosmos DB partition key."""
    if incident_id:
        return f"{tenant_id}:{incident_id}"
    suffix = hashlib.md5(signal_id.encode()).hexdigest()[:8]
    return f"{tenant_id}:unassociated:{suffix}"


class SignalProcessingPipeline:
    """Orchestrates the 6-stage signal processing pipeline."""

    def __init__(
        self,
        config: MonitoringConfig | None = None,
        deduplicator: SignalDeduplicator | None = None,
        freshness_tracker: DataFreshnessTracker | None = None,
        audit_writer: AuditWriter | None = None,
        agent: MonitoringAgent | None = None,
        content_safety: ContentSafetyValidator | None = None,
        deliver_fn=None,
        on_dead_letter_fn=None,
    ) -> None:
        self._config = config or MonitoringConfig()
        self._deduplicator = deduplicator or SignalDeduplicator(window_minutes=self._config.signal_dedup_window_minutes)
        self._freshness_tracker = freshness_tracker or DataFreshnessTracker(self._config)
        self._audit_writer = audit_writer or AuditWriter(self._config)
        self._agent = agent or MonitoringAgent(config=self._config)
        self._content_safety = content_safety or ContentSafetyValidator()
        self._deliver_fn = deliver_fn
        self._on_dead_letter_fn = on_dead_letter_fn or (lambda h: f"dl-{h.handoff_id}")

        # Counters for metrics
        self._signal_count = 0
        self._escalation_count = 0
        self._misinformation_count = 0
        self._validation_failure_count = 0
        self._dedup_discard_count = 0
        self._handoff_success_count = 0
        self._handoff_failure_count = 0

    # ------------------------------------------------------------------
    # Stage 1: Input Validation
    # ------------------------------------------------------------------

    def _validate(self, raw: dict, signal_id: str, tenant_id: str) -> SignalEnvelope | None:
        # RAG-OPTOUT [FR-RAG-NS-02]: BoM live-feed signals are authoritative; doctrine grounding lives on the downstream escalation call. ADR: docs/decisions/036-foundry-rag-grounding/02-rag-optout-bom-live.md  # noqa: E501
        """Stage 1: Validate incoming signal via Pydantic."""
        try:
            envelope = SignalEnvelope.model_validate(raw)
            return envelope
        except (ValidationError, Exception) as exc:
            self._validation_failure_count += 1
            scope_key = _build_scope_key(tenant_id, None, signal_id)
            record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.validation_failed,
                confidence=0.0,
                inputs={"raw_keys": list(raw.keys()) if isinstance(raw, dict) else []},
                output={"error": str(exc)[:500]},
                agent_version=self._config.agent_version,
                reasoning_summary=f"Pydantic validation failed: {str(exc)[:200]}",
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(record)
            logger.warning("Stage 1 validation failed for signal %s: %s", signal_id, exc)
            return None

    # ------------------------------------------------------------------
    # Stage 2: Deduplication
    # ------------------------------------------------------------------

    def _deduplicate(self, signal_id: str, envelope: SignalEnvelope, tenant_id: str) -> bool:
        """Stage 2: Check for duplicates.  Returns True if signal should continue."""
        if self._deduplicator.is_duplicate(signal_id):
            self._dedup_discard_count += 1
            scope_key = _build_scope_key(tenant_id, envelope.incidentId, signal_id)
            record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.discarded,
                confidence=envelope.confidenceScore,
                inputs={"signal_id": signal_id},
                output={"reason": "duplicate_signal_id"},
                agent_version=self._config.agent_version,
                reasoning_summary="Duplicate signal discarded (idempotency check)",
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(record)
            logger.debug("Stage 2 duplicate discarded: %s", signal_id)
            return False
        self._deduplicator.mark_seen(signal_id)
        return True

    # ------------------------------------------------------------------
    # Stage 3: Freshness Assessment
    # ------------------------------------------------------------------

    def _assess_freshness(self, signal_id: str, envelope: SignalEnvelope, tenant_id: str) -> None:
        """Stage 3: Update freshness for the signal's data source."""
        source_id = envelope.source.dataSourceId
        source_type = envelope.source.kind
        change = self._freshness_tracker.update(source_id, source_type, envelope.freshnessScore)

        if change is not None:
            scope_key = _build_scope_key(tenant_id, envelope.incidentId, signal_id)
            record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.degradation_detected,
                confidence=envelope.confidenceScore,
                freshness_score=envelope.freshnessScore,
                inputs={
                    "data_source_id": source_id,
                    "source_type": source_type,
                    "freshness_score": envelope.freshnessScore,
                },
                output={
                    "previous_status": change.previous_status.value,
                    "new_status": change.new_status.value,
                },
                agent_version=self._config.agent_version,
                reasoning_summary=(
                    f"Source {source_id} status: {change.previous_status.value} → {change.new_status.value}"
                ),
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(record)

    # ------------------------------------------------------------------
    # Stage 4: Misinformation Evaluation (conditional)
    # ------------------------------------------------------------------

    async def _evaluate_misinformation(
        self, signal_id: str, envelope: SignalEnvelope, tenant_id: str
    ) -> tuple[str | None, float]:
        """Stage 4: Conditional misinformation check for escalated signals.

        Returns (classification, suspicious_penalty).
        classification is None if stage was skipped.
        """
        if envelope.validationStatus != "escalated":
            return None, 0.0

        classification = await self._agent.evaluate_escalated_signal(envelope)
        scope_key = _build_scope_key(tenant_id, envelope.incidentId, signal_id)
        suspicious_penalty = 0.0

        if classification == "misinformation":
            self._misinformation_count += 1
            record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.blocked,
                confidence=envelope.confidenceScore,
                effective_confidence=envelope.confidenceScore * envelope.freshnessScore,
                freshness_score=envelope.freshnessScore,
                inputs={"category": envelope.category, "payload": envelope.payload},
                output={"blocked_reason": "misinformation"},
                agent_version=self._config.agent_version,
                reasoning_summary="Signal blocked — LLM classified as misinformation",
                llm_classification="misinformation",
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(record)
            return classification, 0.0

        if classification == "suspicious":
            suspicious_penalty = self._config.suspicious_confidence_penalty
            record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.summarised,
                confidence=envelope.confidenceScore,
                effective_confidence=envelope.confidenceScore * envelope.freshnessScore - suspicious_penalty,
                freshness_score=envelope.freshnessScore,
                inputs={"category": envelope.category},
                output={"penalty_applied": suspicious_penalty},
                agent_version=self._config.agent_version,
                reasoning_summary=f"Suspicious classification — penalty {suspicious_penalty} applied",
                llm_classification="suspicious",
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(record)
            return classification, suspicious_penalty

        if classification == "credible":
            record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.summarised,
                confidence=envelope.confidenceScore,
                effective_confidence=envelope.confidenceScore * envelope.freshnessScore,
                freshness_score=envelope.freshnessScore,
                inputs={"category": envelope.category},
                output={"classification": "credible"},
                agent_version=self._config.agent_version,
                reasoning_summary="LLM classified signal as credible",
                llm_classification="credible",
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(record)
            return classification, 0.0

        # llm_timeout, llm_unavailable, held_for_review → fail-safe-CLOSED
        llm_class = classification if classification in ("llm_timeout", "llm_unavailable") else "llm_timeout"
        record = MonitoringDecisionRecord(
            signal_id=signal_id,
            decision=DecisionType.held_for_review,
            confidence=envelope.confidenceScore,
            effective_confidence=envelope.confidenceScore * envelope.freshnessScore,
            freshness_score=envelope.freshnessScore,
            inputs={"category": envelope.category, "classification_result": classification},
            output={"action": "held_for_human_review"},
            agent_version=self._config.agent_version,
            reasoning_summary=f"Signal held for review — fail-safe-CLOSED ({classification})",
            llm_classification=llm_class,
            incident_scope_key=scope_key,
            tenant_id=tenant_id,
        )
        self._write_audit(record)
        return classification, 0.0

    # ------------------------------------------------------------------
    # Stage 5: Signal Summarisation
    # ------------------------------------------------------------------

    def _summarise(self, signal_id: str, envelope: SignalEnvelope, tenant_id: str) -> dict[str, object]:
        """Stage 5: Generate signal summary with content safety validation."""
        summary = self._agent.summarize_signal(envelope)
        content_safety_result = summary.get("content_safety_result", "not_checked")

        scope_key = _build_scope_key(tenant_id, envelope.incidentId, signal_id)
        record = MonitoringDecisionRecord(
            signal_id=signal_id,
            decision=DecisionType.summarised,
            confidence=envelope.confidenceScore,
            effective_confidence=envelope.confidenceScore * envelope.freshnessScore,
            freshness_score=envelope.freshnessScore,
            inputs={"category": envelope.category, "source_kind": envelope.source.kind},
            output=summary,
            agent_version=self._config.agent_version,
            reasoning_summary=f"Signal summarised (content_safety={content_safety_result})",
            content_safety_result=content_safety_result,
            incident_scope_key=scope_key,
            tenant_id=tenant_id,
        )
        self._write_audit(record)
        return summary

    # ------------------------------------------------------------------
    # Stage 6: Confidence-Based Triage
    # ------------------------------------------------------------------

    async def _triage(
        self,
        signal_id: str,
        envelope: SignalEnvelope,
        suspicious_penalty: float,
        tenant_id: str,
    ) -> AgentHandoffEvent | None:
        """Stage 6: Escalation decision based on effectiveConfidence."""
        handoff = self._agent.build_high_risk_handoff(
            envelope,
            suspicious_penalty=suspicious_penalty,
            tenant_id=tenant_id,
        )
        scope_key = _build_scope_key(tenant_id, envelope.incidentId, signal_id)
        effective_confidence = max(0.0, envelope.confidenceScore * envelope.freshnessScore - suspicious_penalty)

        if handoff is None:
            return None

        # Emit escalation audit record
        self._escalation_count += 1
        record = MonitoringDecisionRecord(
            signal_id=signal_id,
            decision=DecisionType.escalated,
            confidence=envelope.confidenceScore,
            effective_confidence=effective_confidence,
            freshness_score=envelope.freshnessScore,
            inputs={
                "category": envelope.category,
                "effective_confidence": effective_confidence,
                "threshold": self._config.escalation_confidence_threshold,
            },
            output={"handoff_id": handoff.handoff_id, "target_agent": "risk_assessment"},
            agent_version=self._config.agent_version,
            reasoning_summary=(
                f"Escalated: category={envelope.category}, "
                f"effectiveConfidence={effective_confidence:.3f} ≥ {self._config.escalation_confidence_threshold}"
            ),
            incident_scope_key=scope_key,
            tenant_id=tenant_id,
        )
        self._write_audit(record)

        # Deliver handoff
        if self._deliver_fn is not None:
            delivered = await deliver_handoff_with_retry(
                handoff=handoff,
                deliver=self._deliver_fn,
                on_dead_letter=self._on_dead_letter_fn,
            )
            # Emit handed_off audit record
            handed_off_record = MonitoringDecisionRecord(
                signal_id=signal_id,
                decision=DecisionType.handed_off,
                confidence=envelope.confidenceScore,
                effective_confidence=effective_confidence,
                freshness_score=envelope.freshnessScore,
                inputs={"handoff_id": handoff.handoff_id},
                output={"status": delivered.status, "retry_count": delivered.retry_count},
                agent_version=self._config.agent_version,
                reasoning_summary=f"Handoff {delivered.status} (retries={delivered.retry_count})",
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
            self._write_audit(handed_off_record)

            if delivered.status == "delivered":
                self._handoff_success_count += 1
            else:
                self._handoff_failure_count += 1

        return handoff

    # ------------------------------------------------------------------
    # Top-level orchestrator
    # ------------------------------------------------------------------

    async def process_signal(
        self,
        raw: dict,
        signal_id: str,
        tenant_id: str = "live",
    ) -> MonitoringDecisionRecord | None:
        """Process a signal through all 6 stages.

        Returns the final audit record (or None if no terminal decision was made).
        """
        start = time.perf_counter()
        self._signal_count += 1

        # Stage 1: Input Validation
        envelope = self._validate(raw, signal_id, tenant_id)
        if envelope is None:
            return None

        # Stage 2: Deduplication
        if not self._deduplicate(signal_id, envelope, tenant_id):
            return None

        # Stage 3: Freshness Assessment
        self._assess_freshness(signal_id, envelope, tenant_id)

        # Stage 4: Misinformation Evaluation (conditional)
        classification, suspicious_penalty = await self._evaluate_misinformation(signal_id, envelope, tenant_id)
        # If blocked or held, stop processing
        if classification in ("misinformation", "llm_timeout", "llm_unavailable", "held_for_review"):
            return None

        # Stage 5: Signal Summarisation
        self._summarise(signal_id, envelope, tenant_id)

        # Stage 6: Confidence-Based Triage
        handoff = await self._triage(signal_id, envelope, suspicious_penalty, tenant_id)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "Pipeline completed for signal %s in %.2fms (escalated=%s)",
            signal_id,
            elapsed_ms,
            handoff is not None,
        )

        return None  # All audit records already written per-stage

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_audit(self, record: MonitoringDecisionRecord) -> None:
        """Write an audit record through the audit writer."""
        self._audit_writer.write(record)

    # ------------------------------------------------------------------
    # Metrics accessors
    # ------------------------------------------------------------------

    @property
    def signal_count(self) -> int:
        return self._signal_count

    @property
    def escalation_count(self) -> int:
        return self._escalation_count

    @property
    def misinformation_count(self) -> int:
        return self._misinformation_count

    @property
    def validation_failure_count(self) -> int:
        return self._validation_failure_count

    @property
    def dedup_discard_count(self) -> int:
        return self._dedup_discard_count

    @property
    def handoff_success_rate(self) -> float:
        total = self._handoff_success_count + self._handoff_failure_count
        if total == 0:
            return 1.0
        return self._handoff_success_count / total
