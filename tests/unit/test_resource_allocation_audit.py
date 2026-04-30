"""Unit tests for audit writer with three-tier degradation.

Covers:
- Tier 1 Cosmos write success
- Tier 2 in-memory ring buffer on Cosmos failure
- Tier 3 JSONL file spill when buffer full
- Recovery flush (memory → file → Cosmos)
- Audit status reporting
"""

from __future__ import annotations

from unittest.mock import MagicMock

from resource_allocation.audit import AuditWriter
from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.models import (
    AllocationDecisionRecord,
    DecisionType,
)


def _make_record(handoff_id="h-001", decision_type=DecisionType.handoff_received):
    return AllocationDecisionRecord(
        handoff_id=handoff_id,
        decision_type=decision_type,
        decision_rationale="Test record",
    )


class TestTier1CosmosWrite:
    def test_write_success(self):
        mock_cosmos = MagicMock()
        writer = AuditWriter(cosmos_client=mock_cosmos)
        record = _make_record()

        writer.write(record)

        mock_cosmos.create_item.assert_called_once()
        assert writer.get_status() == "healthy"
        assert writer.buffer_depth == 0


class TestTier2MemoryBuffer:
    def test_buffer_on_cosmos_failure(self):
        mock_cosmos = MagicMock()
        mock_cosmos.create_item.side_effect = Exception("Cosmos unavailable")
        writer = AuditWriter(cosmos_client=mock_cosmos)
        record = _make_record()

        writer.write(record)

        assert writer.buffer_depth == 1
        assert writer.get_status() == "buffering"

    def test_buffer_multiple_records(self):
        mock_cosmos = MagicMock()
        mock_cosmos.create_item.side_effect = Exception("Cosmos unavailable")
        writer = AuditWriter(cosmos_client=mock_cosmos)

        for i in range(5):
            writer.write(_make_record(handoff_id=f"h-{i}"))

        assert writer.buffer_depth == 5

    def test_buffer_bounded_by_capacity(self):
        config = ResourceAllocationConfig()
        # Override buffer capacity to small value
        mock_cosmos = MagicMock()
        mock_cosmos.create_item.side_effect = Exception("Cosmos unavailable")

        writer = AuditWriter(config=config, cosmos_client=mock_cosmos)
        assert writer._buffer.maxlen is not None  # verify maxlen is set


class TestTier3FileSpill:
    def test_file_spill_when_buffer_full(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AUDIT_BUFFER_CAPACITY", "2")
        file_path = str(tmp_path / "audit.jsonl")
        monkeypatch.setenv("AUDIT_BUFFER_FILE_PATH", file_path)
        config = ResourceAllocationConfig()
        mock_cosmos = MagicMock()
        mock_cosmos.create_item.side_effect = Exception("Cosmos unavailable")

        writer = AuditWriter(config=config, cosmos_client=mock_cosmos)

        # Write 3 records — first 2 go to memory buffer, 3rd spills to file
        for i in range(3):
            writer.write(_make_record(handoff_id=f"h-{i}"))

        assert writer._file_spill_count >= 1


class TestNoCosmosClient:
    def test_write_without_cosmos_buffers(self):
        writer = AuditWriter()  # No cosmos client
        record = _make_record()
        writer.write(record)
        assert writer.buffer_depth == 1


class TestFlush:
    def test_flush_drains_buffer(self):
        mock_cosmos = MagicMock()
        # First call fails (to buffer), then succeeds (for flush)
        mock_cosmos.create_item.side_effect = [
            Exception("fail"),
            Exception("fail"),
            Exception("fail"),
            None,
            None,
            None,  # flush succeeds
        ]
        writer = AuditWriter(cosmos_client=mock_cosmos)

        for i in range(3):
            writer.write(_make_record(handoff_id=f"h-{i}"))
        assert writer.buffer_depth == 3

        # Now cosmos is available
        mock_cosmos.create_item.side_effect = None
        flushed = writer.flush()
        assert flushed == 3
        assert writer.buffer_depth == 0

    def test_flush_without_cosmos(self):
        writer = AuditWriter()  # No cosmos
        flushed = writer.flush()
        assert flushed == 0


class TestAuditStatus:
    def test_healthy_status(self):
        mock_cosmos = MagicMock()
        writer = AuditWriter(cosmos_client=mock_cosmos)
        assert writer.get_status() == "healthy"

    def test_buffering_status(self):
        mock_cosmos = MagicMock()
        mock_cosmos.create_item.side_effect = Exception("fail")
        writer = AuditWriter(cosmos_client=mock_cosmos)
        writer.write(_make_record())
        assert writer.get_status() == "buffering"
