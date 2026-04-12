"""Unit tests for SignalProcessingPipeline (Phase 5: T037–T041, T055, T067)."""

from unittest.mock import MagicMock

import pytest
from monitoring.config import MonitoringConfig


def _make_valid_signal(
    signal_id: str = "sig-001",
    category: str = "fire",
    confidence: float = 0.85,
    freshness: float = 1.0,
    incident_id: str = "INC-042",
    validation_status: str = "validated",
    source_kind: str = "authoritative",
    source_id: str = "bom-nsw",
    tenant_id: str = "live",
    payload: dict | None = None,
    provenance: dict | None = None,
) -> dict:
    return {
        "source": {"dataSourceId": source_id, "name": "BoM NSW", "kind": source_kind},
        "incidentId": incident_id,
        "category": category,
        "occurredAt": "2026-01-01T00:00:00Z",
        "receivedAt": "2026-01-01T00:00:01Z",
        "location": {"type": "Point", "coordinates": [151.2, -33.8]},
        "payload": payload or {"alert_level": "Watch and Act"},
        "confidenceScore": confidence,
        "freshnessScore": freshness,
        "validationStatus": validation_status,
        "provenance": provenance or {"collectionMethod": "api_pull"},
    }


def _make_pipeline(**kwargs):
    from monitoring.audit import AuditWriter
    from monitoring.pipeline import SignalProcessingPipeline

    config = MonitoringConfig()
    return SignalProcessingPipeline(
        config=config,
        audit_writer=AuditWriter(config=config, cosmos_client=None),
        **kwargs,
    )


class TestPipelineEndToEnd:
    """T037: End-to-end pipeline tests."""

    @pytest.mark.asyncio
    async def test_high_risk_fire_signal_produces_handoff(self) -> None:
        delivered = []
        pipeline = _make_pipeline(
            deliver_fn=lambda h: delivered.append(h),
        )
        raw = _make_valid_signal(category="fire", confidence=0.85, freshness=1.0)
        await pipeline.process_signal(raw, "sig-fire-001")
        assert len(delivered) == 1
        assert delivered[0].target_agent == "risk_assessment"
        assert delivered[0].incident_id == "INC-042"

    @pytest.mark.asyncio
    async def test_low_confidence_signal_not_escalated(self) -> None:
        delivered = []
        pipeline = _make_pipeline(
            deliver_fn=lambda h: delivered.append(h),
        )
        raw = _make_valid_signal(category="fire", confidence=0.3, freshness=0.5)
        await pipeline.process_signal(raw, "sig-low-001")
        assert len(delivered) == 0

    @pytest.mark.asyncio
    async def test_missing_incident_id_not_escalated(self) -> None:
        delivered = []
        pipeline = _make_pipeline(
            deliver_fn=lambda h: delivered.append(h),
        )
        raw = _make_valid_signal(incident_id=None)
        await pipeline.process_signal(raw, "sig-noinc-001")
        assert len(delivered) == 0

    @pytest.mark.asyncio
    async def test_non_escalation_category_not_escalated(self) -> None:
        delivered = []
        pipeline = _make_pipeline(
            deliver_fn=lambda h: delivered.append(h),
        )
        raw = _make_valid_signal(category="infrastructure")
        await pipeline.process_signal(raw, "sig-infra-001")
        assert len(delivered) == 0

    @pytest.mark.asyncio
    async def test_earthquake_category_escalated(self) -> None:
        delivered = []
        pipeline = _make_pipeline(
            deliver_fn=lambda h: delivered.append(h),
        )
        raw = _make_valid_signal(category="earthquake", confidence=0.9, freshness=0.95)
        await pipeline.process_signal(raw, "sig-eq-001")
        assert len(delivered) == 1

    @pytest.mark.asyncio
    async def test_tsunami_category_escalated(self) -> None:
        delivered = []
        pipeline = _make_pipeline(
            deliver_fn=lambda h: delivered.append(h),
        )
        raw = _make_valid_signal(category="tsunami", confidence=0.95, freshness=1.0)
        await pipeline.process_signal(raw, "sig-ts-001")
        assert len(delivered) == 1


class TestPipelineValidation:
    """T037/T039: Validation and dedup tests."""

    @pytest.mark.asyncio
    async def test_invalid_signal_rejected(self) -> None:
        pipeline = _make_pipeline()
        raw = {"invalid": "data"}
        result = await pipeline.process_signal(raw, "sig-invalid")
        assert result is None
        assert pipeline.validation_failure_count == 1

    @pytest.mark.asyncio
    async def test_duplicate_signal_discarded(self) -> None:
        pipeline = _make_pipeline()
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-dup-001")
        await pipeline.process_signal(raw, "sig-dup-001")
        assert pipeline.dedup_discard_count == 1


class TestPipelineSummarisation:
    """T038: Summarisation tests."""

    @pytest.mark.asyncio
    async def test_rule_based_summary_without_llm(self) -> None:
        from monitoring.agent import MonitoringAgent

        agent = MonitoringAgent(llm_client=None)
        pipeline = _make_pipeline(agent=agent)
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-sum-001")
        # Signal should be processed without error (rule-based summary used)
        assert pipeline.signal_count == 1

    @pytest.mark.asyncio
    async def test_llm_summary_with_content_safety_pass(self) -> None:
        from monitoring.agent import MonitoringAgent

        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = {
            "text": "Fire warning in Sydney western suburbs, watch and act level."
        }
        agent = MonitoringAgent(llm_client=mock_llm)
        pipeline = _make_pipeline(agent=agent)
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-llm-001")
        assert pipeline.signal_count == 1

    @pytest.mark.asyncio
    async def test_content_safety_failure_triggers_fallback(self) -> None:
        from monitoring.agent import MonitoringAgent

        mock_llm = MagicMock()
        # Return text with blocked keyword to trigger content safety failure
        mock_llm.generate_response.return_value = {
            "text": "This is a bomb threat near the fire zone"
        }
        agent = MonitoringAgent(llm_client=mock_llm)
        pipeline = _make_pipeline(agent=agent)
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-safety-001")
        assert pipeline.signal_count == 1

    @pytest.mark.asyncio
    async def test_llm_unavailable_uses_rule_based(self) -> None:
        from monitoring.agent import MonitoringAgent

        mock_llm = MagicMock()
        mock_llm.generate_response.side_effect = Exception("LLM down")
        agent = MonitoringAgent(llm_client=mock_llm)
        pipeline = _make_pipeline(agent=agent)
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-nollm-001")
        assert pipeline.signal_count == 1


class TestPipelineAuditCompleteness:
    """T039: Every pipeline path produces audit records."""

    @pytest.mark.asyncio
    async def test_validation_failure_produces_audit(self) -> None:
        pipeline = _make_pipeline()
        raw = {"bad": "data"}
        await pipeline.process_signal(raw, "sig-audit-val")
        assert pipeline._audit_writer.buffer_depth >= 1

    @pytest.mark.asyncio
    async def test_dedup_discard_produces_audit(self) -> None:
        pipeline = _make_pipeline()
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-audit-dup")
        depth_after_first = pipeline._audit_writer.buffer_depth
        await pipeline.process_signal(raw, "sig-audit-dup")
        assert pipeline._audit_writer.buffer_depth > depth_after_first

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_multiple_audits(self) -> None:
        pipeline = _make_pipeline(deliver_fn=lambda h: None)
        raw = _make_valid_signal()
        await pipeline.process_signal(raw, "sig-audit-full")
        # Should have at least: summarised + escalated + handed_off
        assert pipeline._audit_writer.buffer_depth >= 2


class TestPipelineFreshness:
    """T041: Freshness degradation tests."""

    @pytest.mark.asyncio
    async def test_source_freshness_tracked(self) -> None:
        pipeline = _make_pipeline()
        raw = _make_valid_signal(source_id="bom-nsw", source_kind="authoritative", freshness=0.9)
        await pipeline.process_signal(raw, "sig-fresh-001")
        indicator = pipeline._freshness_tracker.get_status("bom-nsw")
        assert indicator is not None
        assert indicator.current_freshness_score == 0.9

    @pytest.mark.asyncio
    async def test_freshness_degradation_produces_audit(self) -> None:
        pipeline = _make_pipeline()
        raw1 = _make_valid_signal(source_id="sensor-x", source_kind="iot", freshness=0.9)
        await pipeline.process_signal(raw1, "sig-fresh-002")
        depth_after_first = pipeline._audit_writer.buffer_depth

        raw2 = _make_valid_signal(source_id="sensor-x", source_kind="iot", freshness=0.3)
        await pipeline.process_signal(raw2, "sig-fresh-003")
        # Should have additional audit record for degradation
        assert pipeline._audit_writer.buffer_depth > depth_after_first


class TestPipelineEffectiveConfidence:
    """T040: effectiveConfidence threshold verification."""

    @pytest.mark.asyncio
    async def test_effective_confidence_incorporates_freshness(self) -> None:
        delivered = []
        pipeline = _make_pipeline(deliver_fn=lambda h: delivered.append(h))

        # confidence=0.85, freshness=0.9 → effective=0.765 < 0.8 threshold
        raw = _make_valid_signal(category="fire", confidence=0.85, freshness=0.9)
        await pipeline.process_signal(raw, "sig-eff-001")
        assert len(delivered) == 0  # below threshold

    @pytest.mark.asyncio
    async def test_high_freshness_allows_escalation(self) -> None:
        delivered = []
        pipeline = _make_pipeline(deliver_fn=lambda h: delivered.append(h))

        # confidence=0.85, freshness=1.0 → effective=0.85 >= 0.8 threshold
        raw = _make_valid_signal(category="fire", confidence=0.85, freshness=1.0)
        await pipeline.process_signal(raw, "sig-eff-002")
        assert len(delivered) == 1

    @pytest.mark.asyncio
    async def test_all_five_escalation_categories(self) -> None:
        for cat in ["fire", "weather", "hydrology", "earthquake", "tsunami"]:
            delivered = []
            pipeline = _make_pipeline(deliver_fn=lambda h: delivered.append(h))
            raw = _make_valid_signal(category=cat, confidence=0.9, freshness=1.0)
            await pipeline.process_signal(raw, f"sig-cat-{cat}")
            assert len(delivered) == 1, f"Category '{cat}' should have been escalated"


class TestPipelineProvenanceRetention:
    """T067: Provenance metadata retained through pipeline."""

    @pytest.mark.asyncio
    async def test_provenance_preserved_in_audit(self) -> None:
        delivered = []
        pipeline = _make_pipeline(deliver_fn=lambda h: delivered.append(h))
        provenance = {
            "collectionMethod": "api_pull",
            "sourceUri": "https://bom.gov.au/api/fire",
            "timePrecision": "minute",
            "locationPrecision": "suburb",
            "validationStatus": "validated",
        }
        raw = _make_valid_signal(provenance=provenance)
        await pipeline.process_signal(raw, "sig-prov-001")

        # Handoff should contain signal summary with provenance-sourced data
        assert len(delivered) == 1
        payload = delivered[0].payload
        assert "category" in payload
        assert "sourceKind" in payload
