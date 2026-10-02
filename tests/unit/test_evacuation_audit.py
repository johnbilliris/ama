"""Tests for evacuation.audit — three-tier degradation strategy (T049)."""

import builtins
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event, Thread
from time import perf_counter

import pytest
from evacuation.audit import AuditWriter
from evacuation.config import EvacuationConfig
from evacuation.models import (
    AuditBufferEntry,
    DecisionType,
    EvacuationDecisionRecord,
    ShelterRequirements,
    ZoneDisposition,
    ZoneDispositionType,
)


def _make_record(handoff_id="hf-1", decision_type=DecisionType.handoff_received):
    return EvacuationDecisionRecord(
        handoff_id=handoff_id,
        operation_id=handoff_id,
        incident_id="inc-1",
        decision_type=decision_type,
        decision_rationale="Canonical audit decision",
        agent_version="0.1.0",
        configuration_version="config",
        incident_scope_key="tenant-a:inc-1",
        tenant_id="tenant-a",
    )


def _query_record(
    record_id,
    timestamp,
    *,
    tenant_id="tenant-a",
    incident_id="inc-1",
    decision_type=DecisionType.routes_computed,
    plan_id="ep-inc-1-v1",
):
    values = _make_record(
        handoff_id=f"operation-{record_id}",
        decision_type=decision_type,
    ).model_dump()
    values.update(
        {
            "id": record_id,
            "tenant_id": tenant_id,
            "incident_id": incident_id,
            "incident_scope_key": f"{tenant_id}:{incident_id}",
            "timestamp": timestamp,
            "plan_id": plan_id,
            "version": 1 if plan_id else None,
            "route_ids": ["route-1"],
            "routes_count": 1,
        }
    )
    return EvacuationDecisionRecord.model_validate(values).model_dump(mode="json")


class _QueryCosmos:
    def __init__(self, documents):
        self.documents = list(documents)
        self.query_calls = []

    def query_items(self, query, parameters, partition_key):
        self.query_calls.append((query, parameters, partition_key))
        values = {item["name"]: item["value"] for item in parameters}
        records = [
            document
            for document in self.documents
            if document["incident_scope_key"] == partition_key
            and document["incident_id"] == values["@incident_id"]
            and document["tenant_id"] == values["@tenant_id"]
        ]
        if "@plan_id" in values:
            records = [item for item in records if item.get("plan_id") == values["@plan_id"]]
        if "@decision_type" in values:
            records = [item for item in records if item["decision_type"] == values["@decision_type"]]
        if "@from_timestamp" in values:
            records = [item for item in records if item["timestamp"] >= values["@from_timestamp"]]
        if "@to_timestamp" in values:
            records = [item for item in records if item["timestamp"] <= values["@to_timestamp"]]
        if "@cursor_timestamp" in values:
            records = [
                item
                for item in records
                if (item["timestamp"], item["id"]) > (values["@cursor_timestamp"], values["@cursor_id"])
            ]
        return iter(sorted(records, key=lambda item: (item["timestamp"], item["id"])))


class TestCanonicalAuditEnvelope:
    @pytest.mark.parametrize(
        "overrides",
        [
            {"incident_scope_key": "tenant-b:inc-1"},
            {"incident_scope_key": "tenant-a:other"},
            {
                "plan_id": "ep-other-v1",
                "version": 1,
            },
            {
                "plan_id": "ep-inc-1-v2",
                "version": 1,
            },
        ],
    )
    def test_inconsistent_identity_is_rejected(self, overrides):
        values = _make_record().model_dump()
        values.update(overrides)

        with pytest.raises(ValueError):
            EvacuationDecisionRecord.model_validate(values)


class TestScopedAuditQuery:
    def test_combined_filters_and_time_boundaries_are_inclusive(self):
        start = datetime(2026, 1, 1, tzinfo=UTC)
        store = _QueryCosmos(
            [
                _query_record("a", start),
                _query_record("b", start + timedelta(minutes=1)),
                _query_record(
                    "c",
                    start + timedelta(minutes=1),
                    decision_type=DecisionType.transport_coordinated,
                ),
                _query_record("d", start + timedelta(minutes=2)),
            ]
        )
        writer = AuditWriter(cosmos_client=store)

        page = writer.query(
            incident_id="inc-1",
            tenant_id="tenant-a",
            plan_id="ep-inc-1-v1",
            decision_type=DecisionType.routes_computed.value,
            from_timestamp=start + timedelta(minutes=1),
            to_timestamp=start + timedelta(minutes=2),
        )

        assert [record.id for record in page.records] == ["b", "d"]
        query, _, partition_key = store.query_calls[0]
        assert "@incident_scope_key" in query
        assert partition_key == "tenant-a:inc-1"

    def test_pagination_is_stable_for_equal_timestamps(self):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        writer = AuditWriter(
            cosmos_client=_QueryCosmos([_query_record(record_id, timestamp) for record_id in ("c", "a", "b")])
        )

        first = writer.query(
            incident_id="inc-1",
            tenant_id="tenant-a",
            limit=2,
        )
        second = writer.query(
            incident_id="inc-1",
            tenant_id="tenant-a",
            limit=2,
            cursor=first.next_cursor,
        )

        assert [record.id for record in first.records] == ["a", "b"]
        assert [record.id for record in second.records] == ["c"]
        assert second.next_cursor is None

    def test_cursor_cannot_cross_tenant_or_filter_scope(self):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        writer = AuditWriter(cosmos_client=_QueryCosmos([_query_record("a", timestamp), _query_record("b", timestamp)]))
        first = writer.query(
            incident_id="inc-1",
            tenant_id="tenant-a",
            limit=1,
        )

        with pytest.raises(ValueError, match="scope or filters"):
            writer.query(
                incident_id="inc-1",
                tenant_id="tenant-b",
                limit=1,
                cursor=first.next_cursor,
            )

    def test_identical_incident_ids_are_tenant_isolated(self):
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        store = _QueryCosmos(
            [
                _query_record("a", timestamp),
                _query_record("b", timestamp, tenant_id="tenant-b"),
            ]
        )
        writer = AuditWriter(cosmos_client=store)

        page = writer.query(incident_id="inc-1", tenant_id="tenant-a")

        assert [record.id for record in page.records] == ["a"]

    def test_plan_generated_requires_canonical_domain_counts(self):
        values = _make_record().model_dump()
        values.update(
            {
                "decision_type": DecisionType.plan_generated,
                "plan_id": "ep-inc-1-v1",
                "version": 1,
                "assessment_id": "assess-1",
                "recommendation_id": "rec-1",
            }
        )

        with pytest.raises(ValueError, match="counts"):
            EvacuationDecisionRecord.model_validate(values)

    def test_replanning_trigger_vocabulary_is_closed(self):
        values = _make_record().model_dump()
        values["replanning_triggers"] = ["road closure happened"]

        with pytest.raises(ValueError):
            EvacuationDecisionRecord.model_validate(values)


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
        receipt = writer.write(_make_record())
        assert len(written) == 1
        assert written[0]["handoff_id"] == "hf-1"
        assert receipt.accepted is True
        assert receipt.storage_tier == "direct"

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
        receipt = writer.write(_make_record())
        assert writer.buffer_depth == 1
        assert receipt.accepted is True
        assert receipt.storage_tier == "memory_buffer"

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

    def test_emergency_disposition_and_receipt_survive_buffer_flush(self):
        flushed = []

        class FailThenSucceedCosmos:
            should_fail = True

            def create_item(self, body):
                if self.should_fail:
                    raise RuntimeError("Cosmos unavailable")
                flushed.append(body)

        disposition = ZoneDisposition(
            zone_id="zone-1",
            zone_number=1,
            disposition=ZoneDispositionType.emergency_escalation,
            urgency="maximum",
            affected_population=100,
            evacuating_population=0,
            remaining_population=100,
            prerequisites=["Authorized operator action required"],
            shelter_requirements=ShelterRequirements(
                building=["Use a structurally sound building"],
                supplies=["Maintain water and medication"],
                communication=["Monitor emergency services"],
            ),
            rationale="Immediate threat and no viable route",
            emergency_notification_id="emergency-hf-1-zone-1",
            emergency_notification_receipt="receipt-1",
        )
        record = EvacuationDecisionRecord(
            handoff_id="hf-1",
            operation_id="hf-1",
            incident_id="inc-1",
            decision_type=DecisionType.timeline_estimated,
            decision_rationale="Emergency disposition recorded",
            agent_version="0.1.0",
            configuration_version="config",
            incident_scope_key="tenant-a:inc-1",
            tenant_id="tenant-a",
            zone_dispositions=[disposition],
        )
        cosmos = FailThenSucceedCosmos()
        writer = AuditWriter(cosmos_client=cosmos)
        writer.write(record)
        cosmos.should_fail = False
        assert writer.flush() == 1
        restored = flushed[0]["zone_dispositions"][0]
        assert restored["disposition"] == "emergency_escalation"
        assert restored["emergency_notification_receipt"] == "receipt-1"
        assert restored["shelter_requirements"]["communication"]


class TestLossAwareRecoveryProtocol:
    @staticmethod
    def _config(tmp_path, capacity=1):
        return EvacuationConfig(
            audit_buffer_capacity=capacity,
            audit_buffer_file_path=str(tmp_path / "audit.jsonl"),
        )

    def test_disk_failure_returns_rejected_receipt(self, tmp_path, monkeypatch):
        writer = AuditWriter(config=self._config(tmp_path), cosmos_client=None)
        assert writer.write(_make_record(handoff_id="memory")).accepted
        real_open = builtins.open

        def fail_spill(path, mode="r", *args, **kwargs):
            if str(path).endswith("audit.jsonl") and "a" in mode:
                raise PermissionError("read-only volume")
            return real_open(path, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", fail_spill)

        receipt = writer.write(_make_record(handoff_id="rejected"))

        assert receipt.accepted is False
        assert receipt.durable is False
        assert receipt.storage_tier == "rejected"
        assert writer.get_status() == "degraded"

    def test_fsync_failure_returns_rejected_receipt(self, tmp_path, monkeypatch):
        writer = AuditWriter(config=self._config(tmp_path), cosmos_client=None)
        monkeypatch.setattr(
            "evacuation.audit.os.fsync",
            lambda file_descriptor: (_ for _ in ()).throw(OSError("disk full")),
        )

        receipt = writer.write(_make_record(handoff_id="disk-full"))

        assert receipt.accepted is False
        assert receipt.storage_tier == "rejected"
        assert writer.buffer_depth == 0
        assert writer.get_status() == "degraded"

    def test_metadata_is_serialized_before_direct_and_spill_writes(self, tmp_path):
        direct_documents = []

        class DirectStore:
            def create_item(self, body):
                direct_documents.append(body)

        direct = AuditWriter(
            config=self._config(tmp_path),
            cosmos_client=DirectStore(),
        )
        assert direct.write(_make_record(handoff_id="direct")).durable
        assert direct_documents[0]["flush_source"] == "direct"

        spilled = AuditWriter(
            config=self._config(tmp_path / "spill"),
            cosmos_client=None,
        )
        spilled.write(_make_record(handoff_id="memory"))
        receipt = spilled.write(_make_record(handoff_id="file"))
        entry = AuditBufferEntry.model_validate_json((tmp_path / "spill" / "audit.jsonl").read_text().splitlines()[-1])
        assert receipt.durable is True
        assert entry.record.flush_source == "file_buffer"
        assert entry.record.buffered_at == entry.buffered_at

    def test_memory_failure_prevents_newer_file_delivery(self, tmp_path):
        delivered = []

        class Store:
            def create_item(self, body):
                if body["handoff_id"] == "old-memory":
                    raise RuntimeError("503 unavailable")
                delivered.append(body["handoff_id"])

        writer = AuditWriter(config=self._config(tmp_path), cosmos_client=None)
        writer.write(_make_record(handoff_id="old-memory"))
        writer.write(_make_record(handoff_id="new-file"))
        writer._cosmos_client = Store()

        assert writer.flush() == 0
        assert delivered == []
        assert writer.buffer_depth == 1
        assert (tmp_path / "audit.jsonl").exists()

    def test_partial_file_flush_retains_failed_suffix_in_order(self, tmp_path):
        delivered = []

        class Store:
            def create_item(self, body):
                if body["handoff_id"] == "second":
                    raise RuntimeError("503 unavailable")
                delivered.append(body["handoff_id"])

        writer = AuditWriter(config=self._config(tmp_path, capacity=0), cosmos_client=None)
        for handoff_id in ("first", "second", "third"):
            assert writer.write(_make_record(handoff_id=handoff_id)).accepted
        writer._cosmos_client = Store()

        assert writer.flush() == 1
        assert delivered == ["first"]
        remaining = [
            AuditBufferEntry.model_validate_json(line).record.handoff_id
            for line in (tmp_path / "audit.jsonl").read_text().splitlines()
        ]
        assert remaining == ["second", "third"]
        assert writer.get_status() == "degraded"

    def test_lost_response_conflict_is_idempotent_only_for_same_content(self, tmp_path):
        existing = {}
        lose_response = {"value": True}

        class Store:
            def create_item(self, body):
                if body["id"] in existing:
                    raise RuntimeError("409 Conflict")
                existing[body["id"]] = dict(body)
                if lose_response["value"]:
                    raise RuntimeError("503 response lost")

            def read_item(self, item, partition_key):
                assert partition_key == existing[item]["incident_scope_key"]
                return existing[item]

        store = Store()
        writer = AuditWriter(config=self._config(tmp_path), cosmos_client=store)
        record = _make_record(handoff_id="uncertain")

        receipt = writer.write(record)
        assert receipt.accepted is True
        lose_response["value"] = False
        assert writer.flush() == 1
        assert list(existing) == [record.id]
        assert writer.get_status() == "healthy"

        conflict_writer = AuditWriter(
            config=self._config(tmp_path / "conflict"),
            cosmos_client=None,
        )
        conflicting = _make_record(handoff_id="conflicting")
        conflict_writer.write(conflicting)
        existing[conflicting.id] = {
            **conflicting.model_dump(mode="json"),
            "decision_rationale": "different content",
        }
        conflict_writer._cosmos_client = store
        assert conflict_writer.flush() == 0
        assert conflict_writer.buffer_depth == 1

    def test_restart_detects_backlog_and_preserves_old_before_new(self, tmp_path):
        config = self._config(tmp_path, capacity=0)
        first = AuditWriter(config=config, cosmos_client=None)
        first.write(_make_record(handoff_id="old"))
        delivered = []

        class Store:
            def create_item(self, body):
                delivered.append(body["handoff_id"])

        restarted = AuditWriter(config=config, cosmos_client=Store())
        assert restarted.get_status() == "degraded"
        receipt = restarted.write(_make_record(handoff_id="new"))
        assert receipt.storage_tier == "file_buffer"
        assert delivered == []

        assert restarted.flush() == 2
        assert delivered == ["old", "new"]
        assert restarted.get_status() == "healthy"
        assert not (tmp_path / "audit.jsonl").exists()

    def test_corrupt_line_stops_before_later_valid_record(self, tmp_path):
        config = self._config(tmp_path, capacity=0)
        writer = AuditWriter(config=config, cosmos_client=None)
        writer.write(_make_record(handoff_id="first"))
        path = tmp_path / "audit.jsonl"
        with path.open("a", encoding="utf-8") as file:
            file.write("{partial\n")
        writer.write(_make_record(handoff_id="third"))
        delivered = []

        class Store:
            def create_item(self, body):
                delivered.append(body["handoff_id"])

        writer._cosmos_client = Store()
        assert writer.flush() == 1
        assert delivered == ["first"]
        assert "{partial" in path.read_text()
        assert writer.get_status() == "degraded"

    def test_concurrent_append_waits_for_flush_and_is_not_deleted(self, tmp_path):
        config = self._config(tmp_path, capacity=0)
        writer = AuditWriter(config=config, cosmos_client=None)
        writer.write(_make_record(handoff_id="old"))
        started = Event()
        release = Event()
        delivered = []

        class Store:
            def create_item(self, body):
                started.set()
                release.wait(timeout=2)
                delivered.append(body["handoff_id"])

        writer._cosmos_client = Store()
        with ThreadPoolExecutor(max_workers=2) as executor:
            flush_future = executor.submit(writer.flush)
            assert started.wait(timeout=2)
            write_future = executor.submit(
                writer.write,
                _make_record(handoff_id="new"),
            )
            assert not write_future.done()
            release.set()
            assert flush_future.result(timeout=2) == 1
            receipt = write_future.result(timeout=2)

        assert receipt.storage_tier == "direct"
        assert delivered == ["old", "new"]
        assert writer.get_status() == "healthy"

    def test_capacity_one_simultaneous_writes_retain_exact_wal_order(self, tmp_path):
        config = self._config(tmp_path, capacity=1)
        writer = AuditWriter(config=config, cosmos_client=None)
        records = [
            _make_record(handoff_id="parallel-a"),
            _make_record(handoff_id="parallel-b"),
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = list(executor.map(writer.write, records))

        assert all(receipt.accepted and receipt.durable for receipt in receipts)
        entries = [
            AuditBufferEntry.model_validate_json(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()
        ]
        assert {entry.record.id for entry in entries} == {record.id for record in records}
        assert len(entries) == 2
        delivered = []

        class Store:
            def create_item(self, body):
                delivered.append(body["id"])

        writer._cosmos_client = Store()
        assert writer.flush() == 2
        assert delivered == [entry.record.id for entry in entries]
        assert writer.get_status() == "healthy"


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

    def test_buffering_when_no_primary_store_is_configured(self):
        writer = AuditWriter(cosmos_client=None)
        assert writer.get_status() == "buffering"

    def test_degraded_after_file_spill(self, tmp_path):
        small_cfg = EvacuationConfig.__new__(EvacuationConfig)
        object.__setattr__(small_cfg, "audit_buffer_capacity", 1)
        object.__setattr__(small_cfg, "audit_buffer_file_path", str(tmp_path / "spill.jsonl"))
        object.__setattr__(small_cfg, "max_summary_length", 1000)

        writer = AuditWriter(config=small_cfg, cosmos_client=None)
        writer.write(_make_record())
        writer.write(_make_record(handoff_id="hf-2"))  # Triggers file spill
        assert writer.get_status() == "degraded"

    def test_health_snapshot_does_not_wait_for_active_writer(self):
        writer = AuditWriter(cosmos_client=None)
        lock_acquired = Event()
        release = Event()

        def hold_writer_lock():
            with writer._lock:
                lock_acquired.set()
                release.wait(timeout=1)

        thread = Thread(target=hold_writer_lock)
        thread.start()
        assert lock_acquired.wait(timeout=1)

        started = perf_counter()
        assert writer.health_snapshot() == ("buffering", 0)
        elapsed = perf_counter() - started
        release.set()
        thread.join(timeout=1)

        assert elapsed < 0.05
