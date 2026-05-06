"""Append-only audit-row repository for spec-035.

Cosmos container: ``audit-events``
Partition key: ``/correlationId``

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
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class AuditRepository:
    """Append-only writes to the ``audit-events`` Cosmos container.

    NN-2: rows are immutable; only ``upsert`` of a fresh ``id`` is permitted.
    The container's data plane access policy forbids replace/delete; this
    class never calls those operations.
    """

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub") -> None:
        self._db_name = database_name
        self._container_name = "audit-events"
        self._in_memory: list[dict[str, Any]] = []

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "AuditRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            self._client = None

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    @staticmethod
    def _normalise_row(row: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        row = dict(row)
        row.setdefault("auditId", str(uuid.uuid4()))
        row["id"] = row["auditId"]
        row["correlationId"] = correlation_id
        row.setdefault("timestamp", _now_iso())
        return row

    async def append(self, row: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
        """Append a single audit row. Returns the persisted row including ``auditId``."""
        cid = correlation_id or row.get("correlationId") or str(uuid.uuid4())
        normalised = self._normalise_row(row, cid)
        container = self._get_container()
        if container:
            container.create_item(normalised)
        else:
            self._in_memory.append(normalised)
        return normalised

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
        if not correlation_id:
            raise ValueError("append_paired requires a non-empty correlation_id")

        op_norm = self._normalise_row(operator_row, correlation_id)
        tgt_norm = self._normalise_row(target_row, correlation_id)

        if op_norm.get("outcome") != "admin_override":
            raise ValueError(
                "append_paired operator_row.outcome MUST be 'admin_override' (Q9 paired-row rule)"
            )

        container = self._get_container()
        if container:
            try:
                batch = [
                    ("create", (op_norm,)),
                    ("create", (tgt_norm,)),
                ]
                container.execute_item_batch(
                    batch_operations=batch,
                    partition_key=correlation_id,
                )
            except AttributeError:
                # SDKs without execute_item_batch — fall back to two creates.
                # NN-2 is preserved (append-only); atomicity downgrades to per-row.
                logger.warning(
                    "AuditRepository: TransactionalBatch unavailable; degrading to sequential creates"
                )
                container.create_item(op_norm)
                container.create_item(tgt_norm)
        else:
            self._in_memory.append(op_norm)
            self._in_memory.append(tgt_norm)

        return op_norm, tgt_norm

    @property
    def in_memory_rows(self) -> list[dict[str, Any]]:
        """Test-only view of the in-memory fallback store."""
        return list(self._in_memory)
