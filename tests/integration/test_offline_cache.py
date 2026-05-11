"""T112 — Integration test for the offline cache verifier (Spec 036 / FR-RAG-LS-02; R-04, R-07; SC-009).

Exercises ``apps.agents.common.offline_cache.OfflineCacheLoader`` end-to-end:

* **Dual-signature verification**: both ``cosign_keyless`` and ``age_detached``
  MUST verify; either failing → ``OfflineCacheError`` (R-07 fail-closed).
* **14-day TTL**: at day 0 → loads; at day 11 → loads with ``stale=True``;
  at day 14 → ``OfflineCacheError`` (hard expiry).
* **Queued audit replay**: while offline, audit records are spooled to a
  local SQLite-backed buffer. On reconnect (``replay_audit_spool``) the
  records drain to the writer within ≤ 60s with ``original_timestamps``
  preserved.

The verifier accepts callables for the cosign + age verification steps so
tests can supply trivial in-memory verifiers (FR-RAG-FM-07 hermetic seam).
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest


def _module():
    import importlib

    return importlib.import_module("common.offline_cache")


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _make_manifest_dict(*, generated_at: datetime) -> dict[str, Any]:
    return {
        "version": 1,
        "generated_at": generated_at.isoformat(),
        "corpus_build_sha": "f9c3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a26",
        "ttl_days": 14,
        "stale_warning_days": 11,
        "embedding_model_id": "text-embedding-3-large",
        "entries": [
            {
                "chunk_id": "nt-cyclone-doctrine-p12-c0",
                "jurisdiction": "nt",
                "topic": "cyclone-doctrine",
                "page": 12,
                "sha256_of_chunk": "0" * 64,
                "licence_mode": "full-text",
                "byte_offset": 0,
                "byte_length": 8192,
            }
        ],
        "size_bytes_total": 8192,
        "signatures": {
            "cosign_keyless": "stub-cosign-sig",
            "age_detached": "-----BEGIN AGE ENCRYPTED FILE-----\nstubbed\n-----END AGE ENCRYPTED FILE-----",
        },
    }


def _write_manifest(tmp: Path, payload: dict[str, Any]) -> Path:
    p = tmp / "manifest.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# Dual-signature verification
# --------------------------------------------------------------------------- #


def test_loader_accepts_when_both_signatures_verify(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC))
    p = _write_manifest(tmp_path, payload)

    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: True,
        age_verify=lambda sig, _payload: True,
    )
    result = loader.load(p)
    assert result.manifest.corpus_build_sha == payload["corpus_build_sha"]
    assert result.stale is False


def test_loader_rejects_on_cosign_failure(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC))
    p = _write_manifest(tmp_path, payload)

    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: False,
        age_verify=lambda sig, _payload: True,
    )
    with pytest.raises(mod.OfflineCacheError):
        loader.load(p)


def test_loader_rejects_on_age_failure(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC))
    p = _write_manifest(tmp_path, payload)

    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: True,
        age_verify=lambda sig, _payload: False,
    )
    with pytest.raises(mod.OfflineCacheError):
        loader.load(p)


def test_loader_rejects_when_both_fail(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC))
    p = _write_manifest(tmp_path, payload)
    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: False,
        age_verify=lambda sig, _payload: False,
    )
    with pytest.raises(mod.OfflineCacheError):
        loader.load(p)


# --------------------------------------------------------------------------- #
# 14-day TTL + 11-day stale warning
# --------------------------------------------------------------------------- #


def test_fresh_cache_loads_without_warning(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC) - timedelta(days=1))
    p = _write_manifest(tmp_path, payload)

    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: True,
        age_verify=lambda sig, _payload: True,
    )
    result = loader.load(p)
    assert result.stale is False
    assert result.days_remaining == pytest.approx(13, abs=1)


def test_stale_warning_at_day_11(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC) - timedelta(days=11, hours=1))
    p = _write_manifest(tmp_path, payload)

    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: True,
        age_verify=lambda sig, _payload: True,
    )
    result = loader.load(p)
    assert result.stale is True


def test_hard_expiry_at_day_14(tmp_path: Path) -> None:
    mod = _module()
    payload = _make_manifest_dict(generated_at=datetime.now(tz=UTC) - timedelta(days=14, hours=1))
    p = _write_manifest(tmp_path, payload)

    loader = mod.OfflineCacheLoader(
        cosign_verify=lambda sig, _payload: True,
        age_verify=lambda sig, _payload: True,
    )
    with pytest.raises(mod.OfflineCacheError) as excinfo:
        loader.load(p)
    assert "expired" in str(excinfo.value).lower() or "ttl" in str(excinfo.value).lower()


# --------------------------------------------------------------------------- #
# Queued offline audit replay (SC-009)
# --------------------------------------------------------------------------- #


def _audit_record(*, ts: datetime, call_id: str) -> dict[str, Any]:
    return {
        "call_id": call_id,
        "timestamp_utc": ts.isoformat().replace("+00:00", "Z"),
        "agent_name": "RiskAssessmentAgent",
        "call_kind": "inference",
        "rag_used": False,
        "rag_optout_reason": "offline-cache-bypass",
        "adr_pointer": "docs/decisions/036-foundry-rag-grounding/04-rag-optout-planning-collection.md",
        "model_id": "gpt-4o",
        "model_version": "2024-08-06",
        "deployment_alias": "ama-foundry-au",
        "prompt_sha": "deadbeef",
        "output_text_hash": "abc123",
        "output_tokens": 12,
        "tenant_id": "t",
        "correlation_id": "c",
        "gateway_decision": "allow",
        "hallucinated_citation_count": 0,
        "retrieved_chunks": [],
    }


def test_audit_spool_drains_within_60s_preserving_timestamps(tmp_path: Path) -> None:
    mod = _module()

    # Spool 5 records while "offline".
    spool_path = tmp_path / "spool.sqlite3"
    spool = mod.AuditSpool(spool_path=spool_path)

    original_ts = [datetime.now(tz=UTC) - timedelta(minutes=10 + i) for i in range(5)]
    original_records = [_audit_record(ts=original_ts[i], call_id=f"call-{i}") for i in range(5)]
    for record in original_records:
        spool.enqueue(record)

    # Confirm spool has 5.
    assert spool.size() == 5

    # Drain to a sink writer; assert ≤ 60s SLA and timestamps preserved.
    drained: list[dict[str, Any]] = []

    async def _sink(rec: dict[str, Any]) -> None:
        drained.append(rec)

    start = datetime.now(tz=UTC)
    asyncio.run(spool.drain(_sink, sla_seconds=60))
    elapsed = (datetime.now(tz=UTC) - start).total_seconds()
    assert elapsed <= 60.0, f"drain took {elapsed:.2f}s; SC-009 SLA is 60s"
    assert len(drained) == 5
    # Timestamps preserved with original values intact.
    drained_ts = sorted(rec["timestamp_utc"] for rec in drained)
    expected_ts = sorted(rec["timestamp_utc"] for rec in original_records)
    assert drained_ts == expected_ts
    # Spool emptied.
    assert spool.size() == 0


def test_audit_spool_persists_across_restart(tmp_path: Path) -> None:
    """If the device restarts before reconnect, queued records survive."""
    mod = _module()
    spool_path = tmp_path / "spool.sqlite3"

    spool1 = mod.AuditSpool(spool_path=spool_path)
    rec = _audit_record(ts=datetime.now(tz=UTC), call_id="persist-1")
    spool1.enqueue(rec)
    assert spool1.size() == 1

    # Simulate restart by re-opening.
    spool2 = mod.AuditSpool(spool_path=spool_path)
    assert spool2.size() == 1
    drained: list[dict[str, Any]] = []

    async def _sink(rec: dict[str, Any]) -> None:
        drained.append(rec)

    asyncio.run(spool2.drain(_sink, sla_seconds=60))
    assert len(drained) == 1
    assert drained[0]["call_id"] == "persist-1"
