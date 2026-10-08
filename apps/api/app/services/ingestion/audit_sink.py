from __future__ import annotations

from typing import Protocol


class AuditSink(Protocol):
    """Public sink contract for append-only ingestion audit JSONL writes."""

    async def append_line(self, blob_path: str, data: bytes) -> None:
        """Append one newline-terminated JSON record to the blob path."""
