"""Append-only audit-row repository.

Default Cosmos target aligns with active IaC for this repo:
database ``ama`` and container ``audit_events`` partitioned by ``/environment``.

Provides a single-row ``append`` and a paired-row ``append_paired`` operation.
``append_paired`` uses Cosmos ``TransactionalBatch`` so that the
``admin_override`` row and the normal-outcome row land atomically — see
[Q9 paired-row rule](../../../../specs/035-webapp-capstone-closure/data-model.md)
and [R-006](../../../../specs/035-webapp-capstone-closure/research.md).

When ``COSMOS_ENDPOINT`` is unset the repository falls back to an in-memory
list so unit + contract tests run without infrastructure.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def _build_cosmos_client() -> Any:
    """Build a CosmosClient from ``COSMOS_ENDPOINT`` using DefaultAzureCredential."""
    from app.core.cosmos import create_cosmos_client as CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class AuditRepository:
    """Append-only writes to the configured Cosmos audit container.

    NN-2: rows are immutable; only ``upsert`` of a fresh ``id`` is permitted.
    The container's data plane access policy forbids replace/delete; this
    class never calls those operations.
    """

    def __init__(
        self,
        cosmos_client: Any = None,
        database_name: str | None = None,
        container_name: str | None = None,
        environment: str | None = None,
    ) -> None:
        self._db_name = database_name or os.environ.get("COSMOS_DATABASE") or "ama"
        self._container_name = container_name or os.environ.get("AMA_AUDIT_CONTAINER") or "audit_events"
        self._environment = environment or os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev"
        self._in_memory: list[dict[str, Any]] = []
        is_production = self._environment.lower() in {"production", "staging"}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                if is_production:
                    raise RuntimeError("AuditRepository failed to initialise Cosmos client") from exc
                logger.warning(
                    "AuditRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            if is_production:
                raise RuntimeError("AuditRepository requires COSMOS_ENDPOINT in production/staging")
            self._client = None

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    @staticmethod
    def _normalise_row(row: dict[str, Any], correlation_id: str, environment: str) -> dict[str, Any]:
        row = dict(row)
        row.setdefault("auditId", str(uuid.uuid4()))
        row["id"] = row["auditId"]
        row["correlationId"] = correlation_id
        row.setdefault("environment", environment)
        row.setdefault("timestamp", _now_iso())
        return row

    def _append_impl(self, row: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
        cid = correlation_id or row.get("correlationId") or str(uuid.uuid4())
        normalised = self._normalise_row(row, cid, self._environment)
        container = self._get_container()
        if container:
            container.create_item(normalised)
        else:
            self._in_memory.append(normalised)
        return normalised

    def _append_paired_impl(
        self,
        operator_row: dict[str, Any],
        target_row: dict[str, Any],
        correlation_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not correlation_id:
            raise ValueError("append_paired requires a non-empty correlation_id")

        op_norm = self._normalise_row(operator_row, correlation_id, self._environment)
        tgt_norm = self._normalise_row(target_row, correlation_id, self._environment)

        if op_norm.get("outcome") != "admin_override":
            raise ValueError("append_paired operator_row.outcome MUST be 'admin_override' (Q9 paired-row rule)")

        op_env = op_norm.get("environment")
        tgt_env = tgt_norm.get("environment")
        if op_env != tgt_env:
            raise ValueError("append_paired rows must target the same environment partition")

        container = self._get_container()
        if container:
            try:
                batch = [
                    ("create", (op_norm,)),
                    ("create", (tgt_norm,)),
                ]
                container.execute_item_batch(
                    batch_operations=batch,
                    partition_key=op_env,
                )
            except AttributeError:
                logger.warning("AuditRepository: TransactionalBatch unavailable; degrading to sequential creates")
                container.create_item(op_norm)
                container.create_item(tgt_norm)
        else:
            self._in_memory.append(op_norm)
            self._in_memory.append(tgt_norm)

        return op_norm, tgt_norm

    async def append(self, row: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
        """Append a single audit row. Returns the persisted row including ``auditId``."""
        return self._append_impl(row, correlation_id=correlation_id)

    def append_sync(self, row: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
        """Synchronous append used by mutation paths that must fail closed."""
        return self._append_impl(row, correlation_id=correlation_id)

    async def append_paired(
        self,
        operator_row: dict[str, Any],
        target_row: dict[str, Any],
        correlation_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Atomically append the ``admin_override`` operator row and the target row.

        Both rows MUST share ``correlation_id`` (same partition key) so a Cosmos
        ``TransactionalBatch`` can write them in one logical transaction
        ([R-006](../../../../specs/035-webapp-capstone-closure/research.md)).

        Returns ``(operator_row, target_row)`` after persistence.
        """
        return self._append_paired_impl(operator_row, target_row, correlation_id)

    def append_paired_sync(
        self,
        operator_row: dict[str, Any],
        target_row: dict[str, Any],
        correlation_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Synchronous paired append used by middleware and domain mutation paths."""
        return self._append_paired_impl(operator_row, target_row, correlation_id)

    @property
    def in_memory_rows(self) -> list[dict[str, Any]]:
        """Test-only view of the in-memory fallback store."""
        return list(self._in_memory)

    def fetch_for_subject(self, subject: str) -> list[dict[str, Any]]:
        """Return audit rows whose actor/subject matches ``subject``."""
        if not subject.strip():
            return []

        def _matches(row: dict[str, Any]) -> bool:
            candidates = {
                str(row.get("actor_id", "")),
                str(row.get("user_id", "")),
                str(row.get("subject", "")),
                str(row.get("sub", "")),
            }
            return subject in candidates

        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE c.environment = @environment "
                "AND (c.actor_id = @subject OR c.user_id = @subject OR c.subject = @subject OR c.sub = @subject)"
            )
            rows = list(
                container.query_items(
                    query,
                    parameters=[
                        {"name": "@environment", "value": self._environment},
                        {"name": "@subject", "value": subject},
                    ],
                    enable_cross_partition_query=True,
                )
            )
            return [dict(row) for row in rows]

        return [row for row in self._in_memory if _matches(row)]

    def fetch_window(self, start_dt: datetime, end_dt: datetime) -> list[dict[str, Any]]:
        """Return audit rows in the ISO8601 time window ``[start_dt, end_dt)``."""
        start_iso = start_dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
        end_iso = end_dt.astimezone(UTC).isoformat().replace("+00:00", "Z")

        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE c.environment = @environment AND c.timestamp >= @start AND c.timestamp < @end"
            )
            rows = list(
                container.query_items(
                    query,
                    parameters=[
                        {"name": "@environment", "value": self._environment},
                        {"name": "@start", "value": start_iso},
                        {"name": "@end", "value": end_iso},
                    ],
                    enable_cross_partition_query=True,
                )
            )
            return [dict(row) for row in rows]

        out: list[dict[str, Any]] = []
        for row in self._in_memory:
            raw_ts = str(row.get("timestamp") or "")
            if not raw_ts:
                continue
            ts_text = raw_ts[:-1] + "+00:00" if raw_ts.endswith("Z") else raw_ts
            try:
                row_dt = datetime.fromisoformat(ts_text).astimezone(UTC)
            except ValueError:
                continue
            if start_dt <= row_dt < end_dt:
                out.append(row)
        return out


_AUDIT_REPOSITORY_SINGLETON: AuditRepository | None = None


def get_audit_repository() -> AuditRepository:
    global _AUDIT_REPOSITORY_SINGLETON
    if _AUDIT_REPOSITORY_SINGLETON is None:
        _AUDIT_REPOSITORY_SINGLETON = AuditRepository()
    return _AUDIT_REPOSITORY_SINGLETON
