"""Communication Processing Pipeline — 11-stage orchestrator.

Stages per contracts/communication-pipeline.md:
1. Handoff Intake & Validation
2. Data Retrieval
3. Audience Segmentation
4. Template Loading & Interpolation
5. Multilingual Alert Drafting (LLM)
6. Back-Translation Quality Validation
7. Content Safety Validation
8. Alert Versioning & Persistence
9. Approval Notification
10. Multi-Channel Delivery
11. Audit Finalisation

Each stage produces audit records and emits metrics.
"""

from __future__ import annotations

import logging
import time
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Protocol

from common.async_bridge import run_async
from common.content_safety import ContentSafetyValidator
from common.handoffs import AgentHandoffEvent
from communication.approval import ApprovalNotificationError, ApprovalWorkflow
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.dedup import HandoffDeduplicator
from communication.delivery import MultiChannelDeliveryService
from communication.models import (
    AlertStatus,
    AudienceSegment,
    ChangeType,
    ChannelType,
    CommunicationDecisionRecord,
    CommunicationDecisionType,
    ContentBlock,
    ContentSafetyDetail,
    ContentSafetyResult,
    DeliveryRecord,
    DeliveryStatus,
    GenerationMethod,
    PublicAlert,
)
from communication.repository import CommunicationAlertRepository
from communication.segmentation import AudienceSegmenter
from communication.telemetry import CustomEventEmitter, metrics, pipeline_span
from communication.templates import TemplateLoader
from communication.translator import MultilingualTranslator
from communication.versioning import VersionCounter
from pydantic import BaseModel, ConfigDict, Field

from packages.domain.src.domain.tenant_mode import is_live_tenant

logger = logging.getLogger(__name__)


class CommunicationReadContainer(Protocol):
    def read_item(self, *, item: str, partition_key: str) -> dict[str, object]: ...


class CommunicationWriteContainer(Protocol):
    def create_item(self, *, body: dict[str, object]) -> object: ...


def _required_string_list(record: dict[str, object], field: str) -> list[str]:
    raw_values = record.get(field, [])
    if not isinstance(raw_values, list):
        raise HandoffReferenceError(f"Referenced record field {field!r} must be a list")
    values: list[str] = []
    for value in raw_values:
        if not isinstance(value, str):
            raise HandoffReferenceError(f"Referenced record field {field!r} must contain strings")
        values.append(value)
    return values


class CommunicationHandoffPayload(BaseModel):
    """Validated boundary shared with the Risk Assessment producer."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    recommendation_id: str = Field(alias="recommendationId", min_length=1)
    assessment_id: str = Field(alias="assessmentId", min_length=1)
    summary: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class HandoffReferenceError(ValueError):
    """Permanent rejection caused by missing or foreign provenance."""


class TransientHandoffDependencyError(RuntimeError):
    """Retryable handoff failure caused by an unavailable dependency."""


class CommunicationProcessingPipeline:
    """Orchestrates the 11-stage communication processing pipeline."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        deduplicator: HandoffDeduplicator | None = None,
        template_loader: TemplateLoader | None = None,
        translator: MultilingualTranslator | None = None,
        segmenter: AudienceSegmenter | None = None,
        version_counter: VersionCounter | None = None,
        audit_writer: AuditWriter | None = None,
        delivery_service: MultiChannelDeliveryService | None = None,
        content_safety: ContentSafetyValidator | None = None,
        alert_store: CommunicationReadContainer | None = None,
        assessment_store: CommunicationReadContainer | None = None,
        recommendation_store: CommunicationReadContainer | None = None,
        incident_store: CommunicationReadContainer | None = None,
        delivery_store: CommunicationWriteContainer | None = None,
        alert_repository: CommunicationAlertRepository | None = None,
        approval_workflow: ApprovalWorkflow | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._deduplicator = deduplicator or HandoffDeduplicator(
            window_minutes=self._config.handoff_dedup_window_minutes
        )
        self._template_loader = template_loader
        self._translator = translator or MultilingualTranslator(
            config=self._config, template_loader=self._template_loader
        )
        self._segmenter = segmenter or AudienceSegmenter(config=self._config)
        self._version_counter = version_counter or VersionCounter(config=self._config)
        self._audit_writer = audit_writer or AuditWriter(config=self._config)
        self._delivery_service = delivery_service or MultiChannelDeliveryService(config=self._config)
        self._content_safety = content_safety or ContentSafetyValidator()
        self._alert_store = alert_store
        self._assessment_store = assessment_store
        self._recommendation_store = recommendation_store
        self._incident_store = incident_store
        self._delivery_store = delivery_store
        self._alert_repository = alert_repository
        self._approval_workflow = approval_workflow
        self._processed_count = 0

    def process_handoff(self, event: AgentHandoffEvent) -> PublicAlert | None:
        """Process a single handoff through the 11-stage pipeline.

        Returns PublicAlert on success, None on rejection/discard.
        """
        pipeline_start = time.perf_counter()
        change_key: str | None = None

        with pipeline_span(
            "communication.pipeline.process",
            {
                "handoff_id": event.handoff_id,
                "incident_id": event.incident_id,
            },
        ):
            try:
                # Stage 1: Handoff Intake & Validation
                if not self._stage_1_intake(event):
                    return None

                # Stage 2: Data Retrieval
                assessment_data, recommendation_data = self._stage_2_retrieve(event)
                change_key = self._semantic_change_key(event, assessment_data)
                if not self._deduplicator.reserve_incident_change(
                    event.incident_id,
                    change_key,
                    tenant_id=event.tenant_id,
                ):
                    self._deduplicator.release(
                        tenant_id=event.tenant_id,
                        handoff_id=event.handoff_id,
                        incident_id=event.incident_id,
                        hazard_type=change_key,
                    )
                    self._write_audit(
                        CommunicationDecisionType.duplicate_discarded,
                        handoff_id=event.handoff_id,
                        output_summary=f"Completed or in-flight assessment/change: {change_key}",
                        tenant_id=event.tenant_id,
                    )
                    return None

                # Stage 3: Audience Segmentation
                segments = self._stage_3_segment(event, assessment_data)

                # Stage 4: Template Loading
                template_values = self._stage_4_templates(event, assessment_data)

                draft_deadline = time.monotonic() + self._config.draft_deadline_seconds

                # Stage 5: Multilingual Alert Drafting
                content_blocks = self._stage_5_draft(
                    event,
                    template_values,
                    assessment_data,
                    recommendation_data,
                    draft_deadline,
                )

                # Stage 6: Back-Translation Quality Validation
                content_blocks, bt_penalty = self._stage_6_back_translate(
                    content_blocks,
                    draft_deadline,
                    event.tenant_id,
                )

                # Stage 7: Content Safety Validation
                content_blocks, safety_result, safety_details = self._stage_7_content_safety(
                    content_blocks,
                    template_values,
                    assessment_data,
                    event.tenant_id,
                    event.handoff_id,
                    str(event.payload.get("alert_type") or "evacuation"),
                    str(event.payload.get("warningTier") or assessment_data.get("warning_tier") or "Emergency Warning"),
                )

                # Stage 8: Alert Versioning & Persistence
                alert = self._stage_8_version_persist(
                    event,
                    content_blocks,
                    segments,
                    safety_result,
                    safety_details,
                    bt_penalty,
                    recommendation_data,
                    assessment_data,
                )

                # Stage 9: Approval Notification (stub — full in US2)
                self._stage_9_approval(alert)

                # Stage 10: Delivery (stub — full in US3, triggered by approval)
                # Delivery happens after commander approval, not here

                # Stage 11: Audit Finalisation
                pipeline_elapsed = (time.perf_counter() - pipeline_start) * 1000
                self._stage_11_audit_finalise(event, alert, pipeline_elapsed)

                self._processed_count += 1
                metrics.pipeline_total_latency.record(pipeline_elapsed, {"tenant_id": event.tenant_id})
                metrics.active_alerts_count.add(1, {"tenant_id": event.tenant_id})
                self._deduplicator.complete(
                    tenant_id=event.tenant_id,
                    handoff_id=event.handoff_id,
                    incident_id=event.incident_id,
                    change_key=change_key,
                )

                return alert

            except HandoffReferenceError as exc:
                self._deduplicator.release(
                    tenant_id=event.tenant_id,
                    handoff_id=event.handoff_id,
                    incident_id=event.incident_id,
                    hazard_type=change_key or "",
                )
                logger.warning("Rejected handoff %s: %s", event.handoff_id, exc)
                self._write_audit(
                    CommunicationDecisionType.handoff_rejected,
                    handoff_id=event.handoff_id,
                    output_summary=str(exc),
                    tenant_id=event.tenant_id,
                )
                return None
            except TransientHandoffDependencyError as exc:
                self._deduplicator.release(
                    tenant_id=event.tenant_id,
                    handoff_id=event.handoff_id,
                    incident_id=event.incident_id,
                    hazard_type=change_key or "",
                )
                self._write_audit(
                    CommunicationDecisionType.degradation_detected,
                    handoff_id=event.handoff_id,
                    output_summary=str(exc),
                    tenant_id=event.tenant_id,
                )
                raise
            except Exception as exc:
                self._deduplicator.release(
                    tenant_id=event.tenant_id,
                    handoff_id=event.handoff_id,
                    incident_id=event.incident_id,
                    hazard_type=change_key or "",
                )
                logger.error(
                    "Pipeline failed for handoff %s: %s",
                    event.handoff_id,
                    exc,
                    exc_info=True,
                )
                self._write_audit(
                    CommunicationDecisionType.handoff_rejected,
                    handoff_id=event.handoff_id,
                    output_summary=f"Pipeline error: {exc}",
                    tenant_id=event.tenant_id,
                )
                return None

    def _stage_1_intake(self, event: AgentHandoffEvent) -> bool:
        """Stage 1: Handoff Intake & Validation."""
        with pipeline_span("communication.stage.intake"):
            # Validate target_agent
            if event.target_agent != "communication":
                self._write_audit(
                    CommunicationDecisionType.handoff_rejected,
                    handoff_id=event.handoff_id,
                    output_summary=f"Wrong target agent: {event.target_agent}",
                    tenant_id=event.tenant_id,
                )
                CustomEventEmitter.handoff_rejected(
                    event.handoff_id,
                    "wrong_target_agent",
                    tenant_id=event.tenant_id,
                )
                return False

            if event.source_agent != "risk_assessment":
                self._write_audit(
                    CommunicationDecisionType.handoff_rejected,
                    handoff_id=event.handoff_id,
                    output_summary=f"Untrusted source agent: {event.source_agent}",
                    tenant_id=event.tenant_id,
                )
                return False

            if not event.incident_id.strip() or not event.scope_key.strip() or not event.tenant_id.strip():
                self._write_audit(
                    CommunicationDecisionType.handoff_rejected,
                    handoff_id=event.handoff_id,
                    output_summary="Handoff identity and scope values must be non-empty",
                    tenant_id=event.tenant_id or "unknown",
                )
                return False

            try:
                CommunicationHandoffPayload.model_validate(event.payload)
            except Exception as exc:
                self._write_audit(
                    CommunicationDecisionType.handoff_rejected,
                    handoff_id=event.handoff_id,
                    output_summary=f"Invalid communication handoff payload: {exc}",
                    tenant_id=event.tenant_id,
                )
                return False

            if not self._deduplicator.reserve_handoff(event.handoff_id, tenant_id=event.tenant_id):
                self._write_audit(
                    CommunicationDecisionType.duplicate_discarded,
                    handoff_id=event.handoff_id,
                    output_summary="Duplicate handoff ID",
                    tenant_id=event.tenant_id,
                )
                CustomEventEmitter.duplicate_discarded(event.handoff_id, tenant_id=event.tenant_id)
                return False

            # Record handoff received
            self._write_audit(
                CommunicationDecisionType.handoff_received,
                handoff_id=event.handoff_id,
                input_snapshot={
                    "incident_id": event.incident_id,
                    "source_agent": event.source_agent,
                    "confidence": event.confidence,
                },
                tenant_id=event.tenant_id,
            )
            CustomEventEmitter.handoff_received(
                event.handoff_id,
                event.incident_id,
                tenant_id=event.tenant_id,
            )
            return True

    def _stage_2_retrieve(self, event: AgentHandoffEvent) -> tuple[dict[str, object], dict[str, object]]:
        """Stage 2: Data Retrieval — get recommendation and assessment."""
        with pipeline_span("communication.stage.retrieve"):
            payload = CommunicationHandoffPayload.model_validate(event.payload)
            incident_data = self._read_required(
                self._incident_store,
                record_id=event.incident_id,
                partition_key=event.scope_key,
                record_type="incident",
            )
            recommendation_data = self._read_required(
                self._recommendation_store,
                record_id=payload.recommendation_id,
                partition_key=event.scope_key,
                record_type="recommendation",
            )
            assessment_data = self._read_required(
                self._assessment_store,
                record_id=payload.assessment_id,
                partition_key=event.scope_key,
                record_type="assessment",
            )

            for record_type, record in (
                ("incident", incident_data),
                ("recommendation", recommendation_data),
                ("assessment", assessment_data),
            ):
                self._validate_record_scope(record_type, record, event)

            linked_assessment = recommendation_data.get("assessment_id") or recommendation_data.get("assessmentId")
            if linked_assessment and str(linked_assessment) != payload.assessment_id:
                raise HandoffReferenceError("Recommendation references a different assessment")
            recommendation_data["_commander_chain"] = self._commander_chain(incident_data)
            self._write_audit(
                CommunicationDecisionType.data_retrieved,
                handoff_id=event.handoff_id,
                output_summary=(
                    f"Resolved incident={event.incident_id}, recommendation={payload.recommendation_id}, "
                    f"assessment={payload.assessment_id}"
                ),
                tenant_id=event.tenant_id,
            )
            return deepcopy(assessment_data), deepcopy(recommendation_data)

    @staticmethod
    def _semantic_change_key(event: AgentHandoffEvent, assessment_data: dict[str, object]) -> str:
        assessment_id = str(assessment_data.get("assessment_id") or assessment_data.get("id") or "")
        hazard_type = str(assessment_data.get("hazard_type") or "general")
        change_type = str(event.payload.get("change_type") or "initial")
        return f"{hazard_type}:{assessment_id}:{change_type}"

    @staticmethod
    def _commander_chain(incident_data: dict[str, object]) -> list[str]:
        raw_chain = incident_data.get("commander_chain") or incident_data.get("commanderChain") or []
        if not isinstance(raw_chain, list):
            raise HandoffReferenceError("Incident commander_chain must be a list")
        chain: list[str] = []
        for entry in raw_chain:
            if isinstance(entry, str) and entry.strip():
                chain.append(entry.strip())
            elif isinstance(entry, dict):
                identifier = entry.get("oid") or entry.get("user_id") or entry.get("userId")
                if identifier:
                    chain.append(str(identifier))
        return list(dict.fromkeys(chain))

    @staticmethod
    def _read_required(
        store: CommunicationReadContainer | None,
        *,
        record_id: str,
        partition_key: str,
        record_type: str,
    ) -> dict[str, object]:
        if store is None:
            raise TransientHandoffDependencyError(f"{record_type} store is not configured")
        try:
            record = store.read_item(item=record_id, partition_key=partition_key)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
            if status_code == 404 or "NotFound" in type(exc).__name__:
                raise HandoffReferenceError(f"Referenced {record_type} {record_id} was not found") from exc
            raise TransientHandoffDependencyError(f"{record_type} store is unavailable") from exc
        if not isinstance(record, dict):
            raise HandoffReferenceError(f"Referenced {record_type} {record_id} is invalid")
        return record

    @staticmethod
    def _validate_record_scope(record_type: str, record: dict[str, object], event: AgentHandoffEvent) -> None:
        record_incident = record.get("incident_id") or record.get("incidentId") or record.get("id")
        if str(record_incident or "") != event.incident_id:
            raise HandoffReferenceError(f"Referenced {record_type} belongs to a different incident")
        record_tenant = record.get("tenant_id") or record.get("tenantId")
        if record_tenant is not None and str(record_tenant) != event.tenant_id:
            raise HandoffReferenceError(f"Referenced {record_type} belongs to a different tenant")

    def _stage_3_segment(self, event: AgentHandoffEvent, assessment_data: dict[str, object]) -> list[AudienceSegment]:
        """Stage 3: Audience Segmentation."""
        with pipeline_span("communication.stage.segment"):
            demographics = dict(event.payload.get("demographics", {}) or {})
            segments = self._segmenter.segment_audience(assessment_data, demographics)
            metrics.audience_segment_count.record(len(segments), {"tenant_id": event.tenant_id})

            self._write_audit(
                CommunicationDecisionType.audience_segmented,
                handoff_id=event.handoff_id,
                output_summary=f"{len(segments)} segments created",
                tenant_id=event.tenant_id,
            )
            return segments

    def _stage_4_templates(self, event: AgentHandoffEvent, assessment_data: dict[str, object]) -> dict[str, str]:
        """Stage 4: Template Loading & Interpolation — build template values."""
        with pipeline_span("communication.stage.templates"):
            return {
                "location": str(assessment_data.get("location", "affected area")),
                "time": str(assessment_data.get("time", "the coming hours")),
                "severity": str(assessment_data.get("severity", "moderate")),
                "wind_speed": str(assessment_data.get("wind_speed", "")),
                "severity_detail": str(assessment_data.get("severity_detail", "")),
                "help_url": str(assessment_data.get("help_url", "www.emergency.gov.au")),
            }

    def _stage_5_draft(
        self,
        event: AgentHandoffEvent,
        template_values: dict[str, str],
        assessment_data: dict[str, object],
        recommendation_data: dict[str, object],
        draft_deadline: float,
    ) -> dict[str, ContentBlock]:
        """Stage 5: Multilingual Alert Drafting."""
        draft_start = time.perf_counter()

        with pipeline_span("communication.stage.draft"):
            hazard_type = str(assessment_data.get("hazard_type", "general"))
            severity = str(assessment_data.get("severity", "moderate"))
            alert_type = str(event.payload.get("alert_type", "evacuation"))

            content_blocks = self._translator.translate_all(
                hazard_type=hazard_type,
                severity=severity,
                alert_type=alert_type,
                template_values=template_values,
                change_type=str(event.payload.get("change_type", "initial")),
                incident_id=event.incident_id,
                deadline_monotonic=draft_deadline,
                source_context={
                    "recommendation_summary": str(recommendation_data.get("summary", "")),
                    "recommendation_explanation": str(recommendation_data.get("explanation", "")),
                },
            )

            draft_elapsed = (time.perf_counter() - draft_start) * 1000
            metrics.alert_draft_latency.record(draft_elapsed, {"tenant_id": event.tenant_id})
            CustomEventEmitter.alert_drafted(
                alert_id="pending",
                languages=len(content_blocks),
                tenant_id=event.tenant_id,
                handoff_id=event.handoff_id,
            )

            self._write_audit(
                CommunicationDecisionType.alert_drafted,
                handoff_id=event.handoff_id,
                output_summary=f"Drafted {len(content_blocks)} languages in {draft_elapsed:.0f}ms",
                processing_duration_ms=int(draft_elapsed),
                tenant_id=event.tenant_id,
            )

            return content_blocks

    def _stage_6_back_translate(
        self,
        content_blocks: dict[str, ContentBlock],
        draft_deadline: float,
        tenant_id: str,
    ) -> tuple[dict[str, ContentBlock], float]:
        """Stage 6: Back-Translation Quality Validation."""
        with pipeline_span("communication.stage.back_translate"):
            en_au = content_blocks.get("en-AU")
            bt_penalty = 1.0

            if en_au is None:
                return content_blocks, bt_penalty

            for lang, block in content_blocks.items():
                if lang == "en-AU":
                    continue
                if block.generation_method != GenerationMethod.llm:
                    continue

                try:
                    score = self._translator.back_translate_and_score(
                        block,
                        en_au,
                        deadline_monotonic=draft_deadline,
                    )
                    block.back_translation_score = score
                    block.back_translation_measured = score is not None

                    if score is None:
                        CustomEventEmitter.degradation_detected(
                            service="embedding",
                            fallback="skip_back_translation",
                            tenant_id=tenant_id,
                        )
                    elif score < self._config.back_translation_threshold:
                        block.back_translation_flagged = True
                        bt_penalty = self._config.back_translation_penalty_factor
                        metrics.back_translation_quality.record(score, {"language": lang, "tenant_id": tenant_id})
                        CustomEventEmitter.back_translation_flagged(
                            alert_id="pending",
                            language=lang,
                            score=score,
                            tenant_id=tenant_id,
                        )
                        self._write_audit(
                            CommunicationDecisionType.back_translation_below_threshold,
                            output_summary=f"{lang} score={score:.3f} < {self._config.back_translation_threshold}",
                            tenant_id=tenant_id,
                        )
                    else:
                        metrics.back_translation_quality.record(score, {"language": lang, "tenant_id": tenant_id})
                except Exception:
                    # Embedding outage → skip per CHK051
                    logger.warning("Back-translation check failed for %s, skipping", lang)
                    CustomEventEmitter.degradation_detected(
                        service="embedding",
                        fallback="skip_back_translation",
                        tenant_id=tenant_id,
                    )

            return content_blocks, bt_penalty

    def _stage_7_content_safety(
        self,
        content_blocks: dict[str, ContentBlock],
        template_values: dict[str, str],
        assessment_data: dict[str, object],
        tenant_id: str,
        handoff_id: str,
        alert_type: str,
        warning_tier: str,
    ) -> tuple[dict[str, ContentBlock], ContentSafetyResult, dict[str, ContentSafetyDetail]]:
        """Stage 7: Content Safety Validation."""
        safety_start = time.perf_counter()

        with pipeline_span("communication.stage.content_safety"):
            overall_result = ContentSafetyResult.passed
            safety_details: dict[str, ContentSafetyDetail] = {}

            for lang, block in content_blocks.items():
                # Skip validation for template-based content per FR-014
                if block.generation_method in (
                    GenerationMethod.template,
                    GenerationMethod.template_fallback,
                    GenerationMethod.safety_fallback,
                ):
                    original_failed = (
                        block.generation_method == GenerationMethod.safety_fallback
                        or block.original_content_safety_result == "failed_with_fallback"
                    )
                    safety_details[lang] = ContentSafetyDetail(
                        language_code=lang,
                        passed=not original_failed,
                        failure_reason=block.original_content_safety_failure_reason,
                        original_text_length=len(block.body),
                        fallback_used=block.generation_method == GenerationMethod.safety_fallback,
                    )
                    if original_failed:
                        overall_result = ContentSafetyResult.failed_with_fallback
                    elif block.generation_method in (GenerationMethod.template, GenerationMethod.template_fallback):
                        block.content_safety_result = "not_checked"
                    self._write_audit(
                        CommunicationDecisionType.content_safety_evaluated,
                        handoff_id=handoff_id,
                        content_safety_results={lang: block.content_safety_result},
                        language=lang,
                        tenant_id=tenant_id,
                    )
                    continue

                # Validate LLM-generated content
                full_text = f"{block.title} {block.body} {block.action_items}"
                checks = {
                    "moderation_language": self._content_safety.validate(
                        text=full_text,
                        expected_language=lang,
                        max_length=self._config.content_max_length,
                    ),
                    "factual": self._content_safety.validate_factual(
                        full_text,
                        {
                            "hazard_type": assessment_data.get("hazard_type", ""),
                            "severity_level": assessment_data.get("severity_level")
                            or assessment_data.get("severity", ""),
                            "location_name": assessment_data.get("location_name")
                            or assessment_data.get("location", ""),
                        },
                    ),
                    "tone": self._content_safety.validate_tone(full_text, warning_tier),
                    "cultural": self._content_safety.validate_cultural(full_text),
                }
                failed_checks = [check for check in checks.values() if not check.passed]
                result = failed_checks[0] if failed_checks else checks["moderation_language"]
                block.safety_checks = {name: check.result for name, check in checks.items()}
                block.original_content_safety_result = result.result
                block.original_content_safety_failure_reason = result.reason

                safety_details[lang] = ContentSafetyDetail(
                    language_code=lang,
                    passed=result.passed,
                    failure_reason=result.reason if not result.passed else None,
                    original_text_length=len(full_text),
                    fallback_used=not result.passed,
                )

                if not result.passed:
                    # Fallback to template per FR-011
                    hazard_type = str(assessment_data.get("hazard_type", "general"))
                    severity = str(assessment_data.get("severity", "moderate"))
                    if self._template_loader:
                        title, body, action, unavailable = self._template_loader.get_template_text(
                            hazard_type, severity, alert_type, lang, template_values
                        )
                    else:
                        title = f"EMERGENCY ALERT — {template_values.get('location', '[unknown]')}"
                        body = "An emergency situation exists. Follow emergency services directions."
                        action = "Call 000 for emergencies."

                    block.title = title[:200]
                    block.body = body[:1200]
                    block.action_items = action[:500]
                    block.generation_method = GenerationMethod.safety_fallback
                    block.content_safety_result = "failed_with_fallback"
                    block.content_safety_failure_reason = result.reason

                    overall_result = ContentSafetyResult.failed_with_fallback
                    metrics.content_safety_failure_rate.add(1, {"language": lang, "tenant_id": tenant_id})
                    CustomEventEmitter.content_safety_failed(
                        alert_id="pending",
                        language=lang,
                        reason=result.reason or "",
                        tenant_id=tenant_id,
                    )
                else:
                    block.content_safety_result = "passed"

                self._write_audit(
                    CommunicationDecisionType.content_safety_evaluated,
                    handoff_id=handoff_id,
                    content_safety_results={lang: result.result},
                    language=lang,
                    tenant_id=tenant_id,
                )

            safety_elapsed = (time.perf_counter() - safety_start) * 1000
            metrics.content_safety_check_latency.record(safety_elapsed, {"tenant_id": tenant_id})

            return content_blocks, overall_result, safety_details

    def _stage_8_version_persist(
        self,
        event: AgentHandoffEvent,
        content_blocks: dict[str, ContentBlock],
        segments: list[AudienceSegment],
        safety_result: ContentSafetyResult,
        safety_details: dict[str, ContentSafetyDetail],
        bt_penalty: float,
        recommendation_data: dict[str, object],
        assessment_data: dict[str, object],
    ) -> PublicAlert:
        """Stage 8: Alert Versioning & Persistence."""
        with pipeline_span("communication.stage.version_persist"):
            # Assign version
            version = run_async(
                self._version_counter.assign_version(
                    event.incident_id,
                    event.tenant_id,
                    reservation_key=event.handoff_id,
                )
            )
            alert_id = self._version_counter.format_alert_id(event.incident_id, version)

            # Compute confidence with compound penalties per CHK031
            assessment_timestamp, freshness = self._assessment_freshness(assessment_data)
            freshness_penalty = self._config.freshness_penalty_factor if freshness == "stale" else 1.0
            fallback_penalty = 1.0

            # Check if any language used template fallback
            for block in content_blocks.values():
                if block.generation_method in (GenerationMethod.template_fallback, GenerationMethod.safety_fallback):
                    fallback_penalty = self._config.fallback_reduction_factor
                    break

            confidence = MultilingualTranslator.compute_compound_confidence(
                base=event.confidence,
                freshness_penalty=freshness_penalty,
                back_translation_penalty=bt_penalty,
                fallback_penalty=fallback_penalty,
            )

            # Determine worst-case generation method
            gen_methods = [b.generation_method for b in content_blocks.values()]
            if GenerationMethod.safety_fallback in gen_methods:
                overall_gen = GenerationMethod.safety_fallback
            elif GenerationMethod.template_fallback in gen_methods:
                overall_gen = GenerationMethod.template_fallback
            elif GenerationMethod.template in gen_methods:
                overall_gen = GenerationMethod.template
            else:
                overall_gen = GenerationMethod.llm

            # Determine change type
            change_type_str = str(event.payload.get("change_type", "initial"))
            try:
                change_type = ChangeType(change_type_str)
            except ValueError:
                raise HandoffReferenceError(f"Unsupported change_type: {change_type_str}") from None
            if version > 1 and change_type == ChangeType.initial:
                change_type = ChangeType.update

            referenced_alert_id = (
                str(event.payload.get("referenced_alert_id") or "").strip()
                if change_type in (ChangeType.correction, ChangeType.all_clear)
                else None
            )
            if version > 1 and referenced_alert_id is None:
                referenced_alert_id = self._version_counter.format_alert_id(event.incident_id, version - 1)
            change_summary = (
                str(event.payload.get("change_summary") or "").strip() if change_type != ChangeType.initial else None
            )
            if change_type != ChangeType.initial and not change_summary:
                raise HandoffReferenceError("change_summary is required for update, correction, and all-clear alerts")

            if change_type == ChangeType.all_clear:
                if not referenced_alert_id or self._alert_repository is None:
                    raise HandoffReferenceError("All-clear requires a persisted referenced alert")
                try:
                    referenced_alert = self._alert_repository.require(event.tenant_id, referenced_alert_id)
                    segments = self._alert_repository.audience_segments(event.tenant_id, referenced_alert_id)
                except Exception as exc:
                    raise HandoffReferenceError("Referenced all-clear alert was not found") from exc
                if referenced_alert.incident_id != event.incident_id:
                    raise HandoffReferenceError("All-clear reference belongs to a different incident")
                confirmed_subzones = {
                    str(value) for value in event.payload.get("confirmedActiveSubzones", []) if str(value)
                }
                unconfirmed = set(referenced_alert.active_subzone_ids) - confirmed_subzones
                if unconfirmed:
                    raise HandoffReferenceError(
                        f"All-clear requires confirmation for active sub-zones: {', '.join(sorted(unconfirmed))}"
                    )

            # Build alert
            recommendation_id = str(recommendation_data.get("recommendation_id", event.handoff_id))
            assessment_id = str(event.payload.get("assessmentId", event.handoff_id))

            channels = [ChannelType(ch) for ch in self._config.delivery_channels if ch in ChannelType.__members__]

            alert = PublicAlert(
                alert_id=alert_id,
                incident_id=event.incident_id,
                version=version,
                status=AlertStatus.pending_review,
                change_type=change_type,
                change_summary=change_summary,
                referenced_alert_id=referenced_alert_id,
                content_blocks=content_blocks,
                audience_segments=[s.segment_id for s in segments],
                languages=list(content_blocks.keys()),
                channel_set=channels,
                generation_method=overall_gen,
                content_safety_result=safety_result,
                content_safety_details=safety_details,
                confidence=confidence,
                recommendation_id=recommendation_id,
                assessment_id=assessment_id,
                assessment_timestamp=assessment_timestamp,
                assessment_freshness=freshness,
                commander_chain=_required_string_list(recommendation_data, "_commander_chain"),
                warning_tier=str(event.payload.get("warningTier") or "") or None,
                active_subzone_ids=_required_string_list(assessment_data, "active_subzone_ids"),
                tenant_id=event.tenant_id,
                expires_at=datetime.now(UTC) + timedelta(hours=self._config.alert_expiry_hours),
            )

            if self._alert_repository is None:
                raise TransientHandoffDependencyError("Alert aggregate repository is not configured")
            try:
                alert = self._alert_repository.create(alert, segments)
            except Exception as exc:
                raise TransientHandoffDependencyError(f"Failed to persist alert aggregate {alert_id}") from exc

            # Record audit
            penalties = []
            if freshness_penalty < 1.0:
                penalties.append(f"freshness:{freshness_penalty}")
            if bt_penalty < 1.0:
                penalties.append(f"back_translation:{bt_penalty}")
            if fallback_penalty < 1.0:
                penalties.append(f"fallback:{fallback_penalty}")

            self._write_audit(
                CommunicationDecisionType.alert_versioned,
                handoff_id=event.handoff_id,
                alert_id=alert_id,
                confidence=confidence,
                confidence_penalties_applied=penalties or None,
                output_summary=f"v{version} {change_type.value} confidence={confidence:.3f}",
                tenant_id=event.tenant_id,
            )

            CustomEventEmitter.alert_version_created(
                alert_id=alert_id,
                version=version,
                change_type=change_type.value,
                tenant_id=event.tenant_id,
                incident_id=event.incident_id,
            )
            metrics.pending_approvals.add(1, {"tenant_id": event.tenant_id})

            return alert

    def _assessment_freshness(self, assessment_data: dict[str, object]) -> tuple[datetime | None, str]:
        raw_timestamp = (
            assessment_data.get("assessed_at")
            or assessment_data.get("assessment_timestamp")
            or assessment_data.get("created_at")
            or assessment_data.get("updated_at")
        )
        if raw_timestamp is None:
            return None, "unavailable"
        try:
            timestamp = (
                raw_timestamp
                if isinstance(raw_timestamp, datetime)
                else datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
            )
        except (TypeError, ValueError):
            return None, "unavailable"
        if timestamp.tzinfo is None:
            return None, "unavailable"
        age = datetime.now(UTC) - timestamp.astimezone(UTC)
        if age.total_seconds() < -300:
            return timestamp, "future"
        threshold = timedelta(minutes=self._config.assessment_staleness_threshold_minutes)
        return timestamp, "stale" if age > threshold else "fresh"

    def _stage_9_approval(self, alert: PublicAlert) -> None:
        """Persist and publish the complete version-bound approval request."""
        with pipeline_span("communication.stage.approval"):
            if self._approval_workflow is None:
                raise TransientHandoffDependencyError("Approval workflow is not configured")
            try:
                run_async(self._approval_workflow.request_approval(alert))
            except ApprovalNotificationError as exc:
                self._write_audit(
                    CommunicationDecisionType.degradation_detected,
                    alert_id=alert.alert_id,
                    output_summary=str(exc),
                    tenant_id=alert.tenant_id,
                )
                return
            self._write_audit(
                CommunicationDecisionType.approval_requested,
                alert_id=alert.alert_id,
                output_summary=f"Approval requested for {alert.alert_id}",
                tenant_id=alert.tenant_id,
            )

    def deliver_approved_alert(
        self,
        alert: PublicAlert,
        segments: list[AudienceSegment],
    ) -> list[DeliveryRecord]:
        """Stage 10: Multi-Channel Delivery (called after approval)."""
        with pipeline_span("communication.stage.delivery"):
            records = run_async(self._delivery_service.deliver_alert(alert, segments))

            statuses = [record.delivery_status for record in records if not record.is_deduplicated]
            if not is_live_tenant(alert.tenant_id) or alert.mode != "live":
                alert.status = AlertStatus.approved
            elif statuses and all(status == DeliveryStatus.delivered for status in statuses):
                alert.status = AlertStatus.delivered
                alert.published_at = alert.published_at or datetime.now(UTC)
            elif statuses and all(
                status in {DeliveryStatus.failed, DeliveryStatus.unconfigured, DeliveryStatus.skipped}
                for status in statuses
            ):
                alert.status = AlertStatus.delivery_failed
            elif any(status in {DeliveryStatus.failed, DeliveryStatus.unconfigured} for status in statuses):
                alert.status = AlertStatus.partially_delivered
            else:
                alert.status = AlertStatus.delivering

            alert.updated_at = datetime.now(UTC)

            if self._alert_repository is None:
                raise TransientHandoffDependencyError("Alert aggregate repository is not configured")
            try:
                alert = self._alert_repository.save_delivery(alert, records)
                if alert.status == AlertStatus.delivered and alert.referenced_alert_id:
                    self._alert_repository.supersede(
                        alert.tenant_id,
                        alert.referenced_alert_id,
                        alert.alert_id,
                    )
            except Exception as exc:
                raise TransientHandoffDependencyError(
                    f"Failed to persist delivery outcome for {alert.alert_id}"
                ) from exc

            # Persist delivery records
            if self._delivery_store is not None:
                for record in records:
                    try:
                        doc = record.model_dump(mode="json")
                        doc["id"] = record.delivery_id
                        self._delivery_store.create_item(body=doc)
                    except Exception:
                        logger.warning("Failed to persist delivery record %s", record.delivery_id)

            # Audit
            for record in records:
                dt = (
                    CommunicationDecisionType.delivery_succeeded
                    if record.delivery_status.value == "delivered"
                    else CommunicationDecisionType.delivery_failed
                )
                self._write_audit(
                    dt,
                    alert_id=alert.alert_id,
                    delivery_id=record.delivery_id,
                    output_summary=f"{record.channel.value}: {record.delivery_status.value}",
                    channel=record.channel.value,
                    audience_segment_id=record.audience_segment_id,
                    language=record.language_used,
                    retry_count=max(0, record.attempt_count - 1),
                    approval_mode=alert.approval_mode.value if alert.approval_mode else None,
                    tenant_id=alert.tenant_id,
                )

            return records

    def _stage_11_audit_finalise(
        self,
        event: AgentHandoffEvent,
        alert: PublicAlert,
        pipeline_elapsed_ms: float,
    ) -> None:
        """Stage 11: Audit Finalisation."""
        with pipeline_span("communication.stage.audit_finalise"):
            self._write_audit(
                CommunicationDecisionType.audit_finalised,
                handoff_id=event.handoff_id,
                alert_id=alert.alert_id,
                processing_duration_ms=int(pipeline_elapsed_ms),
                output_summary=(
                    f"Pipeline complete: {alert.alert_id} v{alert.version} "
                    f"status={alert.status.value} confidence={alert.confidence:.3f} "
                    f"elapsed={pipeline_elapsed_ms:.0f}ms"
                ),
                tenant_id=event.tenant_id,
            )
            expected = {
                CommunicationDecisionType.handoff_received,
                CommunicationDecisionType.data_retrieved,
                CommunicationDecisionType.audience_segmented,
                CommunicationDecisionType.alert_drafted,
                CommunicationDecisionType.content_safety_evaluated,
                CommunicationDecisionType.alert_versioned,
                CommunicationDecisionType.audit_finalised,
            }
            missing = self._audit_writer.missing_decisions(
                expected,
                tenant_id=event.tenant_id,
                handoff_id=event.handoff_id,
            )
            if missing:
                raise RuntimeError(
                    "Communication audit reconciliation failed: "
                    + ", ".join(sorted(decision.value for decision in missing))
                )

    def _write_audit(
        self,
        decision_type: CommunicationDecisionType,
        *,
        handoff_id: str | None = None,
        alert_id: str | None = None,
        delivery_id: str | None = None,
        confidence: float | None = None,
        confidence_penalties_applied: list[str] | None = None,
        processing_duration_ms: int | None = None,
        input_snapshot: dict[str, object] | None = None,
        output_summary: str | None = None,
        content_safety_results: dict[str, str] | None = None,
        generation_method: str | None = None,
        language: str | None = None,
        channel: str | None = None,
        audience_segment_id: str | None = None,
        retry_count: int | None = None,
        approval_mode: str | None = None,
        tenant_id: str,
    ) -> None:
        """Write a single audit record."""
        record = CommunicationDecisionRecord(
            handoff_id=handoff_id,
            alert_id=alert_id,
            delivery_id=delivery_id,
            correlation_id=handoff_id or alert_id or delivery_id or "communication",
            stage_name=decision_type.value,
            language=language,
            channel=channel,
            audience_segment_id=audience_segment_id,
            retry_count=retry_count,
            approval_mode=approval_mode,
            decision_type=decision_type,
            confidence=confidence,
            confidence_penalties_applied=confidence_penalties_applied,
            processing_duration_ms=processing_duration_ms,
            input_snapshot=input_snapshot,
            output_summary=output_summary,
            content_safety_results=content_safety_results,
            generation_method=generation_method,
            agent_version=self._config.agent_version,
            config_version=self._config.compute_config_hash(),
            tenant_id=tenant_id,
        )
        self._audit_writer.write(record)

    @property
    def processed_count(self) -> int:
        """Total handoffs successfully processed."""
        return self._processed_count
