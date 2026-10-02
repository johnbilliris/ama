"""Tests for evacuation plan lifecycle, history, expiry, and active selection."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from evacuation.repository import EvacuationPlanRepository

from tests.unit.test_evacuation_endpoints import _FakePlansStore


def _plan(version, status, *, source_plan_id=None, valid_until=None):
    plan_id = f"ep-inc-001-v{version}"
    document = deepcopy(_FakePlansStore().docs["ep-inc-001-v1"])
    document.update(
        {
            "id": plan_id,
            "plan_id": plan_id,
            "version": version,
            "status": status,
            "source_plan_id": (source_plan_id or (f"ep-inc-001-v{version - 1}" if version > 1 else None)),
            "change_summary": ("Updated evacuation plan" if version > 1 else None),
            "valid_until": valid_until,
            "created_at": f"2026-01-0{version}T00:00:00+00:00",
            "updated_at": f"2026-01-0{version}T00:00:00+00:00",
            "_etag": f"etag-v{version}",
        }
    )
    return document


class _LifecycleStore(_FakePlansStore):
    def __init__(self, documents):
        super().__init__()
        self.docs = {document["id"]: deepcopy(document) for document in documents}

    def query_items(self, query, parameters, partition_key):
        del query
        incident_id = next(parameter["value"] for parameter in parameters if parameter["name"] == "@incident_id")
        return [
            deepcopy(document)
            for document in self.docs.values()
            if document.get("incident_scope_key") == partition_key
            and document.get("incident_id") == incident_id
            and document.get("plan_id")
        ]


class TestLifecycleSelection:
    def test_approved_source_remains_authoritative_while_v2_is_proposed(self):
        repository = EvacuationPlanRepository(
            _LifecycleStore(
                [
                    _plan(1, "approved"),
                    _plan(2, "proposed", source_plan_id="ep-inc-001-v1"),
                ]
            )
        )
        authoritative = repository.authoritative_plan("inc-001", "tenant-a:inc-001")
        latest = repository.latest_active("inc-001", "tenant-a:inc-001")
        assert authoritative.plan_id == "ep-inc-001-v1"
        assert latest.plan_id == "ep-inc-001-v2"
        assert repository.active_count("inc-001", "tenant-a:inc-001") == 2

    def test_history_is_newest_first_and_includes_terminal_versions(self):
        repository = EvacuationPlanRepository(
            _LifecycleStore(
                [
                    _plan(1, "superseded"),
                    _plan(2, "rejected", source_plan_id="ep-inc-001-v1"),
                    _plan(3, "approved", source_plan_id="ep-inc-001-v2"),
                ]
            )
        )
        history = repository.list_history("inc-001", "tenant-a:inc-001")
        assert [document["version"] for document in history] == [3, 2, 1]
        assert repository.active_count("inc-001", "tenant-a:inc-001") == 1

    def test_identical_incident_and_plan_ids_are_partition_isolated(self):
        tenant_a = _plan(1, "approved")
        tenant_b = deepcopy(tenant_a)
        tenant_b.update(
            {
                "tenant_id": "tenant-b",
                "incident_scope_key": "tenant-b:inc-001",
            }
        )

        class _PartitionedStore:
            def query_items(self, query, parameters, partition_key):
                del query, parameters
                return [
                    deepcopy(document)
                    for document in (tenant_a, tenant_b)
                    if document["incident_scope_key"] == partition_key
                ]

        repository = EvacuationPlanRepository(_PartitionedStore())

        assert repository.list_history("inc-001", "tenant-a:inc-001")[0]["tenant_id"] == "tenant-a"
        assert repository.list_history("inc-001", "tenant-b:inc-001")[0]["tenant_id"] == "tenant-b"

    def test_point_read_rejects_row_from_another_scope(self):
        foreign = _plan(1, "approved")
        foreign.update(
            {
                "tenant_id": "tenant-b",
                "incident_scope_key": "tenant-b:inc-001",
            }
        )

        class _MisconfiguredStore:
            def read_item(self, item, partition_key):
                del item, partition_key
                return deepcopy(foreign)

        repository = EvacuationPlanRepository(_MisconfiguredStore())

        import pytest

        with pytest.raises(ValueError, match="requested incident scope"):
            repository.get("ep-inc-001-v1", "tenant-a:inc-001")


class TestLifecycleExpiry:
    def test_proposed_plan_expires_at_exact_boundary(self):
        boundary = datetime(2026, 1, 1, 4, tzinfo=UTC)
        store = _LifecycleStore([_plan(1, "proposed", valid_until=boundary.isoformat())])
        repository = EvacuationPlanRepository(store)
        expired = repository.expire_due(
            "inc-001",
            "tenant-a:inc-001",
            now=boundary,
        )
        assert [plan.plan_id for plan in expired] == ["ep-inc-001-v1"]
        assert store.docs["ep-inc-001-v1"]["status"] == "expired"
        assert (
            repository.active_count(
                "inc-001",
                "tenant-a:inc-001",
                now=boundary,
            )
            == 0
        )

    def test_proposed_plan_before_boundary_remains_active(self):
        boundary = datetime(2026, 1, 1, 4, tzinfo=UTC)
        repository = EvacuationPlanRepository(_LifecycleStore([_plan(1, "proposed", valid_until=boundary.isoformat())]))
        assert (
            repository.active_count(
                "inc-001",
                "tenant-a:inc-001",
                now=boundary - timedelta(microseconds=1),
            )
            == 1
        )

    def test_paused_plan_expires_but_approved_plan_does_not(self):
        boundary = datetime(2026, 1, 1, 4, tzinfo=UTC)
        store = _LifecycleStore(
            [
                _plan(1, "approved", valid_until=boundary.isoformat()),
                _plan(2, "paused", valid_until=boundary.isoformat()),
            ]
        )
        repository = EvacuationPlanRepository(store)
        expired = repository.expire_due(
            "inc-001",
            "tenant-a:inc-001",
            now=boundary,
        )
        assert [plan.plan_id for plan in expired] == ["ep-inc-001-v2"]
        assert store.docs["ep-inc-001-v1"]["status"] == "approved"
        assert (
            repository.authoritative_plan(
                "inc-001",
                "tenant-a:inc-001",
                now=boundary,
            ).plan_id
            == "ep-inc-001-v1"
        )
