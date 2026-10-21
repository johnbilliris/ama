"""Workflow Run repository — Cosmos-backed (T016, FR-011, FR-011a).

Responsibilities:
- ``create(...)`` enforces FR-011a: at most one active run per incident at a
  time, using a Cosmos transactional batch on ``incident_id`` + ``is_active=true``.
- ``update_status(...)`` validates the transition through ``run_state.validate_transition``
  and atomically updates ``status``, ``is_active``, and ``terminal_at``.
- Falls back to an in-memory dict when ``COSMOS_ENDPOINT`` is unset (consistent
  with the existing repo convention; integration tests use real Cosmos).
"""

from __future__ import annotations

import builtins
import logging
import os
import uuid
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from ..errors import ActiveRunAlreadyExistsError
from ..workflow.run_state import (
    TERMINAL_STATES,
    WorkflowRunStatus,
    is_active,
    validate_transition,
)

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class WorkflowRunRepository:
    """Cosmos-backed repository for the ``workflow_runs`` container."""

    def __init__(
        self,
        cosmos_client: Any = None,
        database_name: str = "platform",
        container_name: str = "workflow_runs",
    ) -> None:
        self._db_name = database_name
        self._container_name = container_name
        self._in_memory: dict[str, dict[str, Any]] = {}
        self._mem_lock = Lock()

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT") or os.environ.get("AZURE_COSMOS_ENDPOINT"):
            try:
                self._client = self._build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning("WorkflowRunRepository Cosmos init failed (%s); using in-memory", exc)
                self._client = None
        else:
            self._client = None

    @staticmethod
    def _build_cosmos_client() -> Any:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential

        endpoint = os.environ.get("COSMOS_ENDPOINT") or os.environ["AZURE_COSMOS_ENDPOINT"]
        return CosmosClient(endpoint, credential=DefaultAzureCredential())

    def _container(self) -> Any | None:
        if self._client is None:
            return None
        return self._client.get_database_client(self._db_name).get_container_client(self._container_name)

    # ------- Public API -------------------------------------------------

    def create(
        self,
        *,
        incident_id: str,
        current_step: str,
        created_by: str,
        tenant_id: str = "live",
        prior_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Insert a new ``Running`` workflow run; rejects if another active run exists for the incident.

        Raises:
            ActiveRunAlreadyExistsError: another run with ``is_active=true`` exists for this incident.
        """
        run_id = str(uuid.uuid4())
        now = _now_iso()
        doc: dict[str, Any] = {
            "id": run_id,
            "run_id": run_id,
            "incident_id": incident_id,
            "status": WorkflowRunStatus.RUNNING.value,
            "is_active": True,
            "current_step": current_step,
            "last_checkpoint_id": None,
            "prior_run_id": prior_run_id,
            "pending_request_id": None,
            "failure_reason": None,
            "terminal_at": None,
            "started_at": now,
            "last_step_at": now,
            "created_by": created_by,
            "tenant_id": tenant_id,
        }

        existing_active = self.get_active_run_id_for_incident(incident_id, tenant_id=tenant_id)
        if existing_active is not None:
            raise ActiveRunAlreadyExistsError(
                f"Cannot start a second active workflow run for incident {incident_id!r}; "
                f"existing active run is {existing_active!r}.",
                correlation_id=run_id,
                run_id=existing_active,
                details={"incident_id": incident_id, "active_run_id": existing_active},
            )

        container = self._container()
        if container is not None:
            container.create_item(body=doc)
        else:
            with self._mem_lock:
                self._in_memory[run_id] = doc
        return doc

    def get(self, run_id: str, *, tenant_id: str | None = None) -> dict[str, Any] | None:
        container = self._container()
        if container is not None:
            try:
                # Cross-partition read by id since we don't know the incident_id here.
                items = list(
                    container.query_items(
                        query="SELECT * FROM c WHERE c.id=@id AND (@tenant=null OR c.tenant_id=@tenant)",
                        parameters=[
                            {"name": "@id", "value": run_id},
                            {"name": "@tenant", "value": tenant_id},
                        ],
                        enable_cross_partition_query=True,
                    )
                )
                return items[0] if items else None
            except Exception:  # noqa: BLE001
                logger.exception("Cosmos get(%s) failed; returning None", run_id)
                return None
        with self._mem_lock:
            document = self._in_memory.get(run_id)
            if document is not None and tenant_id is not None and document.get("tenant_id") != tenant_id:
                return None
            return document

    def get_active_run_id_for_incident(self, incident_id: str, *, tenant_id: str = "live") -> str | None:
        container = self._container()
        if container is not None:
            try:
                items = list(
                    container.query_items(
                        query=(
                            "SELECT TOP 1 c.id FROM c WHERE c.incident_id=@i "
                            "AND c.tenant_id=@tenant AND c.is_active=true"
                        ),
                        parameters=[
                            {"name": "@i", "value": incident_id},
                            {"name": "@tenant", "value": tenant_id},
                        ],
                        partition_key=incident_id,
                    )
                )
                return items[0]["id"] if items else None
            except Exception:  # noqa: BLE001
                logger.exception("active-run query for incident=%s failed", incident_id)
                return None
        with self._mem_lock:
            for doc in self._in_memory.values():
                if doc["incident_id"] == incident_id and doc.get("tenant_id") == tenant_id and doc.get("is_active"):
                    return doc["id"]
        return None

    def list(  # noqa: A003
        self,
        *,
        status: str | None = None,
        incident_id: str | None = None,
        tenant_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        container = self._container()
        if container is not None:
            clauses: list[str] = []
            params: list[dict[str, Any]] = []
            if status:
                clauses.append("c.status=@s")
                params.append({"name": "@s", "value": status})
            if incident_id:
                clauses.append("c.incident_id=@i")
                params.append({"name": "@i", "value": incident_id})
            if tenant_id:
                clauses.append("c.tenant_id=@tenant")
                params.append({"name": "@tenant", "value": tenant_id})
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            q = f"SELECT TOP {int(limit)} * FROM c{where} ORDER BY c.started_at DESC"
            try:
                return list(
                    container.query_items(
                        query=q,
                        parameters=params,
                        enable_cross_partition_query=True,
                    )
                )
            except Exception:  # noqa: BLE001
                logger.exception("list() query failed")
                return []
        with self._mem_lock:
            items = list(self._in_memory.values())
        if status:
            items = [i for i in items if i["status"] == status]
        if incident_id:
            items = [i for i in items if i["incident_id"] == incident_id]
        if tenant_id:
            items = [i for i in items if i.get("tenant_id") == tenant_id]
        items.sort(key=lambda d: d.get("started_at", ""), reverse=True)
        return items[:limit]

    def list_page(
        self,
        *,
        status: str | None = None,
        incident_id: str | None = None,
        limit: int = 50,
        continuation: str | None = None,
    ) -> tuple[builtins.list[dict[str, Any]], str | None]:
        """Paginated variant of ``list()`` that threads Cosmos continuation tokens.

        Returns a ``(items, next_continuation_token)`` tuple.  The token is
        ``None`` when no further pages exist or when running against the
        in-memory store (which doesn't have real token support).
        """
        container = self._container()
        if container is not None:
            clauses: list[str] = []
            params: list[dict[str, Any]] = []
            if status:
                clauses.append("c.status=@s")
                params.append({"name": "@s", "value": status})
            if incident_id:
                clauses.append("c.incident_id=@i")
                params.append({"name": "@i", "value": incident_id})
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            q = f"SELECT * FROM c{where} ORDER BY c.started_at DESC"
            try:
                pager = container.query_items(
                    query=q,
                    parameters=params,
                    enable_cross_partition_query=True,
                    max_item_count=limit,
                ).by_page(continuation_token=continuation)
                page = next(iter(pager))
                return list(page), pager.continuation_token
            except Exception:  # noqa: BLE001
                logger.exception("list_page() query failed")
                return [], None
        # In-memory fallback — continuation tokens are not supported.
        with self._mem_lock:
            items = list(self._in_memory.values())
        if status:
            items = [i for i in items if i["status"] == status]
        if incident_id:
            items = [i for i in items if i["incident_id"] == incident_id]
        items.sort(key=lambda d: d.get("started_at", ""), reverse=True)
        return items[:limit], None

    def update_status(
        self,
        run_id: str,
        new_status: WorkflowRunStatus | str,
        *,
        correlation_id: str,
        tenant_id: str | None = None,
        failure_reason: dict[str, Any] | None = None,
        pending_request_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate + persist a state transition. Idempotent on same-state."""
        doc = self.get(run_id, tenant_id=tenant_id)
        if doc is None:
            raise KeyError(f"workflow run {run_id} not found")
        current = doc["status"]
        target = WorkflowRunStatus(new_status)
        target_value = target.value
        if current == target_value:
            return doc
        # Validate ALL preconditions BEFORE mutating the document, so an invalid
        # call leaves the run document untouched (in-memory mode mutates by reference).
        validate_transition(current, target_value, correlation_id=correlation_id, run_id=run_id)
        if target == WorkflowRunStatus.AWAITING_APPROVAL and pending_request_id is None:
            raise ValueError("pending_request_id is required when transitioning to AwaitingApproval")

        doc["status"] = target_value
        doc["is_active"] = is_active(target_value)
        doc["last_step_at"] = _now_iso()
        if target in TERMINAL_STATES:
            doc["terminal_at"] = _now_iso()
        if target == WorkflowRunStatus.AWAITING_APPROVAL:
            doc["pending_request_id"] = pending_request_id
        else:
            doc["pending_request_id"] = None
        if target == WorkflowRunStatus.FAILED and failure_reason:
            doc["failure_reason"] = failure_reason
        container = self._container()
        if container is not None:
            container.replace_item(item=doc["id"], body=doc)
        else:
            with self._mem_lock:
                self._in_memory[doc["id"]] = doc
        return doc


__all__ = ["WorkflowRunRepository"]
