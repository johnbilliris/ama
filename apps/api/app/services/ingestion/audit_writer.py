import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.services.ingestion.audit_sink import AuditSink

from packages.domain.src.domain.models.ingestion_audit import IngestionAuditEntry

logger = logging.getLogger(__name__)


class AuditWriter:
    """Appends IngestionAuditEntry records as JSON Lines to Azure Blob Storage."""

    def __init__(self, blob_storage: AuditSink | None = None, now_provider: Any = None):
        self._blob_storage = blob_storage
        self._now = now_provider or (lambda: datetime.now(UTC))
        self._buffer: list[str] = []

        if self._blob_storage is not None and not hasattr(self._blob_storage, "append_line"):
            raise TypeError("AuditWriter requires blob_storage implementing append_line(blob_path, data)")

    async def write_entry(
        self,
        signal_id: str | None,
        data_source_id: str,
        correlation_id: str,
        outcome: str,
        validation_errors: list[str] | None = None,
        validation_status: str | None = None,
        raw_payload_blob_uri: str | None = None,
        raw_archival_enabled: bool | None = None,
        normalisation_latency_ms: float = 0.0,
        dedup_hash: str = "",
        pipeline_id: str = "",
    ) -> IngestionAuditEntry:
        now = self._now()
        archival_enabled = (
            bool(raw_payload_blob_uri)
            if raw_archival_enabled is None
            else raw_archival_enabled and bool(raw_payload_blob_uri)
        )
        if raw_archival_enabled and not archival_enabled:
            logger.warning(
                "Disabling raw payload archival in audit entry because no blob URI was produced "
                "for pipeline %s and correlation %s",
                pipeline_id,
                correlation_id,
            )
        entry = IngestionAuditEntry(
            audit_id=str(uuid4()),
            signal_id=signal_id,
            data_source_id=data_source_id,
            correlation_id=correlation_id,
            timestamp=now,
            outcome=outcome,
            validation_status=validation_status,
            validation_errors=validation_errors or [],
            raw_payload_blob_uri=raw_payload_blob_uri,
            raw_archival_enabled=archival_enabled,
            normalisation_latency_ms=normalisation_latency_ms,
            pipeline_id=pipeline_id,
            dedup_hash=dedup_hash,
        )
        line = entry.model_dump_json() + "\n"
        self._buffer.append(line)

        if self._blob_storage:
            blob_path = f"audit/ingestion/{now.strftime('%Y-%m-%d')}/{now.strftime('%H')}.jsonl"
            await self._blob_storage.append_line(blob_path, line.encode("utf-8"))

        return entry

    @property
    def entries(self) -> list[str]:
        return list(self._buffer)
