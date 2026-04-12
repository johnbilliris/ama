import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from packages.domain.src.domain.models.ingestion_audit import IngestionAuditEntry

logger = logging.getLogger(__name__)


class AuditWriter:
    """Appends IngestionAuditEntry records as JSON Lines to Azure Blob Storage."""

    def __init__(self, blob_storage: Any = None):
        self._blob_storage = blob_storage
        self._buffer: list[str] = []

    async def write_entry(
        self,
        signal_id: str | None,
        data_source_id: str,
        correlation_id: str,
        outcome: str,
        validation_errors: list[str] | None = None,
        raw_payload_blob_uri: str | None = None,
        normalisation_latency_ms: float = 0.0,
        dedup_hash: str = "",
        pipeline_id: str = "",
    ) -> IngestionAuditEntry:
        entry = IngestionAuditEntry(
            audit_id=str(uuid4()),
            signal_id=signal_id,
            data_source_id=data_source_id,
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
            outcome=outcome,
            validation_errors=validation_errors or [],
            raw_payload_blob_uri=raw_payload_blob_uri,
            normalisation_latency_ms=normalisation_latency_ms,
            pipeline_id=pipeline_id,
            dedup_hash=dedup_hash,
        )
        line = entry.model_dump_json() + "\n"
        self._buffer.append(line)

        if self._blob_storage:
            now = datetime.now(UTC)
            blob_path = f"audit/ingestion/{now.strftime('%Y-%m-%d')}/{now.strftime('%H')}.jsonl"
            await self._blob_storage._upload(blob_path, line.encode("utf-8"))

        return entry

    @property
    def entries(self) -> list[str]:
        return list(self._buffer)
