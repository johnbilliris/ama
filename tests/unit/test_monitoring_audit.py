"""Unit tests for AuditWriter with three-tier degradation (Phase 3: T018)."""

import os
import tempfile
from unittest.mock import MagicMock


def _make_record(signal_id: str = "sig-test"):
    from monitoring.models import DecisionType, MonitoringDecisionRecord

    return MonitoringDecisionRecord(
        signal_id=signal_id,
        decision=DecisionType.summarised,
        confidence=0.85,
        reasoning_summary="Test audit record",
        incident_scope_key="live:INC-001",
        tenant_id="live",
    )


class TestAuditWriterCosmosDB:
    """Tier 1: Direct Cosmos DB writes."""

    def test_write_to_cosmos_success(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        mock_cosmos = MagicMock()
        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=mock_cosmos)

        record = _make_record()
        writer.write(record)

        mock_cosmos.create_item.assert_called_once()
        assert writer.get_status() == "healthy"
        assert writer.buffer_depth == 0

    def test_write_sets_flush_source_direct(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        mock_cosmos = MagicMock()
        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=mock_cosmos)

        record = _make_record()
        writer.write(record)
        assert record.flush_source == "direct"


class TestAuditWriterMemoryBuffer:
    """Tier 2: In-memory buffer on Cosmos DB failure."""

    def test_buffer_activated_on_cosmos_failure(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        mock_cosmos = MagicMock()
        mock_cosmos.create_item.side_effect = Exception("Cosmos unavailable")
        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=mock_cosmos)

        record = _make_record()
        writer.write(record)

        assert writer.buffer_depth == 1
        assert writer.get_status() == "buffering"

    def test_buffer_without_cosmos_client(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=None)

        record = _make_record()
        writer.write(record)

        assert writer.buffer_depth == 1
        assert writer.get_status() == "buffering"

    def test_multiple_records_buffered(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=None)

        for i in range(5):
            writer.write(_make_record(f"sig-{i}"))

        assert writer.buffer_depth == 5


class TestAuditWriterFileSpill:
    """Tier 3: File spill when memory buffer is full."""

    def test_spill_to_file_when_buffer_full(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "audit-buffer.jsonl")
            config = MonitoringConfig()
            # Override config fields (frozen dataclass — create new instance)
            config_dict = {
                "audit_buffer_capacity": 3,
                "audit_buffer_file_path": file_path,
            }
            config = MonitoringConfig(
                **{
                    **{f.name: getattr(config, f.name) for f in config.__dataclass_fields__.values()},
                    **config_dict,
                }
            )

            writer = AuditWriter(config=config, cosmos_client=None)

            # Fill buffer to capacity
            for i in range(3):
                writer.write(_make_record(f"sig-buf-{i}"))
            assert writer.buffer_depth == 3

            # Next record should spill to file
            writer.write(_make_record("sig-spill"))
            assert os.path.exists(file_path)

            with open(file_path) as f:
                lines = f.readlines()
            assert len(lines) == 1

            assert writer.get_status() == "degraded"


class TestAuditWriterFlush:
    """Recovery flush: drain memory → file → Cosmos DB."""

    def test_flush_drains_memory_buffer(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        mock_cosmos = MagicMock()
        # First writes fail, then flush succeeds
        mock_cosmos.create_item.side_effect = [
            Exception("fail"),
            Exception("fail"),
            None,  # flush succeeds
            None,
        ]
        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=mock_cosmos)

        writer.write(_make_record("sig-1"))
        writer.write(_make_record("sig-2"))
        assert writer.buffer_depth == 2

        # Reset mock to succeed for flush
        mock_cosmos.create_item.side_effect = None
        flushed = writer.flush()
        assert flushed == 2
        assert writer.buffer_depth == 0
        assert writer.get_status() == "healthy"

    def test_flush_returns_zero_without_cosmos(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=None)
        writer.write(_make_record("sig-1"))
        assert writer.flush() == 0

    def test_flush_drains_file_buffer(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig
        from monitoring.models import AuditBufferEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "audit-buffer.jsonl")

            # Pre-populate a file buffer
            record = _make_record("sig-file")
            entry = AuditBufferEntry(record=record)
            with open(file_path, "w") as f:
                f.write(entry.model_dump_json() + "\n")

            config = MonitoringConfig()
            config_dict = {"audit_buffer_file_path": file_path}
            config = MonitoringConfig(
                **{
                    **{f.name: getattr(config, f.name) for f in config.__dataclass_fields__.values()},
                    **config_dict,
                }
            )

            mock_cosmos = MagicMock()
            writer = AuditWriter(config=config, cosmos_client=mock_cosmos)

            flushed = writer.flush()
            assert flushed == 1
            assert not os.path.exists(file_path)  # file removed after full flush


class TestAuditWriterStatus:
    """T017: Status reporting."""

    def test_status_healthy_when_cosmos_working(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        mock_cosmos = MagicMock()
        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=mock_cosmos)
        writer.write(_make_record())
        assert writer.get_status() == "healthy"

    def test_status_buffering_when_in_memory(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=None)
        writer.write(_make_record())
        assert writer.get_status() == "buffering"

    def test_buffer_depth_property(self) -> None:
        from monitoring.audit import AuditWriter
        from monitoring.config import MonitoringConfig

        writer = AuditWriter(config=MonitoringConfig(), cosmos_client=None)
        assert writer.buffer_depth == 0
        writer.write(_make_record())
        assert writer.buffer_depth == 1
