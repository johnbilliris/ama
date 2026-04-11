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
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydantic import ValidationError

from common.content_safety import ContentSafetyValidator
from common.handoffs import AgentHandoffEvent

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
    GenerationMethod,
    PublicAlert,
    SegmentPriority,
    UrgencyLevel,
)
from communication.segmentation import AudienceSegmenter
from communication.templates import TemplateLoader
from communication.telemetry import CustomEventEmitter, metrics, pipeline_span
from communication.translator import MultilingualTranslator
from communication.versioning import VersionCounter

logger = logging.getLogger(__name__)


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
        alert_store: object | None = None,
        assessment_store: object | None = None,
        recommendation_store: object | None = None,
        delivery_store: object | None = None,
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
        self._delivery_store = delivery_store
        self._processed_count = 0

    def process_handoff(self, event: AgentHandoffEvent) -> PublicAlert | None:
        """Process a single handoff through the 11-stage pipeline.

        Returns PublicAlert on success, None on rejection/discard.
        """
        pipeline_start = time.perf_counter()

        with pipeline_span("communication.pipeline.process", {
            "handoff_id": event.handoff_id,
            "incident_id": event.incident_id,
        }):
            try:
                # Stage 1: Handoff Intake & Validation
                if not self._stage_1_intake(event):
                    return None

                # Stage 2: Data Retrieval
                assessment_data, recommendation_data = self._stage_2_retrieve(event)

                # Stage 3: Audience Segmentation
                segments = self._stage_3_segment(event, assessment_data)

                # Stage 4: Template Loading
                template_values = self._stage_4_templates(event, assessment_data)

                # Stage 5: Multilingual Alert Drafting
                content_blocks = self._stage_5_draft(event, template_values, assessment_data)

                # Stage 6: Back-Translation Quality Validation
                content_blocks, bt_penalty = self._stage_6_back_translate(content_blocks)

                # Stage 7: Content Safety Validation
                content_blocks, safety_result, safety_details = self._stage_7_content_safety(
                    content_blocks, template_values, assessment_data
                )

                # Stage 8: Alert Versioning & Persistence
                alert = self._stage_8_version_persist(
                    event, content_blocks, segments, safety_result,
                    safety_details, bt_penalty, recommendation_data,
                )

                # Stage 9: Approval Notification (stub — full in US2)
                self._stage_9_approval(alert)

                # Stage 10: Delivery (stub — full in US3, triggered by approval)
                # Delivery happens after commander approval, not here

                # Stage 11: Audit Finalisation
                pipeline_elapsed = (time.perf_counter() - pipeline_start) * 1000
                self._stage_11_audit_finalise(event, alert, pipeline_elapsed)

                self._processed_count += 1
                metrics.pipeline_total_latency.record(pipeline_elapsed)
                metrics.active_alerts_count.add(1)

                return alert

            except Exception as exc:
                logger.error(
                    "Pipeline failed for handoff %s: %s",
                    event.handoff_id, exc, exc_info=True,
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
                CustomEventEmitter.handoff_rejected(event.handoff_id, "wrong_target_agent")
                return False

            # Check dedup by handoff ID
            if self._deduplicator.is_duplicate_by_id(event.handoff_id):
                self._write_audit(
                    CommunicationDecisionType.duplicate_discarded,
                    handoff_id=event.handoff_id,
                    output_summary="Duplicate handoff ID",
                    tenant_id=event.tenant_id,
                )
                CustomEventEmitter.duplicate_discarded(event.handoff_id)
                return False

            # Check dedup by incident+hazard
            hazard_type = event.payload.get("hazard_type", "general")
            if self._deduplicator.is_duplicate_by_incident(
                event.incident_id, str(hazard_type)
            ):
                self._write_audit(
                    CommunicationDecisionType.duplicate_discarded,
                    handoff_id=event.handoff_id,
                    output_summary=f"Duplicate incident+hazard: {event.incident_id}/{hazard_type}",
                    tenant_id=event.tenant_id,
                )
                CustomEventEmitter.duplicate_discarded(event.handoff_id)
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
            CustomEventEmitter.handoff_received(event.handoff_id, event.incident_id)
            return True

    def _stage_2_retrieve(
        self, event: AgentHandoffEvent
    ) -> tuple[dict, dict]:
        """Stage 2: Data Retrieval — get recommendation and assessment."""
        with pipeline_span("communication.stage.retrieve"):
            recommendation_id = str(event.payload.get("recommendationId", ""))
            assessment_id = str(event.payload.get("assessmentId", ""))

            recommendation_data: dict = {}
            assessment_data: dict = {}

            if self._recommendation_store and recommendation_id:
                try:
                    recommendation_data = self._recommendation_store.read_item(
                        item=recommendation_id,
                        partition_key=event.scope_key,
                    )
                except Exception:
                    logger.warning("Failed to retrieve recommendation %s", recommendation_id)

            if self._assessment_store and assessment_id:
                try:
                    assessment_data = self._assessment_store.read_item(
                        item=assessment_id,
                        partition_key=event.scope_key,
                    )
                except Exception:
                    logger.warning("Failed to retrieve assessment %s", assessment_id)

            # Use payload as fallback
            if not recommendation_data:
                recommendation_data = {
                    "recommendation_id": recommendation_id or event.handoff_id,
                    "summary": str(event.payload.get("summary", "")),
                    "explanation": str(event.payload.get("explanation", "")),
                }
            if not assessment_data:
                assessment_data = {
                    "assessment_id": assessment_id or event.handoff_id,
                    "hazard_type": str(event.payload.get("hazard_type", "general")),
                    "severity": str(event.payload.get("severity", "moderate")),
                    "location": str(event.payload.get("location", "affected area")),
                    "zones": event.payload.get("zones", []),
                    "vulnerability_data": event.payload.get("vulnerability_data", {}),
                }

            return assessment_data, recommendation_data

    def _stage_3_segment(
        self, event: AgentHandoffEvent, assessment_data: dict
    ) -> list[AudienceSegment]:
        """Stage 3: Audience Segmentation."""
        with pipeline_span("communication.stage.segment"):
            demographics = dict(event.payload.get("demographics", {}) or {})
            segments = self._segmenter.segment_audience(assessment_data, demographics)
            metrics.audience_segment_count.record(len(segments))

            self._write_audit(
                CommunicationDecisionType.audience_segmented,
                handoff_id=event.handoff_id,
                output_summary=f"{len(segments)} segments created",
                tenant_id=event.tenant_id,
            )
            return segments

    def _stage_4_templates(
        self, event: AgentHandoffEvent, assessment_data: dict
    ) -> dict[str, str]:
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
        assessment_data: dict,
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
            )

            draft_elapsed = (time.perf_counter() - draft_start) * 1000
            metrics.alert_draft_latency.record(draft_elapsed)
            CustomEventEmitter.alert_drafted(
                alert_id="pending", languages=len(content_blocks)
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
                    score = self._translator.back_translate_and_score(block, en_au)
                    block.back_translation_score = score

                    if score < self._config.back_translation_threshold:
                        block.back_translation_flagged = True
                        bt_penalty = self._config.back_translation_penalty_factor
                        metrics.back_translation_quality.record(score, {"language": lang})
                        CustomEventEmitter.back_translation_flagged(
                            alert_id="pending", language=lang, score=score
                        )
                        self._write_audit(
                            CommunicationDecisionType.back_translation_below_threshold,
                            output_summary=f"{lang} score={score:.3f} < {self._config.back_translation_threshold}",
                        )
                    else:
                        metrics.back_translation_quality.record(score, {"language": lang})
                except Exception:
                    # Embedding outage → skip per CHK051
                    logger.warning("Back-translation check failed for %s, skipping", lang)
                    CustomEventEmitter.degradation_detected(
                        service="embedding", fallback="skip_back_translation"
                    )

            return content_blocks, bt_penalty

    def _stage_7_content_safety(
        self,
        content_blocks: dict[str, ContentBlock],
        template_values: dict[str, str],
        assessment_data: dict,
    ) -> tuple[dict[str, ContentBlock], ContentSafetyResult, dict[str, ContentSafetyDetail]]:
        """Stage 7: Content Safety Validation."""
        safety_start = time.perf_counter()

        with pipeline_span("communication.stage.content_safety"):
            overall_result = ContentSafetyResult.passed
            safety_details: dict[str, ContentSafetyDetail] = {}

            for lang, block in content_blocks.items():
                # Skip validation for template-based content per FR-014
                if block.generation_method in (
                    GenerationMethod.template, GenerationMethod.template_fallback
                ):
                    safety_details[lang] = ContentSafetyDetail(
                        language_code=lang,
                        passed=True,
                        original_text_length=len(block.body),
                    )
                    block.content_safety_result = "not_checked"
                    continue

                # Validate LLM-generated content
                full_text = f"{block.title} {block.body} {block.action_items}"
                result = self._content_safety.validate(
                    text=full_text,
                    expected_language=lang,
                    max_length=self._config.content_max_length,
                )

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
                    alert_type = "evacuation"

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
                    metrics.content_safety_failure_rate.add(1, {"language": lang})
                    CustomEventEmitter.content_safety_failed(
                        alert_id="pending", language=lang, reason=result.reason or ""
                    )
                else:
                    block.content_safety_result = "passed"

                self._write_audit(
                    CommunicationDecisionType.content_safety_evaluated,
                    content_safety_results={lang: result.result},
                )

            safety_elapsed = (time.perf_counter() - safety_start) * 1000
            metrics.content_safety_check_latency.record(safety_elapsed)

            return content_blocks, overall_result, safety_details

    def _stage_8_version_persist(
        self,
        event: AgentHandoffEvent,
        content_blocks: dict[str, ContentBlock],
        segments: list[AudienceSegment],
        safety_result: ContentSafetyResult,
        safety_details: dict[str, ContentSafetyDetail],
        bt_penalty: float,
        recommendation_data: dict,
    ) -> PublicAlert:
        """Stage 8: Alert Versioning & Persistence."""
        with pipeline_span("communication.stage.version_persist"):
            # Assign version
            version = self._version_counter.assign_version(event.incident_id)
            alert_id = self._version_counter.format_alert_id(event.incident_id, version)

            # Compute confidence with compound penalties per CHK031
            freshness_penalty = self._config.freshness_penalty_factor
            fallback_penalty = 1.0

            # Check if any language used template fallback
            for block in content_blocks.values():
                if block.generation_method in (
                    GenerationMethod.template_fallback, GenerationMethod.safety_fallback
                ):
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
                change_type = ChangeType.initial

            # Build alert
            recommendation_id = str(
                recommendation_data.get("recommendation_id", event.handoff_id)
            )
            assessment_id = str(event.payload.get("assessmentId", event.handoff_id))

            channels = [
                ChannelType(ch) for ch in self._config.delivery_channels
                if ch in ChannelType.__members__
            ]

            alert = PublicAlert(
                alert_id=alert_id,
                incident_id=event.incident_id,
                version=version,
                status=AlertStatus.pending_review,
                change_type=change_type,
                change_summary=str(event.payload.get("change_summary")) if change_type != ChangeType.initial else None,
                referenced_alert_id=str(event.payload.get("referenced_alert_id")) if change_type in (ChangeType.correction, ChangeType.all_clear) else None,
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
                tenant_id=event.tenant_id,
                expires_at=datetime.now(UTC) + timedelta(hours=self._config.alert_expiry_hours),
            )

            # Supersede previous version
            if version > 1:
                self._version_counter.supersede_previous(
                    event.incident_id, version, event.tenant_id
                )

            # Persist to Cosmos
            if self._alert_store is not None:
                try:
                    doc = alert.model_dump(mode="json")
                    doc["id"] = alert.alert_id
                    self._alert_store.create_item(body=doc)
                except Exception as exc:
                    logger.error("Failed to persist alert %s: %s", alert_id, exc)

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
                alert_id=alert_id, version=version, change_type=change_type.value
            )
            metrics.pending_approvals.add(1)

            return alert

    def _stage_9_approval(self, alert: PublicAlert) -> None:
        """Stage 9: Approval Notification (stub — full implementation in US2)."""
        with pipeline_span("communication.stage.approval"):
            self._write_audit(
                CommunicationDecisionType.approval_requested,
                alert_id=alert.alert_id,
                output_summary=f"Approval requested for {alert.alert_id}",
                tenant_id=alert.tenant_id,
            )
            CustomEventEmitter.approval_requested(alert_id=alert.alert_id)

    def deliver_approved_alert(
        self,
        alert: PublicAlert,
        segments: list[AudienceSegment],
    ) -> list[DeliveryRecord]:
        """Stage 10: Multi-Channel Delivery (called after approval)."""
        with pipeline_span("communication.stage.delivery"):
            alert.status = AlertStatus.delivering
            alert.updated_at = datetime.now(UTC)

            records = self._delivery_service.deliver_alert(alert, segments)

            # Determine overall status
            statuses = [r.delivery_status for r in records if not r.is_deduplicated]
            if all(s.value == "delivered" for s in statuses):
                alert.status = AlertStatus.delivered
            elif any(s.value == "failed" for s in statuses):
                alert.status = AlertStatus.partially_delivered
            else:
                alert.status = AlertStatus.delivered

            alert.published_at = alert.published_at or datetime.now(UTC)
            alert.updated_at = datetime.now(UTC)

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
                CommunicationDecisionType.handoff_received,
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
        input_snapshot: dict | None = None,
        output_summary: str | None = None,
        content_safety_results: dict[str, str] | None = None,
        generation_method: str | None = None,
        tenant_id: str = "live",
    ) -> None:
        """Write a single audit record."""
        record = CommunicationDecisionRecord(
            handoff_id=handoff_id,
            alert_id=alert_id,
            delivery_id=delivery_id,
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
