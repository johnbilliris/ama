"""Audit writer with three-tier degradation strategy.

Tier 1: Cosmos DB (primary) — append-only writes to ``communication-decisions`` container
Tier 2: In-memory ring buffer (bounded at AUDIT_BUFFER_CAPACITY, default 10K)
Tier 3: Local JSONL file spill when memory buffer is full

Recovery: ``flush()`` drains memory buffer then file buffer to Cosmos DB
in chronological order, annotating each record with ``buffered_at`` and
``flush_source``.
"""

from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

from communication.config import CommunicationConfig
from communication.models import AuditBufferEntry, CommunicationDecisionRecord, CommunicationDecisionType

logger = logging.getLogger(__name__)


class AuditWriter:
    """Append-only audit trail with three-tier degradation."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        cosmos_client: object | None = None,
    ) -> None:
        self._config = config or CommunicationConfig()
        self._cosmos_client = cosmos_client
        self._buffer: deque[AuditBufferEntry] = deque(maxlen=self._config.audit_buffer_capacity)
        self._file_path = self._config.audit_buffer_file_path
        self._tier: str = "cosmos"
        self._records_written: int = 0
        self._file_spill_count: int = 0
        self._lock = threading.RLock()

    def write(self, record: CommunicationDecisionRecord) -> None:
        """Write an audit record. Falls through tiers on failure."""
        with self._lock:
            self._write_locked(record)

    def _write_locked(self, record: CommunicationDecisionRecord) -> None:
        # Tier 1: Cosmos DB
        if self._cosmos_client is not None:
            try:
                record.flush_source = "direct"
                self._write_to_cosmos(record)
                self._tier = "cosmos"
                self._records_written += 1
                return
            except Exception as exc:
                if self._is_duplicate(exc):
                    self._tier = "cosmos"
                    return
                logger.warning("Cosmos DB write failed, falling back to memory buffer")

        # Tier 2: In-memory buffer
        if len(self._buffer) < self._config.audit_buffer_capacity:
            self._buffer_in_memory(record)
            self._tier = "memory"
            return

        # Tier 3: File spill
        self._spill_to_file(record)
        self._tier = "file"

    def _write_to_cosmos(self, record: CommunicationDecisionRecord) -> None:
        """Write a single record to Cosmos DB (append-only)."""
        if self._cosmos_client is None:
            raise RuntimeError("Cosmos DB client is not configured")
        container = self._cosmos_client
        doc = record.model_dump(mode="json")
        doc["id"] = str(doc["id"])
        container.create_item(body=doc)

    def _buffer_in_memory(self, record: CommunicationDecisionRecord) -> None:
        """Buffer a record in-memory (Tier 2)."""
        entry = AuditBufferEntry(
            record=record,
            buffered_at=datetime.now(UTC),
        )
        self._buffer.append(entry)
        if len(self._buffer) == 1:
            logger.warning("Audit buffer activated — Cosmos DB unavailable")

    def _spill_to_file(self, record: CommunicationDecisionRecord) -> None:
        """Spill a record to local JSONL file (Tier 3)."""
        try:
            path = Path(self._file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            entry = AuditBufferEntry(
                record=record,
                buffered_at=datetime.now(UTC),
            )
            with open(path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
            self._file_spill_count += 1
            logger.critical(
                "Audit record spilled to file — memory buffer full (%d entries), file: %s",
                len(self._buffer),
                self._file_path,
            )
        except Exception:
            logger.critical(
                "AUDIT RECORD LOSS RISK — failed to spill to file: %s",
                self._file_path,
                exc_info=True,
            )

    def flush(self) -> int:
        """Flush buffered records to Cosmos DB. Returns count of records flushed."""
        with self._lock:
            return self._flush_locked()

    def _flush_locked(self) -> int:
        if self._cosmos_client is None:
            return 0

        flushed = 0

        # Drain memory buffer first (chronological order)
        while self._buffer:
            entry = self._buffer[0]
            entry.record.buffered_at = entry.buffered_at
            entry.record.flush_source = "memory_buffer"
            entry.retry_count += 1
            entry.last_retry_at = datetime.now(UTC)
            try:
                self._write_to_cosmos(entry.record)
                self._buffer.popleft()
                flushed += 1
            except Exception as exc:
                if self._is_duplicate(exc):
                    self._buffer.popleft()
                    flushed += 1
                    continue
                logger.warning("Flush failed for memory-buffered record, stopping flush")
                return flushed

        # Then drain file buffer (if it exists)
        file_path = Path(self._file_path)
        if file_path.exists():
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
                remaining_lines: list[str] = []
                failed = False
                for line in lines:
                    if failed:
                        remaining_lines.append(line)
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry_data = json.loads(line)
                        entry = AuditBufferEntry.model_validate(entry_data)
                        entry.record.buffered_at = entry.buffered_at
                        entry.record.flush_source = "file_buffer"
                        self._write_to_cosmos(entry.record)
                        flushed += 1
                    except Exception as exc:
                        if self._is_duplicate(exc):
                            flushed += 1
                            continue
                        remaining_lines.append(line)
                        failed = True

                if remaining_lines:
                    temporary = file_path.with_suffix(file_path.suffix + ".tmp")
                    temporary.write_text("\n".join(remaining_lines) + "\n", encoding="utf-8")
                    temporary.replace(file_path)
                    self._file_spill_count = len(remaining_lines)
                else:
                    file_path.unlink(missing_ok=True)
                    self._file_spill_count = 0
            except Exception:
                logger.warning("Failed to process file buffer during flush", exc_info=True)

        if flushed > 0:
            logger.info("Flushed %d audit records to Cosmos DB", flushed)
            self._tier = "cosmos"

        return flushed

    def get_status(self) -> str:
        """Return current audit tier: 'healthy' | 'buffering' | 'degraded'."""
        if self._tier == "cosmos" and len(self._buffer) == 0:
            return "healthy"
        if self._tier == "file" or self._file_spill_count > 0:
            return "degraded"
        if len(self._buffer) > 0:
            return "buffering"
        return "healthy"

    def records_for(
        self,
        *,
        tenant_id: str,
        handoff_id: str | None = None,
        alert_id: str | None = None,
    ) -> list[CommunicationDecisionRecord]:
        records = [entry.record for entry in self._buffer if entry.record.tenant_id == tenant_id]
        if self._cosmos_client is not None:
            clauses = ["c.tenant_id = @tenant_id"]
            parameters = [{"name": "@tenant_id", "value": tenant_id}]
            if handoff_id is not None:
                clauses.append("c.handoff_id = @handoff_id")
                parameters.append({"name": "@handoff_id", "value": handoff_id})
            if alert_id is not None:
                clauses.append("c.alert_id = @alert_id")
                parameters.append({"name": "@alert_id", "value": alert_id})
            documents = self._cosmos_client.query_items(
                query=f"SELECT * FROM c WHERE {' AND '.join(clauses)}",
                parameters=parameters,
                partition_key=tenant_id,
            )
            records.extend(CommunicationDecisionRecord.model_validate(document) for document in documents)
        if handoff_id is not None:
            records = [record for record in records if record.handoff_id == handoff_id]
        if alert_id is not None:
            records = [record for record in records if record.alert_id == alert_id]
        return records

    def missing_decisions(
        self,
        expected: set[CommunicationDecisionType],
        *,
        tenant_id: str,
        handoff_id: str,
    ) -> set[CommunicationDecisionType]:
        observed = {record.decision_type for record in self.records_for(tenant_id=tenant_id, handoff_id=handoff_id)}
        return expected - observed

    @property
    def buffer_depth(self) -> int:
        """Current in-memory and file-backed record count."""
        return len(self._buffer) + self._file_spill_count

    @property
    def records_written(self) -> int:
        """Total records written to primary storage."""
        return self._records_written

    @staticmethod
    def _is_duplicate(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        return status_code == 409 or "Conflict" in type(exc).__name__
