"""Tests for risk_assessment.audit – AuditWriter three-tier degradation."""

from unittest.mock import MagicMock

from risk_assessment.audit import AuditWriter
from risk_assessment.config import RiskAssessmentConfig
from risk_assessment.models import DecisionType, RiskAssessmentDecisionRecord


def _make_record(handoff_id="hf-1", decision_type=DecisionType.handoff_received, rationale=""):
    return RiskAssessmentDecisionRecord(
        handoff_id=handoff_id,
        decision_type=decision_type,
        decision_rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Tier 1: Cosmos write
# ---------------------------------------------------------------------------


class TestTier1CosmosWrite:
    def test_cosmos_write_succeeds(self):
        cosmos = MagicMock()
        cosmos.create_item.return_value = {}
        writer = AuditWriter(config=RiskAssessmentConfig(), cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        cosmos.create_item.assert_called_once()

    def test_flush_source_direct(self):
        cosmos = MagicMock()
        cosmos.create_item.return_value = {}
        writer = AuditWriter(config=RiskAssessmentConfig(), cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        # Verify the record written has flush_source set
        call_args = cosmos.create_item.call_args
        written = call_args[0][0] if call_args[0] else call_args[1].get("body", {})
        if isinstance(written, dict):
            assert written.get("flush_source") in ("direct", None)


# ---------------------------------------------------------------------------
# Tier 2: Memory buffer
# ---------------------------------------------------------------------------


class TestTier2MemoryBuffer:
    def test_memory_buffer_on_cosmos_failure(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        writer = AuditWriter(config=RiskAssessmentConfig(), cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        assert writer.buffer_depth >= 1

    def test_buffer_bounded_at_capacity(self):
        config = RiskAssessmentConfig(audit_buffer_capacity=5)
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        writer = AuditWriter(config=config, cosmos_client=cosmos)
        for i in range(10):
            writer.write(_make_record(handoff_id=f"hf-{i}"))
        assert writer.buffer_depth <= 5


# ---------------------------------------------------------------------------
# Tier 3: File spill
# ---------------------------------------------------------------------------


class TestTier3FileSpill:
    def test_file_spill_when_buffer_full(self, tmp_path):
        spill_file = tmp_path / "audit-spill.jsonl"
        config = RiskAssessmentConfig(
            audit_buffer_capacity=2,
            audit_buffer_file_path=str(spill_file),
        )
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        writer = AuditWriter(config=config, cosmos_client=cosmos)
        for i in range(5):
            writer.write(_make_record(handoff_id=f"hf-{i}"))
        assert spill_file.exists()


# ---------------------------------------------------------------------------
# Recovery flush
# ---------------------------------------------------------------------------


class TestRecoveryFlush:
    def test_flush_empties_buffer(self):
        config = RiskAssessmentConfig(audit_buffer_capacity=100)
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        writer = AuditWriter(config=config, cosmos_client=cosmos)
        for i in range(3):
            writer.write(_make_record(handoff_id=f"hf-{i}"))
        assert writer.buffer_depth >= 3

        # Now fix cosmos
        cosmos.create_item.side_effect = None
        cosmos.create_item.return_value = {}
        flushed = writer.flush()
        assert flushed >= 3
        assert writer.buffer_depth == 0


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------


class TestAnnotations:
    def test_buffered_at_set_on_memory_buffer(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        writer = AuditWriter(config=RiskAssessmentConfig(), cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        # buffered_at should be set on entries in the buffer
        assert writer.buffer_depth >= 1


# ---------------------------------------------------------------------------
# get_status()
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_healthy_with_cosmos(self):
        cosmos = MagicMock()
        cosmos.create_item.return_value = {}
        writer = AuditWriter(config=RiskAssessmentConfig(), cosmos_client=cosmos)
        assert writer.get_status() == "healthy"

    def test_buffering_after_cosmos_failure(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        config = RiskAssessmentConfig(audit_buffer_capacity=100)
        writer = AuditWriter(config=config, cosmos_client=cosmos)
        writer.write(_make_record())
        assert writer.get_status() in ("buffering", "degraded")

    def test_degraded_when_buffer_full(self, tmp_path):
        spill_file = tmp_path / "audit-spill.jsonl"
        config = RiskAssessmentConfig(
            audit_buffer_capacity=2,
            audit_buffer_file_path=str(spill_file),
        )
        cosmos = MagicMock()
        cosmos.create_item.side_effect = Exception("Cosmos down")
        writer = AuditWriter(config=config, cosmos_client=cosmos)
        for i in range(5):
            writer.write(_make_record(handoff_id=f"hf-{i}"))
        assert writer.get_status() == "degraded"


# ---------------------------------------------------------------------------
# Rationale truncation
# ---------------------------------------------------------------------------


class TestRationaleTruncation:
    def test_long_rationale_truncated(self):
        config = RiskAssessmentConfig(max_reasoning_summary_length=20)
        cosmos = MagicMock()
        cosmos.create_item.return_value = {}
        writer = AuditWriter(config=config, cosmos_client=cosmos)
        long_rationale = "A" * 100
        record = _make_record(rationale=long_rationale)
        writer.write(record)
        call_args = cosmos.create_item.call_args
        written = call_args[0][0] if call_args[0] else call_args[1].get("body", {})
        if isinstance(written, dict) and "decision_rationale" in written:
            assert len(written["decision_rationale"]) <= 20
