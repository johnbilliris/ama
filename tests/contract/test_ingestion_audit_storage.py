from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from app.services.ingestion.audit_writer import AuditWriter
from app.services.ingestion.blob_storage import BlobStorageService

from packages.domain.src.domain.models.ingestion_audit import IngestionAuditEntry


def _base_kwargs() -> dict[str, object]:
    return {
        "audit_id": "aud-1",
        "signal_id": "sig-1",
        "data_source_id": "bom-warnings",
        "correlation_id": "corr-1",
        "timestamp": datetime.now(UTC),
        "validation_errors": [],
        "raw_payload_blob_uri": "raw-payloads/bom-warnings/2026-09-16/sig-1.json",
        "normalisation_latency_ms": 12.5,
        "pipeline_id": "bom-warnings",
        "dedup_hash": "abc",
        "validation_status": "validated",
        "raw_archival_enabled": True,
    }


def test_all_pipeline_outcomes_are_accepted() -> None:
    expected = {"success", "rejected", "failed", "deduplicated", "blocked", "degraded"}
    accepted: set[str] = set()

    for outcome in expected:
        kwargs = _base_kwargs()
        kwargs["outcome"] = outcome
        if outcome == "success":
            kwargs["validation_status"] = "validated"
            kwargs["validation_errors"] = []
            kwargs["signal_id"] = "sig-1"
            kwargs["raw_payload_blob_uri"] = "raw-payloads/x.json"
        elif outcome == "rejected":
            kwargs["validation_status"] = "rejected"
            kwargs["validation_errors"] = ["schema error"]
            kwargs["signal_id"] = None
        elif outcome in {"blocked", "degraded"}:
            kwargs["signal_id"] = None
            kwargs["validation_status"] = None
            kwargs["validation_errors"] = ["dependency unavailable"]
        else:
            kwargs["signal_id"] = None
            kwargs["validation_status"] = None
            kwargs["validation_errors"] = []

        entry = IngestionAuditEntry(**kwargs)
        accepted.add(entry.outcome)

    assert accepted == expected


def test_audit_writer_rejects_non_protocol_sink() -> None:
    with pytest.raises(TypeError, match="append_line"):
        AuditWriter(blob_storage=object())


@pytest.mark.asyncio
async def test_same_hour_entries_are_appended_and_retrievable() -> None:
    blob_storage = BlobStorageService(blob_service_client=None)
    fixed_time = datetime(2026, 9, 16, 5, 30, tzinfo=UTC)
    writer = AuditWriter(blob_storage=blob_storage, now_provider=lambda: fixed_time)

    await writer.write_entry(
        signal_id="sig-a",
        data_source_id="bom-warnings",
        correlation_id="corr-a",
        outcome="success",
        validation_status="validated",
        raw_payload_blob_uri="raw/a",
        raw_archival_enabled=True,
    )
    await writer.write_entry(
        signal_id="sig-b",
        data_source_id="bom-warnings",
        correlation_id="corr-b",
        outcome="success",
        validation_status="validated",
        raw_payload_blob_uri="raw/b",
        raw_archival_enabled=True,
    )

    blob_path = "audit/ingestion/2026-09-16/05.jsonl"
    payload = await blob_storage.retrieve(blob_path)
    assert payload is not None
    lines = payload.decode("utf-8").strip().splitlines()
    assert len(lines) == 2


@pytest.mark.asyncio
async def test_writer_disables_archival_when_uri_is_omitted() -> None:
    entry = await AuditWriter().write_entry(
        signal_id="sig-no-raw",
        data_source_id="bom-warnings",
        correlation_id="corr-no-raw",
        outcome="success",
        validation_status="validated",
    )

    assert entry.raw_payload_blob_uri is None
    assert entry.raw_archival_enabled is False


@pytest.mark.asyncio
async def test_writer_disables_inconsistent_explicit_archival_flag() -> None:
    entry = await AuditWriter().write_entry(
        signal_id="sig-no-raw",
        data_source_id="bom-radar",
        correlation_id="corr-no-raw",
        outcome="success",
        validation_status="validated",
        raw_archival_enabled=True,
    )

    assert entry.raw_payload_blob_uri is None
    assert entry.raw_archival_enabled is False


@pytest.mark.asyncio
async def test_concurrent_and_hour_rollover_writes_preserve_all_entries() -> None:
    blob_storage = BlobStorageService(blob_service_client=None)
    timestamps = [
        datetime(2026, 9, 16, 5, 59, tzinfo=UTC),
        datetime(2026, 9, 16, 5, 59, tzinfo=UTC),
        datetime(2026, 9, 16, 6, 0, tzinfo=UTC),
    ]

    def _now() -> datetime:
        return timestamps.pop(0)

    writer = AuditWriter(blob_storage=blob_storage, now_provider=_now)

    async def _write(idx: int) -> None:
        await writer.write_entry(
            signal_id=f"sig-{idx}",
            data_source_id="bom-warnings",
            correlation_id=f"corr-{idx}",
            outcome="success",
            validation_status="validated",
            raw_payload_blob_uri=f"raw-{idx}",
            raw_archival_enabled=True,
        )

    await asyncio.gather(_write(1), _write(2), _write(3))

    hour_05 = await blob_storage.retrieve("audit/ingestion/2026-09-16/05.jsonl")
    hour_06 = await blob_storage.retrieve("audit/ingestion/2026-09-16/06.jsonl")
    assert hour_05 is not None
    assert hour_06 is not None
    assert len(hour_05.decode("utf-8").strip().splitlines()) == 2
    assert len(hour_06.decode("utf-8").strip().splitlines()) == 1
