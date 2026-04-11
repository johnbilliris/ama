"""Tests for communication.audit — AuditWriter with three-tier degradation."""

from unittest.mock import MagicMock

import pytest

from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.models import CommunicationDecisionRecord, CommunicationDecisionType


def _make_record(**overrides):
    defaults = dict(decision_type=CommunicationDecisionType.handoff_received)
    defaults.update(overrides)
    return CommunicationDecisionRecord(**defaults)


# ---------------------------------------------------------------------------
# Tier 1: Cosmos DB write
# ---------------------------------------------------------------------------


class TestTier1CosmosWrite:
    def test_write_to_cosmos_success(self):
        cosmos = MagicMock()
        writer = AuditWriter(cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        cosmos.create_item.assert_called_once()
        assert writer.get_status() == "healthy"
        assert writer.records_written == 1

    def test_write_sets_flush_source_direct(self):
        cosmos = MagicMock()
        writer = AuditWriter(cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        assert record.flush_source == "direct"


# ---------------------------------------------------------------------------
# Tier 2: In-memory buffer on Cosmos failure
# ---------------------------------------------------------------------------


class TestTier2MemoryBuffer:
    def test_buffer_on_cosmos_failure(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = RuntimeError("Cosmos unavailable")
        writer = AuditWriter(cosmos_client=cosmos)
        record = _make_record()
        writer.write(record)
        assert writer.buffer_depth == 1
        assert writer.get_status() == "buffering"

    def test_buffer_accumulates(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = RuntimeError("Cosmos unavailable")
        writer = AuditWriter(cosmos_client=cosmos)
        for _ in range(5):
            writer.write(_make_record())
        assert writer.buffer_depth == 5

    def test_no_cosmos_uses_buffer(self):
        writer = AuditWriter(cosmos_client=None)
        record = _make_record()
        writer.write(record)
        assert writer.buffer_depth == 1


# ---------------------------------------------------------------------------
# Tier 3: File spill when buffer full
# ---------------------------------------------------------------------------


class TestTier3FileSpill:
    def test_spill_to_file_when_buffer_full(self, tmp_path):
        cfg = CommunicationConfig.__new__(CommunicationConfig)
        object.__setattr__(cfg, "audit_buffer_capacity", 2)
        object.__setattr__(cfg, "audit_buffer_file_path", str(tmp_path / "audit.jsonl"))
        # Set remaining required defaults
        object.__setattr__(cfg, "agent_version", "0.1.0")

        writer = AuditWriter(config=cfg, cosmos_client=None)
        # Fill buffer
        writer.write(_make_record())
        writer.write(_make_record())
        # This should spill to file
        writer.write(_make_record())
        assert writer.get_status() == "degraded"
        spill_file = tmp_path / "audit.jsonl"
        assert spill_file.exists()


# ---------------------------------------------------------------------------
# get_status()
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_healthy_with_cosmos(self):
        cosmos = MagicMock()
        writer = AuditWriter(cosmos_client=cosmos)
        assert writer.get_status() == "healthy"

    def test_buffering_after_failure(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = RuntimeError("fail")
        writer = AuditWriter(cosmos_client=cosmos)
        writer.write(_make_record())
        assert writer.get_status() == "buffering"


# ---------------------------------------------------------------------------
# flush()
# ---------------------------------------------------------------------------


class TestFlush:
    def test_flush_drains_buffer(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = RuntimeError("fail")
        writer = AuditWriter(cosmos_client=cosmos)

        # Buffer some records
        for _ in range(3):
            writer.write(_make_record())
        assert writer.buffer_depth == 3

        # Fix cosmos and flush
        cosmos.create_item.side_effect = None
        flushed = writer.flush()
        assert flushed == 3
        assert writer.buffer_depth == 0

    def test_flush_no_cosmos_returns_zero(self):
        writer = AuditWriter(cosmos_client=None)
        writer.write(_make_record())
        assert writer.flush() == 0

    def test_flush_file_buffer(self, tmp_path):
        cfg = CommunicationConfig.__new__(CommunicationConfig)
        object.__setattr__(cfg, "audit_buffer_capacity", 1)
        object.__setattr__(cfg, "audit_buffer_file_path", str(tmp_path / "audit.jsonl"))
        object.__setattr__(cfg, "agent_version", "0.1.0")

        writer = AuditWriter(config=cfg, cosmos_client=None)
        writer.write(_make_record())
        writer.write(_make_record())  # spills to file

        # Now give it a cosmos client and flush
        cosmos = MagicMock()
        writer._cosmos_client = cosmos
        flushed = writer.flush()
        assert flushed >= 1

    def test_flush_partial_failure_stops(self):
        cosmos = MagicMock()
        cosmos.create_item.side_effect = RuntimeError("fail")
        writer = AuditWriter(cosmos_client=cosmos)

        writer.write(_make_record())
        writer.write(_make_record())
        assert writer.buffer_depth == 2

        # Flush still fails → returns 0
        flushed = writer.flush()
        assert flushed == 0
        assert writer.buffer_depth == 2
