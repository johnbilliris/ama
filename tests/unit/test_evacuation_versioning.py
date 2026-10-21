"""Strict tests for scoped optimistic-concurrency version reservation."""

from __future__ import annotations

import asyncio
import inspect
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from azure.core import MatchConditions
from evacuation.versioning import (
    VersionConflictError,
    VersionCounter,
    VersionReservationError,
)


class _StrictVersionStore:
    def __init__(self):
        self.documents = {}
        self.etag = 0
        self.lock = threading.Lock()
        self.conflicts_remaining = 0
        self.create_race_once = False
        self.read_error = None
        self.replace_calls = []

    def _next_etag(self):
        self.etag += 1
        return f"etag-{self.etag}"

    def create_item(self, body):
        key = (body["incident_scope_key"], body["id"])
        with self.lock:
            if self.create_race_once:
                self.create_race_once = False
                winner = deepcopy(body)
                winner["_etag"] = self._next_etag()
                self.documents[key] = winner
                raise RuntimeError("409 Conflict")
            if key in self.documents:
                raise RuntimeError("409 Conflict")
            document = deepcopy(body)
            document["_etag"] = self._next_etag()
            self.documents[key] = document
            return deepcopy(document)

    def read_item(self, item, partition_key):
        if self.read_error is not None:
            raise self.read_error
        key = (partition_key, item)
        with self.lock:
            if key not in self.documents:
                raise RuntimeError("404 NotFound")
            return deepcopy(self.documents[key])

    def replace_item(self, item, body, etag, match_condition):
        key = (body["incident_scope_key"], item)
        with self.lock:
            self.replace_calls.append((item, etag, match_condition, body["incident_scope_key"]))
            if match_condition is not MatchConditions.IfNotModified:
                raise AssertionError("SDK MatchConditions.IfNotModified is required")
            current = self.documents[key]
            if self.conflicts_remaining:
                self.conflicts_remaining -= 1
                current["_etag"] = self._next_etag()
                raise RuntimeError("412 PreconditionFailed")
            if etag != current["_etag"]:
                raise RuntimeError("412 PreconditionFailed")
            document = deepcopy(body)
            document["_etag"] = self._next_etag()
            self.documents[key] = document
            return deepcopy(document)


async def _no_sleep(_delay):
    return None


class TestLocalVersionAssignment:
    @pytest.mark.asyncio
    async def test_local_versions_increment_per_scope(self):
        counter = VersionCounter()
        assert [await counter.assign_version("inc-1", "tenant-a:inc-1") for _ in range(3)] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_identical_incident_ids_are_independent_across_tenants(self):
        counter = VersionCounter()
        assert await counter.assign_version("inc-1", "tenant-a:inc-1") == 1
        assert await counter.assign_version("inc-1", "tenant-b:inc-1") == 1

    def test_parallel_local_versions_are_unique(self):
        counter = VersionCounter()
        with ThreadPoolExecutor(max_workers=8) as pool:
            versions = list(
                pool.map(
                    lambda _: asyncio.run(counter.assign_version("inc-1", "tenant-a:inc-1")),
                    range(20),
                )
            )
        assert sorted(versions) == list(range(1, 21))


class TestFormatPlanId:
    @pytest.mark.parametrize(
        ("incident_id", "version", "expected"),
        [
            ("inc-001", 1, "ep-inc-001-v1"),
            ("abc-xyz", 42, "ep-abc-xyz-v42"),
            ("qld-fire-2025-03", 3, "ep-qld-fire-2025-03-v3"),
        ],
    )
    def test_format(self, incident_id, version, expected):
        assert VersionCounter().format_plan_id(incident_id, version) == expected


class TestVersionErrors:
    def test_conflict_and_reservation_errors_are_explicit(self):
        assert issubclass(VersionConflictError, RuntimeError)
        assert issubclass(VersionReservationError, RuntimeError)

    def test_installed_cosmos_sdk_exposes_typed_etag_contract(self):
        from azure.cosmos import ContainerProxy

        parameters = inspect.signature(ContainerProxy.replace_item).parameters
        assert "etag" in parameters
        assert "match_condition" in parameters
        assert "if_match" not in parameters


class TestCosmosReservation:
    @pytest.mark.asyncio
    async def test_bootstrap_reserves_version_one(self):
        store = _StrictVersionStore()
        counter = VersionCounter(store)
        assert await counter.assign_version("inc-1", "tenant-a:inc-1") == 1
        document = store.read_item("inc-1_plan_counter", "tenant-a:inc-1")
        assert document["current_version"] == 1

    @pytest.mark.asyncio
    async def test_existing_high_counter_is_incremented_with_sdk_etag_contract(self):
        store = _StrictVersionStore()
        store.create_item(
            {
                "id": "inc-1_plan_counter",
                "current_version": 999,
                "incident_scope_key": "tenant-a:inc-1",
            }
        )
        counter = VersionCounter(store)
        assert await counter.assign_version("inc-1", "tenant-a:inc-1") == 1000
        assert store.replace_calls[0][2] is MatchConditions.IfNotModified
        assert store.replace_calls[0][3] == "tenant-a:inc-1"

    @pytest.mark.asyncio
    async def test_stale_etag_retries_with_fresh_read(self):
        store = _StrictVersionStore()
        store.create_item(
            {
                "id": "inc-1_plan_counter",
                "current_version": 4,
                "incident_scope_key": "tenant-a:inc-1",
            }
        )
        store.conflicts_remaining = 1
        counter = VersionCounter(store, sleep=_no_sleep, jitter=lambda low, high: low)
        assert await counter.assign_version("inc-1", "tenant-a:inc-1") == 5
        assert len(store.replace_calls) == 2
        assert store.replace_calls[0][1] != store.replace_calls[1][1]

    @pytest.mark.asyncio
    async def test_first_create_race_retries_and_reserves_version_two(self):
        store = _StrictVersionStore()
        store.create_race_once = True
        counter = VersionCounter(store, sleep=_no_sleep, jitter=lambda low, high: low)
        assert await counter.assign_version("inc-1", "tenant-a:inc-1") == 2
        assert store.read_item("inc-1_plan_counter", "tenant-a:inc-1")["current_version"] == 2

    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises_without_unreserved_fallback(self):
        store = _StrictVersionStore()
        store.create_item(
            {
                "id": "inc-1_plan_counter",
                "current_version": 7,
                "incident_scope_key": "tenant-a:inc-1",
            }
        )
        store.conflicts_remaining = 3
        counter = VersionCounter(
            store,
            max_retries=3,
            sleep=_no_sleep,
            jitter=lambda low, high: low,
        )
        with pytest.raises(VersionReservationError, match="exhausted"):
            await counter.assign_version("inc-1", "tenant-a:inc-1")
        assert store.read_item("inc-1_plan_counter", "tenant-a:inc-1")["current_version"] == 7

    @pytest.mark.asyncio
    async def test_timeout_fails_without_returning_a_version(self):
        store = _StrictVersionStore()
        store.read_error = TimeoutError("Cosmos timeout")
        with pytest.raises(VersionReservationError, match="Failed to read"):
            await VersionCounter(store).assign_version("inc-1", "tenant-a:inc-1")

    @pytest.mark.parametrize(
        ("uncertain", "field"),
        [(False, "orphaned_versions"), (True, "uncertain_versions")],
    )
    def test_reserved_version_gap_is_recorded(self, uncertain, field):
        store = _StrictVersionStore()
        store.create_item(
            {
                "id": "inc-1_plan_counter",
                "current_version": 3,
                "last_reserved_version": 3,
                "orphaned_versions": [],
                "uncertain_versions": [],
                "incident_scope_key": "tenant-a:inc-1",
            }
        )
        counter = VersionCounter(store)
        counter.record_gap(
            "inc-1",
            "tenant-a:inc-1",
            3,
            uncertain=uncertain,
            reason="write outcome unavailable",
        )
        document = store.read_item("inc-1_plan_counter", "tenant-a:inc-1")
        assert document[field] == [{"version": 3, "reason": "write outcome unavailable"}]

    @pytest.mark.asyncio
    async def test_same_incident_id_is_partitioned_by_tenant(self):
        store = _StrictVersionStore()
        tenant_a = VersionCounter(store)
        tenant_b = VersionCounter(store)
        assert await tenant_a.assign_version("inc-1", "tenant-a:inc-1") == 1
        assert await tenant_b.assign_version("inc-1", "tenant-b:inc-1") == 1
        assert await tenant_a.assign_version("inc-1", "tenant-a:inc-1") == 2
        assert store.read_item("inc-1_plan_counter", "tenant-b:inc-1")["current_version"] == 1

    def test_two_independent_writers_reserve_unique_versions(self):
        store = _StrictVersionStore()
        store.create_item(
            {
                "id": "inc-1_plan_counter",
                "current_version": 0,
                "incident_scope_key": "tenant-a:inc-1",
            }
        )
        counters = [
            VersionCounter(store, sleep=_no_sleep, jitter=lambda low, high: low),
            VersionCounter(store, sleep=_no_sleep, jitter=lambda low, high: low),
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            versions = list(
                pool.map(
                    lambda counter: asyncio.run(counter.assign_version("inc-1", "tenant-a:inc-1")),
                    counters,
                )
            )
        assert sorted(versions) == [1, 2]
        assert store.read_item("inc-1_plan_counter", "tenant-a:inc-1")["current_version"] == 2
