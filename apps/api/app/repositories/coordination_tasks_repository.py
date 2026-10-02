"""Cosmos DB repository for ``CoordinationTask`` records.

Cosmos container: ``coordination_tasks`` (provisioned by
``infra/main.bicep``). Partition key path: ``/assigned_organisation_id``.

Backends
--------
* **Cosmos** — used when ``COSMOS_ENDPOINT`` is set. List + dependency
  queries scope to the persona's organisation and are therefore
  single-partition.
* **In-memory** — used when ``COSMOS_ENDPOINT`` is unset (unit / contract
  tests, local dev without Azure). Backed by ``state_store.TASKS`` so
  legacy services that still read ``state_store.TASKS`` directly continue
  to observe the same data.

The Cosmos backend ALSO mirrors writes into ``state_store.TASKS`` so the
in-process cache stays consistent with Cosmos and the existing legacy
read paths (e.g. ``task_status_sync.py`` reading ``TASKS`` directly) keep
working without modification when Cosmos is configured.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.services import state_store
from app.services.operational_store import current_tenant_id

from packages.domain.src.domain.models.coordination_task import CoordinationTask

logger = logging.getLogger(__name__)

_DEFAULT_DATABASE = "disaster-hub"
_CONTAINER_NAME = "coordination_tasks"


def _build_container() -> Any:
    """Build a Cosmos container client from environment.

    Uses :class:`DefaultAzureCredential` so the deployed Container App
    managed identity is preferred. Returns ``None`` on any failure so the
    repository can transparently fall back to the in-memory backend.
    """
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    database = os.environ.get("COSMOS_DATABASE", _DEFAULT_DATABASE)
    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    db = client.get_database_client(database)
    return db.get_container_client(_CONTAINER_NAME)


def _to_doc(task: CoordinationTask, scope: str) -> dict[str, Any]:
    doc = task.model_dump(mode="json")
    doc["id"] = f"{scope}:{task.task_id}"
    doc["scope"] = scope
    return doc


def _from_doc(doc: dict[str, Any]) -> CoordinationTask:
    payload = {k: v for k, v in doc.items() if not k.startswith("_") and k != "id"}
    return CoordinationTask.model_validate(payload)


class CoordinationTasksRepository:
    """Hybrid Cosmos / in-memory repository for ``CoordinationTask``."""

    def __init__(self, container: Any | None = None, tenant_id: str | None = None) -> None:
        self._tenant_id = tenant_id
        if container is not None:
            self._container = container
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._container = _build_container()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "CoordinationTasksRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._container = None
        else:
            self._container = None

    @property
    def is_cosmos_backed(self) -> bool:
        return self._container is not None

    @property
    def scope(self) -> str:
        return self._tenant_id or current_tenant_id()

    def bind(self, tenant_id: str) -> CoordinationTasksRepository:
        return CoordinationTasksRepository(container=self._container, tenant_id=tenant_id)

    def _memory_tasks(self) -> dict[str, CoordinationTask]:
        return state_store.TASKS.bucket_for(self.scope)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get(self, task_id: str, organisation_id: str | None = None) -> CoordinationTask | None:
        if self._container is None:
            return self._memory_tasks().get(task_id)
        if organisation_id:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                doc = self._container.read_item(f"{self.scope}:{task_id}", partition_key=organisation_id)
                if doc.get("scope") != self.scope:
                    return None
                return _from_doc(doc)
            except CosmosResourceNotFoundError:
                return None
        docs = self._query(
            "SELECT * FROM c WHERE c.task_id = @id AND c.scope = @scope",
            [
                {"name": "@id", "value": task_id},
                {"name": "@scope", "value": self.scope},
            ],
        )
        if not docs:
            return None
        return _from_doc(docs[0])

    def list_for_persona_or_org(self, persona_id: str, organisation_id: str) -> list[CoordinationTask]:
        """Tasks where assignee == persona OR assigned-org == organisation.

        Single-partition Cosmos query when ``organisation_id`` is provided
        (the partition key path). The cross-persona OR clause means tasks
        assigned to a different persona inside the same org are visible —
        matching the existing in-memory contract in
        :class:`PersonaWorkspaceService`.
        """
        if self._container is None:
            return [
                task
                for task in self._memory_tasks().values()
                if task.assigned_persona_id == persona_id or task.assigned_organisation_id == organisation_id
            ]
        docs = self._query(
            "SELECT * FROM c WHERE c.scope = @scope "
            "AND (c.assigned_persona_id = @pid OR c.assigned_organisation_id = @oid)",
            [
                {"name": "@scope", "value": self.scope},
                {"name": "@pid", "value": persona_id},
                {"name": "@oid", "value": organisation_id},
            ],
            partition_key=organisation_id,
        )
        return [_from_doc(doc) for doc in docs]

    def list_for_organisation(self, organisation_id: str) -> list[CoordinationTask]:
        if self._container is None:
            return [task for task in self._memory_tasks().values() if task.assigned_organisation_id == organisation_id]
        docs = self._query(
            "SELECT * FROM c WHERE c.scope = @scope AND c.assigned_organisation_id = @oid",
            [
                {"name": "@scope", "value": self.scope},
                {"name": "@oid", "value": organisation_id},
            ],
            partition_key=organisation_id,
        )
        return [_from_doc(doc) for doc in docs]

    def list_dependencies(self, organisation_id: str, dependency_ids: list[str]) -> list[CoordinationTask]:
        """Resolve dependency-chain tasks scoped to a single organisation.

        Returns tasks whose ``task_id`` is in ``dependency_ids`` AND whose
        ``assigned_organisation_id == organisation_id``. The org filter is
        deliberately enforced at the data layer (matches the legacy
        in-memory contract that excludes cross-agency dependencies).
        """
        if not dependency_ids:
            return []
        if self._container is None:
            ids = set(dependency_ids)
            return [
                task
                for task in self._memory_tasks().values()
                if task.task_id in ids and task.assigned_organisation_id == organisation_id
            ]
        placeholders = ", ".join(f"@id{i}" for i in range(len(dependency_ids)))
        params: list[dict[str, object]] = [{"name": f"@id{i}", "value": tid} for i, tid in enumerate(dependency_ids)]
        params.extend(
            [
                {"name": "@oid", "value": organisation_id},
                {"name": "@scope", "value": self.scope},
            ]
        )
        docs = self._query(
            f"SELECT * FROM c WHERE c.scope = @scope "
            f"AND c.assigned_organisation_id = @oid AND c.task_id IN ({placeholders})",
            params,
            partition_key=organisation_id,
        )
        return [_from_doc(doc) for doc in docs]

    def list_dependencies_for_incident(self, incident_id: str, dependency_ids: list[str]) -> list[CoordinationTask]:
        """Resolve dependencies across organisations for a specific incident."""
        if not dependency_ids:
            return []
        if self._container is None:
            ids = set(dependency_ids)
            return [
                task
                for task in self._memory_tasks().values()
                if task.task_id in ids and task.incident_id == incident_id
            ]

        placeholders = ", ".join(f"@id{i}" for i in range(len(dependency_ids)))
        params: list[dict[str, object]] = [{"name": f"@id{i}", "value": tid} for i, tid in enumerate(dependency_ids)]
        params.extend(
            [
                {"name": "@incident", "value": incident_id},
                {"name": "@scope", "value": self.scope},
            ]
        )
        docs = self._query(
            f"SELECT * FROM c WHERE c.scope = @scope AND c.incident_id = @incident AND c.task_id IN ({placeholders})",
            params,
        )
        return [_from_doc(doc) for doc in docs]

    def list_for_persona_assignment(self, persona_id: str) -> list[CoordinationTask]:
        """Tasks where ``assigned_persona_id == persona_id`` — used by status sync.

        Cross-partition when Cosmos-backed because we don't know the org;
        small task count makes the cost negligible. In-memory mode reads
        ``state_store.TASKS`` directly.
        """
        if self._container is None:
            return [task for task in self._memory_tasks().values() if task.assigned_persona_id == persona_id]
        docs = self._query(
            "SELECT * FROM c WHERE c.scope = @scope AND c.assigned_persona_id = @pid",
            [
                {"name": "@scope", "value": self.scope},
                {"name": "@pid", "value": persona_id},
            ],
        )
        return [_from_doc(doc) for doc in docs]

    def list_all(self) -> list[CoordinationTask]:
        if self._container is None:
            return list(self._memory_tasks().values())
        docs = self._query(
            "SELECT * FROM c WHERE c.scope = @scope",
            [{"name": "@scope", "value": self.scope}],
        )
        return [_from_doc(doc) for doc in docs]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def upsert(self, task: CoordinationTask) -> CoordinationTask:
        if self._container is not None:
            self._container.upsert_item(_to_doc(task, self.scope))
        self._memory_tasks()[task.task_id] = task
        return task

    def bulk_upsert(self, tasks: list[CoordinationTask]) -> int:
        seeded = 0
        for task in tasks:
            self.upsert(task)
            seeded += 1
        return seeded

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _query(
        self,
        query: str,
        parameters: list[dict[str, object]],
        partition_key: str | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {}
        if partition_key is not None:
            kwargs["partition_key"] = partition_key
        else:
            kwargs["enable_cross_partition_query"] = True
        return list(self._container.query_items(query=query, parameters=parameters, **kwargs))


_singleton: CoordinationTasksRepository | None = None
_singleton_endpoint: str | None = None


def get_coordination_tasks_repository() -> CoordinationTasksRepository:
    """Return a process-wide repository instance.

    The cache key is the current ``COSMOS_ENDPOINT`` value, so toggling the
    env var between tests transparently rebuilds the repo. Construction is
    cheap (no eager network call) so this is safe to call frequently.
    """
    global _singleton, _singleton_endpoint
    current_endpoint = os.environ.get("COSMOS_ENDPOINT")
    if _singleton is None or _singleton_endpoint != current_endpoint:
        _singleton = CoordinationTasksRepository()
        _singleton_endpoint = current_endpoint
    return _singleton


def reset_coordination_tasks_repository() -> None:
    """Test hook to drop the cached repository instance."""
    global _singleton, _singleton_endpoint
    _singleton = None
    _singleton_endpoint = None


__all__ = [
    "CoordinationTasksRepository",
    "get_coordination_tasks_repository",
    "reset_coordination_tasks_repository",
]
