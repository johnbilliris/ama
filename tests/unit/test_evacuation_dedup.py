"""Tests for evacuation.dedup scoped local and durable claims (T016)."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import Lock

import pytest
from evacuation.dedup import (
    HandoffClaimInProgressError,
    HandoffClaimStoreError,
    HandoffDeduplicator,
)


def _complete_plan_document() -> dict:
    area = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
    }
    return {
        "id": "ep-inc-1-v1",
        "plan_id": "ep-inc-1-v1",
        "incident_id": "inc-1",
        "tenant_id": "tenant-a",
        "incident_scope_key": "tenant-a:inc-1",
        "simulation": True,
        "population_estimate": 0,
        "total_population": 0,
        "affected_area": area,
        "hazard_summary": {
            "hazard_type": "flood",
            "hazard_types": ["flood"],
            "severity_level": "high",
            "time_horizon": "4h",
            "source_assessment_id": "assess-1",
            "affected_area": area,
            "sources": [
                {
                    "assessment_id": "assess-1",
                    "hazard_type": "flood",
                    "severity_level": "high",
                    "affected_area": area,
                    "generated_at": "2026-01-01T00:00:00+00:00",
                    "buffer_radius_metres": 2_000,
                    "geometry_sha256": "a" * 64,
                }
            ],
        },
        "zones": [{"zone_id": "1", "zone_number": 1}],
        "phases": [{"phase_number": 1, "zone_ids": ["1"]}],
        "zone_dispositions": [
            {
                "zone_id": "1",
                "zone_number": 1,
                "disposition": "shelter_in_place",
                "urgency": "immediate",
                "affected_population": 0,
                "evacuating_population": 0,
                "remaining_population": 0,
                "rationale": "No movement required",
            }
        ],
        "traceability": {
            "source_handoff_id": "hf-1",
            "risk_assessment_id": "assess-1",
            "risk_assessment_ids": ["assess-1"],
            "recommendation_id": "rec-1",
            "input_data_versions": {"config": "config"},
            "generation_method": "template_fallback",
        },
        "data_snapshot": {
            "road_network_version": "road",
            "population_data_version": "population",
            "facility_data_version": "facility",
            "assembly_area_data_version": "assembly",
            "hazard_assessment_ids": ["assess-1"],
            "hazard_geometry_algorithm": "per-hazard-aeqd-level-union-v1",
        },
        "summary": "Recovered plan",
        "assumptions": [],
        "generation_method": "template_fallback",
        "configuration_version": "config",
    }


# ---------------------------------------------------------------------------
# Basic duplicate detection
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    def test_first_seen_returns_false(self):
        d = HandoffDeduplicator(window_minutes=10)
        assert d.is_duplicate("hf-1") is False

    def test_second_seen_returns_true(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")
        assert d.is_duplicate("hf-1") is True

    def test_different_ids_not_duplicate(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")
        assert d.is_duplicate("hf-2") is False

    def test_size_grows(self):
        d = HandoffDeduplicator(window_minutes=10)
        assert d.size == 0
        d.is_duplicate("hf-1")
        assert d.size == 1
        d.is_duplicate("hf-2")
        assert d.size == 2

    def test_duplicate_does_not_increase_size(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")
        d.is_duplicate("hf-1")
        assert d.size == 1


# ---------------------------------------------------------------------------
# TTL expiry
# ---------------------------------------------------------------------------


class TestTTLExpiry:
    def test_entry_expires_after_window(self):
        clock = [100.0]
        d = HandoffDeduplicator(window_minutes=1, monotonic=lambda: clock[0])
        d.is_duplicate("hf-1")
        clock[0] += 61
        assert d.is_duplicate("hf-1") is False

    def test_entry_not_expired_within_window(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-1")

        # Still within window
        assert d.is_duplicate("hf-1") is True

    def test_expired_entries_evicted(self):
        clock = [100.0]
        d = HandoffDeduplicator(window_minutes=1, monotonic=lambda: clock[0])
        d.is_duplicate("hf-1")
        d.is_duplicate("hf-2")
        assert d.size == 2
        clock[0] += 61
        d.is_duplicate("hf-3")
        assert d.size == 1


# ---------------------------------------------------------------------------
# Max size / LRU eviction
# ---------------------------------------------------------------------------


class TestMaxSizeEviction:
    def test_max_size_enforced(self):
        d = HandoffDeduplicator(window_minutes=10, max_size=5)
        for i in range(10):
            d.is_duplicate(f"hf-{i}")
        assert d.size == 5

    def test_oldest_evicted_first(self):
        d = HandoffDeduplicator(window_minutes=10, max_size=3)
        d.is_duplicate("hf-1")
        d.is_duplicate("hf-2")
        d.is_duplicate("hf-3")
        d.is_duplicate("hf-4")  # hf-1 should be evicted

        assert d.is_duplicate("hf-1") is False  # Re-added as new
        assert d.is_duplicate("hf-4") is True  # Still present


# ---------------------------------------------------------------------------
# Empty cache
# ---------------------------------------------------------------------------


class TestEmptyCache:
    def test_empty_cache_size(self):
        d = HandoffDeduplicator()
        assert d.size == 0

    def test_empty_cache_not_duplicate(self):
        d = HandoffDeduplicator()
        assert d.is_duplicate("anything") is False


# ---------------------------------------------------------------------------
# Concurrent and scoped access
# ---------------------------------------------------------------------------


class TestConcurrentAccess:
    def test_parallel_access_has_one_winner(self):
        d = HandoffDeduplicator(window_minutes=10)
        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(lambda _: d.is_duplicate("hf-same"), range(100)))
        assert results.count(False) == 1
        assert results.count(True) == 99

    def test_interleaved_ids(self):
        d = HandoffDeduplicator(window_minutes=10)
        for i in range(50):
            d.is_duplicate(f"hf-{i % 10}")
        # All 10 unique IDs should be present
        assert d.size == 10

    def test_same_handoff_id_is_independent_across_tenants(self):
        d = HandoffDeduplicator(window_minutes=10)
        assert d.is_duplicate("hf-shared", tenant_id="tenant-a", incident_id="inc-1") is False
        assert d.is_duplicate("hf-shared", tenant_id="tenant-b", incident_id="inc-1") is False
        assert d.is_duplicate("hf-shared", tenant_id="tenant-a", incident_id="inc-1") is True

    def test_retryable_release_is_scoped(self):
        d = HandoffDeduplicator(window_minutes=10)
        d.is_duplicate("hf-shared", tenant_id="tenant-a", incident_id="inc-1")
        d.is_duplicate("hf-shared", tenant_id="tenant-b", incident_id="inc-1")
        d.release("hf-shared", tenant_id="tenant-a", incident_id="inc-1")
        assert d.is_duplicate("hf-shared", tenant_id="tenant-a", incident_id="inc-1") is False
        assert d.is_duplicate("hf-shared", tenant_id="tenant-b", incident_id="inc-1") is True


class _DurableClaimStore:
    def __init__(self):
        self.documents = {}
        self._etag = 0
        self._lock = Lock()

    def _next_etag(self):
        self._etag += 1
        return f"etag-{self._etag}"

    def create_item(self, body):
        key = (body["incident_scope_key"], body["id"])
        with self._lock:
            if key in self.documents:
                raise RuntimeError("409 Conflict")
            document = deepcopy(body)
            document["_etag"] = self._next_etag()
            self.documents[key] = document
            return deepcopy(document)

    def read_item(self, item, partition_key):
        key = (partition_key, item)
        with self._lock:
            if key not in self.documents:
                raise RuntimeError("404 NotFound")
            return deepcopy(self.documents[key])

    def replace_item(self, item, body, etag, match_condition):
        del match_condition
        key = (body["incident_scope_key"], item)
        with self._lock:
            current = self.documents[key]
            if current["_etag"] != etag:
                raise RuntimeError("412 PreconditionFailed")
            document = deepcopy(body)
            document["_etag"] = self._next_etag()
            self.documents[key] = document
            return deepcopy(document)

    def execute_item_batch(self, batch_operations, partition_key):
        with self._lock:
            next_documents = deepcopy(self.documents)
            for operation in batch_operations:
                operation_type, args = operation[:2]
                options = operation[2] if len(operation) == 3 else {}
                if operation_type == "create":
                    body = deepcopy(args[0])
                    key = (partition_key, body["id"])
                    if key in next_documents:
                        raise RuntimeError("409 Conflict")
                    body["_etag"] = self._next_etag()
                    next_documents[key] = body
                    continue
                item, body = args
                key = (partition_key, item)
                current = next_documents[key]
                if options.get("if_match_etag") != current.get("_etag"):
                    raise RuntimeError("412 PreconditionFailed")
                replacement = deepcopy(body)
                replacement["_etag"] = self._next_etag()
                next_documents[key] = replacement
            self.documents = next_documents
            return []


class TestDurableClaims:
    def test_two_replicas_have_one_concurrent_winner(self):
        store = _DurableClaimStore()
        workers = [
            HandoffDeduplicator(cosmos_container=store),
            HandoffDeduplicator(cosmos_container=store),
        ]

        def claim(worker):
            try:
                return worker.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1").acquired
            except HandoffClaimInProgressError:
                return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(claim, workers))
        assert results.count(True) == 1
        assert results.count(False) == 1
        claims = [document for document in store.documents.values() if document["id"].startswith("handoff-claim-")]
        assert len(claims) == 1

    def test_losing_replica_cannot_release_winner_claim(self):
        store = _DurableClaimStore()
        winner = HandoffDeduplicator(cosmos_container=store, owner_id="winner")
        loser = HandoffDeduplicator(cosmos_container=store, owner_id="loser")
        winner.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        with pytest.raises(HandoffClaimInProgressError):
            loser.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        loser.release(
            "hf-1",
            tenant_id="tenant-a",
            incident_id="inc-1",
            incident_scope_key="tenant-a:inc-1",
        )
        claim = next(document for document in store.documents.values() if document["id"].startswith("handoff-claim-"))
        assert claim["status"] == "processing"
        assert claim["owner_id"] == "winner"

    def test_same_handoff_is_independent_across_tenants(self):
        store = _DurableClaimStore()
        worker = HandoffDeduplicator(cosmos_container=store)
        first = worker.try_claim("tenant-a", "inc-1", "hf-shared", "tenant-a:inc-1")
        second = worker.try_claim("tenant-b", "inc-1", "hf-shared", "tenant-b:inc-1")
        assert first.acquired and second.acquired
        assert {partition for partition, _ in store.documents} == {
            "tenant-a:inc-1",
            "tenant-b:inc-1",
        }

    def test_completed_claim_returns_original_plan(self):
        store = _DurableClaimStore()
        worker = HandoffDeduplicator(cosmos_container=store)
        worker.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        worker.assign_plan_id("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1", "ep-inc-1-v1")
        store.create_item(
            {
                "id": "ep-inc-1-v1",
                "plan_id": "ep-inc-1-v1",
                "incident_id": "inc-1",
                "tenant_id": "tenant-a",
                "incident_scope_key": "tenant-a:inc-1",
                "simulation": True,
                "population_estimate": 0,
                "total_population": 0,
                "affected_area": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                },
                "hazard_summary": {
                    "hazard_type": "flood",
                    "hazard_types": ["flood"],
                    "severity_level": "high",
                    "time_horizon": "4h",
                    "source_assessment_id": "assess-1",
                    "affected_area": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                    },
                    "sources": [
                        {
                            "assessment_id": "assess-1",
                            "hazard_type": "flood",
                            "severity_level": "high",
                            "affected_area": {
                                "type": "Polygon",
                                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                            },
                            "generated_at": "2026-01-01T00:00:00+00:00",
                            "buffer_radius_metres": 2_000,
                            "geometry_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        }
                    ],
                },
                "zones": [{"zone_id": "1", "zone_number": 1}],
                "phases": [{"phase_number": 1, "zone_ids": ["1"]}],
                "zone_dispositions": [
                    {
                        "zone_id": "1",
                        "zone_number": 1,
                        "disposition": "shelter_in_place",
                        "urgency": "immediate",
                        "affected_population": 0,
                        "evacuating_population": 0,
                        "remaining_population": 0,
                        "rationale": "No movement required",
                    }
                ],
                "traceability": {
                    "source_handoff_id": "hf-1",
                    "risk_assessment_id": "assess-1",
                    "risk_assessment_ids": ["assess-1"],
                    "recommendation_id": "rec-1",
                    "input_data_versions": {"config": "config"},
                    "generation_method": "template_fallback",
                },
                "data_snapshot": {
                    "road_network_version": "road",
                    "population_data_version": "population",
                    "facility_data_version": "facility",
                    "assembly_area_data_version": "assembly",
                    "hazard_assessment_ids": ["assess-1"],
                    "hazard_geometry_algorithm": "per-hazard-aeqd-level-union-v1",
                },
                "summary": "Recovered plan",
                "assumptions": [],
                "generation_method": "template_fallback",
                "configuration_version": "config",
            }
        )
        worker.complete("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1", "ep-inc-1-v1")
        replay = HandoffDeduplicator(cosmos_container=store).try_claim(
            "tenant-a",
            "inc-1",
            "hf-1",
            "tenant-a:inc-1",
        )
        assert replay.completed is True
        assert replay.plan_id == "ep-inc-1-v1"

    def test_existing_plan_recovers_lost_claim_completion(self):
        store = _DurableClaimStore()
        first = HandoffDeduplicator(cosmos_container=store)
        first.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        first.assign_plan_id("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1", "ep-inc-1-v1")
        store.create_item(_complete_plan_document())
        replay = HandoffDeduplicator(cosmos_container=store).try_claim(
            "tenant-a",
            "inc-1",
            "hf-1",
            "tenant-a:inc-1",
        )
        assert replay.completed is True
        assert replay.plan_id == "ep-inc-1-v1"
        claims = [document for document in store.documents.values() if document["id"].startswith("handoff-claim-")]
        assert claims[0]["status"] == "completed"

    def test_malformed_linked_plan_is_not_accepted_as_completed(self):
        store = _DurableClaimStore()
        first = HandoffDeduplicator(cosmos_container=store)
        first.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        first.assign_plan_id("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1", "ep-inc-1-v1")
        store.create_item(
            {
                "id": "ep-inc-1-v1",
                "plan_id": "ep-inc-1-v1",
                "incident_scope_key": "tenant-a:inc-1",
            }
        )
        with pytest.raises(HandoffClaimStoreError, match="invalid"):
            HandoffDeduplicator(cosmos_container=store).try_claim(
                "tenant-a",
                "inc-1",
                "hf-1",
                "tenant-a:inc-1",
            )

    def test_abandoned_claim_can_be_reclaimed(self):
        store = _DurableClaimStore()
        first = HandoffDeduplicator(cosmos_container=store)
        first.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        first.release(
            "hf-1",
            tenant_id="tenant-a",
            incident_id="inc-1",
            incident_scope_key="tenant-a:inc-1",
        )
        replay = HandoffDeduplicator(cosmos_container=store).try_claim(
            "tenant-a",
            "inc-1",
            "hf-1",
            "tenant-a:inc-1",
        )
        assert replay.acquired is True

    def test_stale_processing_lease_can_be_taken_over(self):
        store = _DurableClaimStore()
        clock = [datetime(2026, 1, 1, tzinfo=UTC)]
        first = HandoffDeduplicator(cosmos_container=store, lease_seconds=30, now=lambda: clock[0])
        first.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        clock[0] += timedelta(seconds=31)
        replay = HandoffDeduplicator(
            cosmos_container=store,
            lease_seconds=30,
            now=lambda: clock[0],
        ).try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        assert replay.acquired is True

    def test_rejected_claim_is_a_durable_duplicate_outcome(self):
        store = _DurableClaimStore()
        worker = HandoffDeduplicator(cosmos_container=store)
        worker.try_claim("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1")
        worker.reject("tenant-a", "inc-1", "hf-1", "tenant-a:inc-1", "invalid reference")
        replay = HandoffDeduplicator(cosmos_container=store).try_claim(
            "tenant-a",
            "inc-1",
            "hf-1",
            "tenant-a:inc-1",
        )
        assert replay.rejected is True
        assert replay.acquired is False
