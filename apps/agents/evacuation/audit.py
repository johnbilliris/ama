"""Audit writer with three-tier degradation strategy (matching monitoring agent pattern).

Tier 1: Cosmos DB (primary) — append-only writes
Tier 2: WAL-backed in-memory cache (bounded at AUDIT_BUFFER_CAPACITY, default 10K)
Tier 3: WAL-only overflow after the memory cache is full

Every buffered acceptance is fsynced to one synchronized local JSONL write-ahead
log. Recovery drains that single chronological source of truth and annotates each
record with ``buffered_at`` and ``flush_source`` before serialization.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import tempfile
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path
from threading import RLock
from typing import Any, Protocol
from uuid import uuid4

from evacuation.config import EvacuationConfig
from evacuation.models import (
    AuditBufferEntry,
    DecisionType,
    EvacuationDecisionRecord,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuditWriteReceipt:
    """Observation that an append was accepted by one audit storage tier."""

    record_id: str
    accepted: bool
    storage_tier: str
    durable: bool


@dataclass(frozen=True)
class AuditQueryPage:
    """Stable chronological page of validated audit records."""

    records: list[EvacuationDecisionRecord]
    next_cursor: str | None


class AuditCosmosContainer(Protocol):
    def create_item(self, *, body: dict[str, object]) -> object: ...

    def read_item(self, *, item: str, partition_key: str) -> dict[str, object]: ...

    def query_items(
        self,
        *,
        query: str,
        parameters: list[dict[str, Any]],
        partition_key: str,
    ) -> Iterable[dict[str, object]]: ...


class AuditWriter:
    """Append-only audit trail with three-tier degradation."""

    def __init__(
        self,
        config: EvacuationConfig | None = None,
        cosmos_client: AuditCosmosContainer | None = None,
    ) -> None:
        self._config = config or EvacuationConfig()
        self._cosmos_client = cosmos_client
        self._buffer: deque[AuditBufferEntry] = deque()
        configured_path = self._config.audit_buffer_file_path
        default_path = "/app/var/evacuation-agent/audit-buffer.jsonl"
        if (
            getattr(self._config, "environment", "development") in {"development", "test"}
            and configured_path == default_path
            and "AUDIT_BUFFER_FILE_PATH" not in os.environ
        ):
            configured_path = str(Path(tempfile.gettempdir()) / "ama-evacuation-audit" / f"{uuid4().hex}.jsonl")
        self._file_path = configured_path
        self._lock = RLock()
        self._records_written: int = 0
        self._file_spill_count: int = 0
        self._last_rejection: str = ""
        self._spill_corrupt = False
        self._cached_status = "buffering" if cosmos_client is None else "healthy"
        self._cached_buffer_depth = 0
        if self._has_file_backlog_locked():
            self._rebuild_pending_state_locked()
        self._refresh_health_cache_locked()

    def write(self, record: EvacuationDecisionRecord) -> AuditWriteReceipt:
        """Write an audit record. Falls through tiers on failure."""
        with self._lock:
            max_len = self._config.max_summary_length
            if len(record.decision_rationale) > max_len:
                record.decision_rationale = record.decision_rationale[:max_len]

            pending = self._has_file_backlog_locked()
            if self._cosmos_client is not None and not pending:
                record.flush_source = "direct"
                if self._deliver_to_cosmos(record):
                    self._records_written += 1
                    self._refresh_health_cache_locked()
                    return AuditWriteReceipt(record.id, True, "direct", True)
                logger.warning("Cosmos DB write unconfirmed, falling back to audit buffer")

            storage_tier = (
                "memory_buffer"
                if self._file_spill_count == 0 and len(self._buffer) < self._config.audit_buffer_capacity
                else "file_buffer"
            )
            accepted = self._append_to_wal(record, storage_tier)
            if not accepted:
                self._last_rejection = record.id
            self._refresh_health_cache_locked()
            return AuditWriteReceipt(
                record.id,
                accepted,
                storage_tier if accepted else "rejected",
                accepted,
            )

    def _write_to_cosmos(self, record: EvacuationDecisionRecord) -> None:
        """Write a single record to Cosmos DB (append-only)."""
        if self._cosmos_client is None:
            raise RuntimeError("Cosmos DB client is not configured")
        container = self._cosmos_client
        doc = record.model_dump(mode="json")
        doc["id"] = str(doc["id"])
        container.create_item(body=doc)

    def _deliver_to_cosmos(self, record: EvacuationDecisionRecord) -> bool:
        try:
            self._write_to_cosmos(record)
            return True
        except Exception as exc:
            if not self._is_conflict(exc):
                return False
            if self._cosmos_client is None or not hasattr(
                self._cosmos_client,
                "read_item",
            ):
                return False
            try:
                existing = self._cosmos_client.read_item(
                    item=record.id,
                    partition_key=record.incident_scope_key,
                )
                existing_record = EvacuationDecisionRecord.model_validate(existing)
            except Exception:
                return False
            return self._canonical_record_content(existing_record) == self._canonical_record_content(record)

    @staticmethod
    def _canonical_record_content(
        record: EvacuationDecisionRecord,
    ) -> dict[str, Any]:
        content = record.model_dump(mode="json")
        content.pop("buffered_at", None)
        content.pop("flush_source", None)
        return content

    @staticmethod
    def _is_conflict(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None) or getattr(
            exc,
            "http_status",
            None,
        )
        return status == 409 or "409" in str(exc) or "Conflict" in str(exc)

    def _append_to_wal(
        self,
        record: EvacuationDecisionRecord,
        storage_tier: str,
    ) -> bool:
        """Fsync one pending record before exposing an accepted receipt."""
        entry = AuditBufferEntry(
            record=record,
            buffered_at=datetime.now(UTC),
        )
        entry.record.buffered_at = entry.buffered_at
        entry.record.flush_source = storage_tier
        try:
            path = Path(self._file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8", newline="\n") as file:
                file.write(entry.model_dump_json() + "\n")
                file.flush()
                os.fsync(file.fileno())
            if storage_tier == "memory_buffer":
                self._buffer.append(entry)
                if len(self._buffer) == 1:
                    logger.warning("Audit buffer activated — Cosmos DB unavailable")
            else:
                self._file_spill_count += 1
                logger.critical(
                    "Audit record spilled beyond memory cache (%d entries), file: %s",
                    len(self._buffer),
                    self._file_path,
                )
            return True
        except Exception:
            logger.critical(
                "AUDIT RECORD LOSS RISK — failed to spill to file: %s",
                self._file_path,
                exc_info=True,
            )
            return False

    def flush(self) -> int:
        """Flush buffered records to Cosmos DB. Returns count of records flushed."""
        with self._lock:
            if self._cosmos_client is None:
                return 0

            flushed = 0
            file_path = Path(self._file_path)
            if not file_path.exists():
                if self._buffer:
                    self._last_rejection = "wal_missing"
                return 0
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                logger.warning("Failed to read audit WAL", exc_info=True)
                return 0

            remaining: list[str] = []
            self._spill_corrupt = False
            for index, raw_line in enumerate(lines):
                if not raw_line.strip():
                    continue
                try:
                    entry = AuditBufferEntry.model_validate_json(raw_line)
                except Exception:
                    self._spill_corrupt = True
                    remaining = lines[index:]
                    logger.error(
                        "Audit WAL is corrupt at line %d; recovery stopped",
                        index + 1,
                    )
                    break
                entry.retry_count += 1
                entry.last_retry_at = datetime.now(UTC)
                if not self._deliver_to_cosmos(entry.record):
                    remaining = [
                        entry.model_dump_json(),
                        *lines[index + 1 :],
                    ]
                    logger.warning("Flush failed for oldest buffered record; newer records were not attempted")
                    break
                self._records_written += 1
                flushed += 1
            self._rewrite_spill(remaining)
            self._rebuild_pending_state_locked(remaining)

            if not self._has_file_backlog_locked() and not self._buffer:
                self._file_spill_count = 0
                self._spill_corrupt = False
            if flushed > 0:
                logger.info("Flushed %d audit records to Cosmos DB", flushed)
            self._refresh_health_cache_locked()
            return flushed

    def _rewrite_spill(self, lines: list[str]) -> None:
        path = Path(self._file_path)
        if not lines:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        with open(temporary, "w", encoding="utf-8", newline="\n") as file:
            for line in lines:
                file.write(line.rstrip("\n") + "\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)

    def _has_file_backlog_locked(self) -> bool:
        path = Path(self._file_path)
        try:
            return path.is_file() and path.stat().st_size > 0
        except OSError:
            return True

    def _rebuild_pending_state_locked(
        self,
        lines: list[str] | None = None,
    ) -> None:
        self._buffer.clear()
        self._file_spill_count = 0
        if lines is None:
            try:
                lines = Path(self._file_path).read_text(encoding="utf-8").splitlines()
            except OSError:
                self._spill_corrupt = True
                return
        for raw_line in lines:
            if not raw_line.strip():
                continue
            try:
                entry = AuditBufferEntry.model_validate_json(raw_line)
            except Exception:
                self._spill_corrupt = True
                return
            if (
                entry.record.flush_source == "memory_buffer"
                and len(self._buffer) < self._config.audit_buffer_capacity
                and self._file_spill_count == 0
            ):
                self._buffer.append(entry)
            else:
                self._file_spill_count += 1

    def get_status(self) -> str:
        """Return current audit tier: 'healthy' | 'buffering' | 'degraded'."""
        with self._lock:
            self._refresh_health_cache_locked()
            return self._cached_status

    def health_snapshot(self) -> tuple[str, int]:
        """Return audit status without waiting for an active append/flush."""
        if not self._lock.acquire(blocking=False):
            return self._cached_status, self._cached_buffer_depth
        try:
            self._refresh_health_cache_locked()
            return self._cached_status, self._cached_buffer_depth
        finally:
            self._lock.release()

    def _refresh_health_cache_locked(self) -> None:
        self._cached_buffer_depth = len(self._buffer)
        if self._last_rejection or self._spill_corrupt:
            self._cached_status = "degraded"
        elif self._file_spill_count > 0:
            self._cached_status = "degraded"
        elif self._buffer or self._has_file_backlog_locked() or self._cosmos_client is None:
            self._cached_status = "buffering"
        else:
            self._cached_status = "healthy"

    def query(
        self,
        *,
        incident_id: str,
        tenant_id: str,
        plan_id: str | None = None,
        decision_type: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> AuditQueryPage:
        """Query one incident partition with optional combined filters."""
        if self._cosmos_client is None:
            raise RuntimeError("Audit store is unavailable")
        if not incident_id.strip() or not tenant_id.strip():
            raise ValueError("incident_id and tenant_id are required")
        if decision_type is not None:
            DecisionType(decision_type)
        if plan_id is not None:
            prefix = f"ep-{incident_id}-v"
            if not plan_id.startswith(prefix) or not plan_id[len(prefix) :].isdigit():
                raise ValueError("plan_id does not belong to the queried incident")
        if not 1 <= limit <= 100:
            raise ValueError("audit query limit must be in 1..100")
        for value in (from_timestamp, to_timestamp):
            if value is not None and value.tzinfo is None:
                raise ValueError("audit query timestamps must be timezone-aware")
        if from_timestamp is not None and to_timestamp is not None and from_timestamp > to_timestamp:
            raise ValueError("from_timestamp cannot exceed to_timestamp")

        incident_scope_key = f"{tenant_id}:{incident_id}"
        fingerprint = self._query_fingerprint(
            incident_scope_key,
            plan_id,
            decision_type,
            from_timestamp,
            to_timestamp,
        )
        cursor_timestamp: str | None = None
        cursor_id: str | None = None
        if cursor:
            cursor_data = self._decode_cursor(cursor)
            if cursor_data.get("fingerprint") != fingerprint:
                raise ValueError("audit cursor does not match query scope or filters")
            cursor_timestamp = str(cursor_data.get("timestamp") or "")
            cursor_id = str(cursor_data.get("id") or "")
            if not cursor_timestamp or not cursor_id:
                raise ValueError("audit cursor is malformed")

        clauses = [
            "c.incident_id = @incident_id",
            "c.incident_scope_key = @incident_scope_key",
            "c.tenant_id = @tenant_id",
        ]
        parameters: list[dict[str, Any]] = [
            {"name": "@incident_id", "value": incident_id},
            {"name": "@incident_scope_key", "value": incident_scope_key},
            {"name": "@tenant_id", "value": tenant_id},
        ]
        optional_filters = (
            ("c.plan_id = @plan_id", "@plan_id", plan_id),
            ("c.decision_type = @decision_type", "@decision_type", decision_type),
            (
                "c.timestamp >= @from_timestamp",
                "@from_timestamp",
                self._format_timestamp(from_timestamp),
            ),
            (
                "c.timestamp <= @to_timestamp",
                "@to_timestamp",
                self._format_timestamp(to_timestamp),
            ),
        )
        for clause, name, filter_value in optional_filters:
            if filter_value is not None:
                clauses.append(clause)
                parameters.append({"name": name, "value": filter_value})
        if cursor_timestamp is not None and cursor_id is not None:
            clauses.append(
                "(c.timestamp > @cursor_timestamp OR (c.timestamp = @cursor_timestamp AND c.id > @cursor_id))"
            )
            parameters.extend(
                [
                    {"name": "@cursor_timestamp", "value": cursor_timestamp},
                    {"name": "@cursor_id", "value": cursor_id},
                ]
            )
        query = "SELECT * FROM c WHERE " + " AND ".join(clauses) + " ORDER BY c.timestamp ASC, c.id ASC"
        documents = self._cosmos_client.query_items(
            query=query,
            parameters=parameters,
            partition_key=incident_scope_key,
        )
        records = [EvacuationDecisionRecord.model_validate(document) for document in islice(documents, limit + 1)]
        next_cursor = None
        if len(records) > limit:
            records = records[:limit]
            last = records[-1]
            next_cursor = self._encode_cursor(
                {
                    "fingerprint": fingerprint,
                    "timestamp": last.timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                    "id": last.id,
                }
            )
        return AuditQueryPage(records=records, next_cursor=next_cursor)

    @staticmethod
    def _query_fingerprint(
        incident_scope_key: str,
        plan_id: str | None,
        decision_type: str | None,
        from_timestamp: datetime | None,
        to_timestamp: datetime | None,
    ) -> str:
        canonical = json.dumps(
            {
                "scope": incident_scope_key,
                "plan": plan_id,
                "type": decision_type,
                "from": AuditWriter._format_timestamp(from_timestamp),
                "to": AuditWriter._format_timestamp(to_timestamp),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _format_timestamp(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _encode_cursor(value: dict[str, str]) -> str:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
        return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(value: str) -> dict[str, Any]:
        try:
            padding = "=" * (-len(value) % 4)
            decoded = base64.urlsafe_b64decode(value + padding)
            result = json.loads(decoded)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("audit cursor is invalid") from exc
        if not isinstance(result, dict):
            raise ValueError("audit cursor is invalid")
        return result

    @property
    def buffer_depth(self) -> int:
        """Current in-memory buffer depth."""
        with self._lock:
            return len(self._buffer)

    __all__ = ["AuditQueryPage", "AuditWriteReceipt", "AuditWriter"]
