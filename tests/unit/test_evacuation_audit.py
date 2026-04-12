"""Tests for evacuation.audit — three-tier degradation strategy (T049)."""



from evacuation.audit import AuditWriter
from evacuation.config import EvacuationConfig
from evacuation.models import DecisionType, EvacuationDecisionRecord


def _make_record(handoff_id="hf-1", decision_type=DecisionType.handoff_received):
    return EvacuationDecisionRecord(
        handoff_id=handoff_id,
        decision_type=decision_type,
    )


# ---------------------------------------------------------------------------
# Tier 1: Write to Cosmos (mock)
# ---------------------------------------------------------------------------


class TestCosmosWrite:
    def test_write_to_cosmos_success(self):
        """When Cosmos is available, records are written directly."""
        written = []

        class FakeCosmos:
            def create_item(self, body):
                written.append(body)

        writer = AuditWriter(cosmos_client=FakeCosmos())
        writer.write(_make_record())
        assert len(written) == 1
        assert written[0]["handoff_id"] == "hf-1"

    def test_tier_is_cosmos_on_success(self):
        class FakeCosmos:
            def create_item(self, body):
                pass

        writer = AuditWriter(cosmos_client=FakeCosmos())
        writer.write(_make_record())
        assert writer.get_status() == "healthy"

    def test_records_written_count(self):
        class FakeCosmos:
            def create_item(self, body):
                pass

        writer = AuditWriter(cosmos_client=FakeCosmos())
        writer.write(_make_record())
        writer.write(_make_record(handoff_id="hf-2"))
        assert writer._records_written == 2


# ---------------------------------------------------------------------------
# Tier 2: Memory buffer when Cosmos fails
# ---------------------------------------------------------------------------


class TestMemoryBuffer:
    def test_buffers_when_cosmos_fails(self):
        class FailingCosmos:
            def create_item(self, body):
                raise Exception("Cosmos unavailable")

        writer = AuditWriter(cosmos_client=FailingCosmos())
        writer.write(_make_record())
        assert writer.buffer_depth == 1
        assert writer.get_status() == "buffering"

    def test_buffers_when_no_cosmos_client(self):
        writer = AuditWriter(cosmos_client=None)
        writer.write(_make_record())
        assert writer.buffer_depth == 1

    def test_buffer_preserves_record(self):
        writer = AuditWriter(cosmos_client=None)
        writer.write(_make_record())
        entry = writer._buffer[0]
        assert entry.record.handoff_id == "hf-1"

    def test_multiple_buffered_records(self):
        writer = AuditWriter(cosmos_client=None)
        for i in range(5):
            writer.write(_make_record(handoff_id=f"hf-{i}"))
        assert writer.buffer_depth == 5


# ---------------------------------------------------------------------------
# Tier 3: File spill when memory full
# ---------------------------------------------------------------------------


class TestFileSpill:
    def test_spills_to_file_when_buffer_full(self, tmp_path):
        EvacuationConfig()
        # Use object.__new__ to bypass frozen dataclass
        small_cfg = EvacuationConfig.__new__(EvacuationConfig)
        object.__setattr__(small_cfg, "audit_buffer_capacity", 2)
        object.__setattr__(small_cfg, "audit_buffer_file_path", str(tmp_path / "spill.jsonl"))
        object.__setattr__(small_cfg, "max_summary_length", 1000)

        writer = AuditWriter(config=small_cfg, cosmos_client=None)
        writer.write(_make_record(handoff_id="hf-0"))
        writer.write(_make_record(handoff_id="hf-1"))
        # Buffer is now full (capacity=2), next should spill
        writer.write(_make_record(handoff_id="hf-2"))

        spill_file = tmp_path / "spill.jsonl"
        assert spill_file.exists()
        lines = spill_file.read_text().strip().split("\n")
        assert len(lines) >= 1

    def test_status_degraded_after_spill(self, tmp_path):
        small_cfg = EvacuationConfig.__new__(EvacuationConfig)
        object.__setattr__(small_cfg, "audit_buffer_capacity", 1)
        object.__setattr__(small_cfg, "audit_buffer_file_path", str(tmp_path / "spill.jsonl"))
        object.__setattr__(small_cfg, "max_summary_length", 1000)

        writer = AuditWriter(config=small_cfg, cosmos_client=None)
        writer.write(_make_record(handoff_id="hf-0"))
        writer.write(_make_record(handoff_id="hf-1"))

        assert writer.get_status() == "degraded"


# ---------------------------------------------------------------------------
# Flush recovery
# ---------------------------------------------------------------------------


class TestFlushRecovery:
    def test_flush_drains_memory_buffer(self):
        flushed = []

        class FailThenSucceedCosmos:
            def __init__(self):
                self.should_fail = True

            def create_item(self, body):
                if self.should_fail:
                    raise Exception("Cosmos down")
                flushed.append(body)

        cosmos = FailThenSucceedCosmos()
        writer = AuditWriter(cosmos_client=cosmos)
        writer.write(_make_record())
        writer.write(_make_record(handoff_id="hf-2"))
        assert writer.buffer_depth == 2

        # Cosmos comes back up
        cosmos.should_fail = False
        count = writer.flush()
        assert count == 2
        assert writer.buffer_depth == 0
        assert len(flushed) == 2

    def test_flush_returns_zero_without_cosmos(self):
        writer = AuditWriter(cosmos_client=None)
        writer.write(_make_record())
        assert writer.flush() == 0

    def test_flush_drains_file_buffer(self, tmp_path):
        flushed = []

        class FakeCosmos:
            def create_item(self, body):
                flushed.append(body)

        spill_file = tmp_path / "spill.jsonl"
        small_cfg = EvacuationConfig.__new__(EvacuationConfig)
        object.__setattr__(small_cfg, "audit_buffer_capacity", 1)
        object.__setattr__(small_cfg, "audit_buffer_file_path", str(spill_file))
        object.__setattr__(small_cfg, "max_summary_length", 1000)

        # Write without cosmos (buffers and spills)
        writer = AuditWriter(config=small_cfg, cosmos_client=None)
        writer.write(_make_record(handoff_id="hf-0"))
        writer.write(_make_record(handoff_id="hf-1"))  # spill

        assert spill_file.exists()

        # Now flush with cosmos
        writer._cosmos_client = FakeCosmos()
        count = writer.flush()
        assert count >= 1  # At least memory buffer flushed


# ---------------------------------------------------------------------------
# get_status() returns correct tier
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_healthy_when_cosmos_and_no_buffer(self):
        class FakeCosmos:
            def create_item(self, body):
                pass

        writer = AuditWriter(cosmos_client=FakeCosmos())
        writer.write(_make_record())
        assert writer.get_status() == "healthy"

    def test_buffering_when_buffer_has_entries(self):
        writer = AuditWriter(cosmos_client=None)
        writer.write(_make_record())
        assert writer.get_status() == "buffering"

    def test_healthy_when_empty_and_no_errors(self):
        writer = AuditWriter(cosmos_client=None)
        # No writes yet, tier is still cosmos by default
        assert writer.get_status() == "healthy"

    def test_degraded_after_file_spill(self, tmp_path):
        small_cfg = EvacuationConfig.__new__(EvacuationConfig)
        object.__setattr__(small_cfg, "audit_buffer_capacity", 1)
        object.__setattr__(small_cfg, "audit_buffer_file_path", str(tmp_path / "spill.jsonl"))
        object.__setattr__(small_cfg, "max_summary_length", 1000)

        writer = AuditWriter(config=small_cfg, cosmos_client=None)
        writer.write(_make_record())
        writer.write(_make_record(handoff_id="hf-2"))  # Triggers file spill
        assert writer.get_status() == "degraded"
