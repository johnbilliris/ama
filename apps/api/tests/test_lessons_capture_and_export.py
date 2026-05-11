"""Phase H — lessons capture + audit export tests (T-H02/T-H06)."""

from __future__ import annotations

import gzip
from datetime import UTC, datetime, timedelta

import pytest

from apps.api.app.services.simulation.audit_export import build_export
from apps.api.app.services.simulation.audit_writer import AuditWriter
from apps.api.app.services.simulation.lessons_capture import (
    aggregate_participant_summary,
    generate,
)

pytestmark = pytest.mark.asyncio


async def _seed_audit(sim_id: str = "sim-H") -> AuditWriter:
    AuditWriter.reset_memory_for_test()
    audit = AuditWriter()
    await audit.write(
        "injection.attempted",
        simulation_id=sim_id,
        actor="alice",
        details={
            "chat_turn_id": "turn-1",
            "user_id": "alice",
            "original_text_hash": "a" * 64,
            "parse_started_at": datetime.now(UTC),
            "pii_redactions": 0,
        },
    )
    await audit.write(
        "injection.success",
        simulation_id=sim_id,
        actor="alice",
        details={
            "chat_turn_id": "turn-1",
            "injection_correlation_id": "corr-1",
            "signal_ids": ["sig-1"],
            "categories": ["weather"],
            "confidences": ["medium"],
            "model_deployment": "gpt-4o-australiaeast",
            "prompt_hash": "b" * 64,
        },
    )
    await audit.write(
        "sub_agent.timeout",
        simulation_id=sim_id,
        actor="planning_adapter",
        details={
            "correlation_id": "corr-1",
            "sub_agent": "planning",
            "timeout_seconds": 120.0,
            "soft_ack_emitted": True,
        },
    )
    return audit


async def test_aggregate_participant_summary_counts_correctly() -> None:
    await _seed_audit()
    entries = AuditWriter.memory_for_test("sim-H")
    summary = aggregate_participant_summary(audit_entries=entries)
    assert summary.injections_attempted == 1
    assert summary.injections_accepted == 1
    assert summary.sub_agents_invoked == 1


async def test_generate_writes_blob_and_index_idempotently() -> None:
    sim_id = "sim-H-2"
    await _seed_audit(sim_id)
    entries = AuditWriter.memory_for_test(sim_id)

    blob_calls: list[tuple[str, int]] = []
    index_calls: list[dict[str, object]] = []

    async def upload(record_id: str, payload: bytes) -> str:
        blob_calls.append((record_id, len(payload)))
        return f"https://blob.example/exercise-outcome-records/{record_id}.json"

    async def write_index(doc: dict[str, object]) -> None:
        index_calls.append(doc)

    res = await generate(
        simulation_id=sim_id,
        tenant_id="tenant-H",
        start_at=datetime.now(UTC) - timedelta(hours=1),
        end_at=datetime.now(UTC),
        end_reason="completed",
        audit_entries=entries,
        blob_uploader=upload,
        index_writer=write_index,
    )
    assert res.record.record_id == sim_id  # FR-055 idempotency invariant
    assert res.blob_uri and res.index_written is True
    assert len(blob_calls) == 1
    assert index_calls[0]["id"] == sim_id


async def test_audit_export_produces_ndjson_gzip_and_sha256() -> None:
    sim_id = "sim-H-3"
    await _seed_audit(sim_id)
    entries = AuditWriter.memory_for_test(sim_id)
    bundle = build_export(audit_entries=entries, simulation_id=sim_id)

    assert bundle.line_count == 3
    decompressed = gzip.decompress(bundle.body).decode("utf-8")
    lines = decompressed.split("\n")
    assert len(lines) == 3
    # Lines must be ordered by sequence_number
    seq = [int(line.split('"sequence_number":', 1)[1].split(",", 1)[0]) for line in lines]
    assert seq == sorted(seq)
    # SHA-256 must match
    import hashlib

    assert hashlib.sha256(bundle.body).hexdigest() == bundle.sha256


async def test_audit_export_filters_by_entry_type_and_time_range() -> None:
    sim_id = "sim-H-4"
    await _seed_audit(sim_id)
    entries = AuditWriter.memory_for_test(sim_id)
    bundle = build_export(
        audit_entries=entries,
        simulation_id=sim_id,
        entry_types=["injection.attempted"],
    )
    assert bundle.line_count == 1


async def test_audit_export_flags_non_au_carve_out() -> None:
    AuditWriter.reset_memory_for_test()
    audit = AuditWriter()
    sim_id = "sim-H-5"
    await audit.write(
        "injection.success",
        simulation_id=sim_id,
        actor="bob",
        details={
            "chat_turn_id": "turn-X",
            "injection_correlation_id": "corr-X",
            "signal_ids": ["sig-X"],
            "categories": ["weather"],
            "confidences": ["high"],
            "model_deployment": "gpt-4o-eastus2",  # non-AU
            "prompt_hash": "c" * 64,
        },
    )
    entries = AuditWriter.memory_for_test(sim_id)
    bundle = build_export(audit_entries=entries, simulation_id=sim_id)
    body = gzip.decompress(bundle.body).decode("utf-8")
    assert "carve_out_review_required" in body
    assert "eastus2" in body
