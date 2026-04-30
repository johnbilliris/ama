"""Audit writer with three-tier degradation strategy (matching monitoring agent pattern).

Tier 1: Cosmos DB (primary) — append-only writes
Tier 2: In-memory ring buffer (bounded at AUDIT_BUFFER_CAPACITY, default 10K)
Tier 3: Local JSONL file spill when memory buffer is full

Recovery: ``flush()`` drains memory buffer then file buffer to Cosmos DB
in chronological order, annotating each record with ``buffered_at`` and
``flush_source``.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

from evacuation.config import EvacuationConfig
from evacuation.models import AuditBufferEntry, EvacuationDecisionRecord

logger = logging.getLogger(__name__)


class AuditWriter:
    """Append-only audit trail with three-tier degradation."""

    def __init__(
        self,
        config: EvacuationConfig | None = None,
        cosmos_client: object | None = None,
    ) -> None:
        self._config = config or EvacuationConfig()
        self._cosmos_client = cosmos_client
        self._buffer: deque[AuditBufferEntry] = deque(maxlen=self._config.audit_buffer_capacity)
        self._file_path = self._config.audit_buffer_file_path
        self._tier: str = "cosmos"
        self._records_written: int = 0
        self._file_spill_count: int = 0

    def write(self, record: EvacuationDecisionRecord) -> None:
        """Write an audit record. Falls through tiers on failure."""
        # Truncate rationale to max length
        max_len = self._config.max_summary_length
        if len(record.decision_rationale) > max_len:
            record.decision_rationale = record.decision_rationale[:max_len]

        # Tier 1: Cosmos DB
        if self._cosmos_client is not None:
            try:
                self._write_to_cosmos(record)
                record.flush_source = "direct"
                self._tier = "cosmos"
                self._records_written += 1
                return
            except Exception:
                logger.warning("Cosmos DB write failed, falling back to memory buffer")

        # Tier 2: In-memory buffer
        if len(self._buffer) < self._config.audit_buffer_capacity:
            self._buffer_in_memory(record)
            self._tier = "memory"
            return

        # Tier 3: File spill
        self._spill_to_file(record)
        self._tier = "file"

    def _write_to_cosmos(self, record: EvacuationDecisionRecord) -> None:
        """Write a single record to Cosmos DB (append-only)."""
        if self._cosmos_client is None:
            raise RuntimeError("Cosmos DB client is not configured")
        container = self._cosmos_client
        doc = record.model_dump(mode="json")
        doc["id"] = str(doc["id"])
        container.create_item(body=doc)

    def _buffer_in_memory(self, record: EvacuationDecisionRecord) -> None:
        """Buffer a record in-memory (Tier 2)."""
        entry = AuditBufferEntry(
            record=record,
            buffered_at=datetime.now(UTC),
        )
        self._buffer.append(entry)
        if len(self._buffer) == 1:
            logger.warning("Audit buffer activated — Cosmos DB unavailable")

    def _spill_to_file(self, record: EvacuationDecisionRecord) -> None:
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
            except Exception:
                logger.warning("Flush failed for memory-buffered record, stopping flush")
                break

        # Then drain file buffer (if it exists)
        file_path = Path(self._file_path)
        if file_path.exists():
            try:
                remaining_lines: list[str] = []
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
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
                        except Exception:
                            remaining_lines.append(line)

                if remaining_lines:
                    with open(file_path, "w", encoding="utf-8") as f:
                        for remaining in remaining_lines:
                            f.write(remaining + "\n")
                else:
                    file_path.unlink(missing_ok=True)
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

    @property
    def buffer_depth(self) -> int:
        """Current in-memory buffer depth."""
        return len(self._buffer)
