"""Unit tests for ``CoordinationTasksRepository``.

Covers both the in-memory fallback (driven by ``state_store.TASKS``) and
the Cosmos-backed branch via a stub container that records calls. The
intent is to lock in:
* read paths return a ``CoordinationTask`` model instance, not a raw dict;
* writes update both Cosmos and ``state_store.TASKS`` (cache-through);
* the singleton transparently rebuilds when ``COSMOS_ENDPOINT`` toggles.
"""

from __future__ import annotations

from typing import Any

import pytest
from app.repositories import coordination_tasks_repository as repo_module
from app.repositories.coordination_tasks_repository import (
    CoordinationTasksRepository,
    get_coordination_tasks_repository,
    reset_coordination_tasks_repository,
)
from app.services import state_store

from packages.domain.src.domain.models.coordination_task import CoordinationTask


@pytest.fixture(autouse=True)
def _reset_state() -> Any:
    state_store.reset_state()
    reset_coordination_tasks_repository()
    yield
    state_store.reset_state()
    reset_coordination_tasks_repository()


def _make(task_id: str, persona_id: str, organisation_id: str, **overrides: Any) -> CoordinationTask:
    payload = {
        "task_id": task_id,
        "incident_id": overrides.get("incident_id", "inc-test"),
        "title": overrides.get("title", f"Title for {task_id}"),
        "assigned_persona_id": persona_id,
        "assigned_organisation_id": organisation_id,
        "status": overrides.get("status", "queued"),
        "priority": overrides.get("priority", "medium"),
        "dependency_task_ids": overrides.get("dependency_task_ids", []),
    }
    return CoordinationTask.model_validate(payload)


# ---------------------------------------------------------------------------
# In-memory backend
# ---------------------------------------------------------------------------


class TestInMemoryBackend:
    def test_upsert_writes_to_state_store(self) -> None:
        repo = CoordinationTasksRepository()
        task = _make("t1", "p1", "org1")
        repo.upsert(task)
        assert state_store.TASKS["t1"] is task

    def test_get_returns_task_from_state_store(self) -> None:
        repo = CoordinationTasksRepository()
        task = _make("t1", "p1", "org1")
        state_store.TASKS["t1"] = task
        result = repo.get("t1")
        assert result is task

    def test_list_for_persona_or_org_filters_by_either(self) -> None:
        repo = CoordinationTasksRepository()
        repo.upsert(_make("t1", "p1", "org1"))
        repo.upsert(_make("t2", "p2", "org1"))
        repo.upsert(_make("t3", "p1", "org2"))
        repo.upsert(_make("t4", "p3", "org3"))
        result = {t.task_id for t in repo.list_for_persona_or_org("p1", "org1")}
        assert result == {"t1", "t2", "t3"}

    def test_list_dependencies_scopes_to_organisation(self) -> None:
        repo = CoordinationTasksRepository()
        repo.upsert(_make("t1", "p1", "org1"))
        repo.upsert(_make("t2", "p2", "org2"))  # different org
        result = {t.task_id for t in repo.list_dependencies("org1", ["t1", "t2"])}
        assert result == {"t1"}

    def test_list_dependencies_empty_when_no_ids(self) -> None:
        repo = CoordinationTasksRepository()
        repo.upsert(_make("t1", "p1", "org1"))
        assert repo.list_dependencies("org1", []) == []

    def test_list_for_persona_assignment_matches_assigned_persona_id(self) -> None:
        repo = CoordinationTasksRepository()
        repo.upsert(_make("t1", "p1", "org1"))
        repo.upsert(_make("t2", "p2", "org1"))  # same org, different persona
        result = {t.task_id for t in repo.list_for_persona_assignment("p1")}
        assert result == {"t1"}

    def test_bulk_upsert_returns_count(self) -> None:
        repo = CoordinationTasksRepository()
        count = repo.bulk_upsert([_make("t1", "p1", "org1"), _make("t2", "p1", "org1")])
        assert count == 2
        assert set(state_store.TASKS) == {"t1", "t2"}

    def test_is_cosmos_backed_is_false(self) -> None:
        repo = CoordinationTasksRepository()
        assert repo.is_cosmos_backed is False


# ---------------------------------------------------------------------------
# Cosmos backend (stubbed container)
# ---------------------------------------------------------------------------


class _StubContainer:
    """Minimal Cosmos container stub for unit tests."""

    def __init__(self) -> None:
        self.docs: dict[tuple[str, str], dict[str, Any]] = {}
        self.upserts: list[dict[str, Any]] = []

    def upsert_item(self, doc: dict[str, Any]) -> dict[str, Any]:
        self.upserts.append(doc)
        key = (doc["id"], doc["assigned_organisation_id"])
        self.docs[key] = doc
        return doc

    def read_item(self, item_id: str, partition_key: str) -> dict[str, Any]:
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        doc = self.docs.get((item_id, partition_key))
        if doc is None:
            raise CosmosResourceNotFoundError(message="missing")
        return doc

    def query_items(
        self,
        query: str,
        parameters: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        params = {p["name"]: p["value"] for p in parameters}
        rows = list(self.docs.values())
        if "@scope" in params:
            rows = [r for r in rows if r["scope"] == params["@scope"]]
        if "@oid" in params:
            rows = [r for r in rows if r["assigned_organisation_id"] == params["@oid"]]
        if "@pid" in params:
            if "OR c.assigned_organisation_id" in query:
                rows = [
                    r
                    for r in rows
                    if r["assigned_persona_id"] == params["@pid"] or r["assigned_organisation_id"] == params["@oid"]
                ]
            else:
                rows = [r for r in rows if r["assigned_persona_id"] == params["@pid"]]
        if "c.task_id IN" in query:
            id_values = {v for k, v in params.items() if k.startswith("@id")}
            rows = [r for r in rows if r["task_id"] in id_values]
        elif "c.task_id = @id" in query:
            rows = [r for r in rows if r["task_id"] == params["@id"]]
        return rows


class TestCosmosBackend:
    def test_upsert_writes_to_cosmos_and_state_store(self) -> None:
        stub = _StubContainer()
        repo = CoordinationTasksRepository(container=stub)
        task = _make("t1", "p1", "org1")
        repo.upsert(task)
        assert len(stub.upserts) == 1
        assert stub.upserts[0]["id"] == "live:t1"
        assert stub.upserts[0]["scope"] == "live"
        assert state_store.TASKS["t1"] is task

    def test_get_uses_partition_key_when_provided(self) -> None:
        stub = _StubContainer()
        repo = CoordinationTasksRepository(container=stub)
        repo.upsert(_make("t1", "p1", "org1"))
        result = repo.get("t1", "org1")
        assert result is not None
        assert result.task_id == "t1"

    def test_get_returns_none_when_missing(self) -> None:
        repo = CoordinationTasksRepository(container=_StubContainer())
        assert repo.get("missing", "org1") is None

    def test_list_for_persona_or_org_runs_single_partition_query(self) -> None:
        stub = _StubContainer()
        repo = CoordinationTasksRepository(container=stub)
        repo.upsert(_make("t1", "p1", "org1"))
        repo.upsert(_make("t2", "p2", "org1"))
        repo.upsert(_make("t3", "p1", "org2"))
        result = {t.task_id for t in repo.list_for_persona_or_org("p1", "org1")}
        assert result == {"t1", "t2"}

    def test_list_dependencies_filters_by_org_and_ids(self) -> None:
        stub = _StubContainer()
        repo = CoordinationTasksRepository(container=stub)
        repo.upsert(_make("t1", "p1", "org1"))
        repo.upsert(_make("t2", "p2", "org1"))
        repo.upsert(_make("t3", "p3", "org2"))
        result = {t.task_id for t in repo.list_dependencies("org1", ["t1", "t2", "t3"])}
        assert result == {"t1", "t2"}

    def test_is_cosmos_backed_is_true(self) -> None:
        repo = CoordinationTasksRepository(container=_StubContainer())
        assert repo.is_cosmos_backed is True

    def test_same_task_id_is_isolated_by_tenant_scope(self) -> None:
        stub = _StubContainer()
        live_repo = CoordinationTasksRepository(container=stub, tenant_id="live")
        sim_repo = CoordinationTasksRepository(container=stub, tenant_id="sim-drill")

        live_repo.upsert(_make("t1", "p1", "org1", title="Live task"))
        sim_repo.upsert(_make("t1", "p1", "org1", title="Simulation task"))

        assert live_repo.get("t1", "org1").title == "Live task"
        assert sim_repo.get("t1", "org1").title == "Simulation task"
        assert {doc["id"] for doc in stub.upserts} == {"live:t1", "sim-drill:t1"}


# ---------------------------------------------------------------------------
# Singleton cache invalidation on COSMOS_ENDPOINT toggle
# ---------------------------------------------------------------------------


class TestSingletonCache:
    def test_singleton_rebuilds_when_endpoint_changes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
        repo_a = get_coordination_tasks_repository()
        assert repo_a.is_cosmos_backed is False

        monkeypatch.setenv("COSMOS_ENDPOINT", "https://stub.example.invalid/")
        # patch _build_container so we don't try to open a real connection
        monkeypatch.setattr(repo_module, "_build_container", lambda: _StubContainer())
        repo_b = get_coordination_tasks_repository()
        assert repo_b is not repo_a
        assert repo_b.is_cosmos_backed is True

        monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
        repo_c = get_coordination_tasks_repository()
        assert repo_c is not repo_b
        assert repo_c.is_cosmos_backed is False
