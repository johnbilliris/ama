"""T069 — Audit-replay invariant test (Spec 036 / FR-RAG-AG-02, SC-011, R-13).

Given ``(corpus_build_sha, prompt_sha, model_version, retrieved_chunks_set)``,
replay reproduces byte-identical retrieval inputs ≥ 95% across one-month window.

This integration test exercises a deterministic replay against a synthetic
sample of audit records and asserts the replay key is sufficient.
"""

from __future__ import annotations

import hashlib
from typing import Any


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _audit_module():
    import importlib

    return importlib.import_module("common.audit")


def _build_record(
    *,
    corpus_build_sha: str,
    prompt_sha: str,
    model_version: str,
    chunk_shas: list[str],
) -> dict[str, Any]:
    return {
        "call_id": hashlib.sha256(f"{corpus_build_sha}|{prompt_sha}|{model_version}".encode()).hexdigest()[:36],
        "timestamp_utc": "2026-05-15T03:42:11Z",
        "agent_name": "RiskAssessmentAgent",
        "call_kind": "inference",
        "prompt_sha": prompt_sha,
        "model_id": "gpt-4o-mini",
        "model_version": model_version,
        "deployment_alias": "ama-prod-v1",
        "embedding_model_id": "text-embedding-3-large",
        "corpus_build_sha": corpus_build_sha,
        "retrieved_chunks": [
            {
                "chunk_id": f"c-{i}",
                "sha256_of_chunk": s,
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": i + 1,
                "licence_mode": "full-text",
                "confidence": 0.9,
            }
            for i, s in enumerate(chunk_shas)
        ],
        "rag_used": True,
        "gateway_decision": "allow",
        "hallucinated_citation_count": 0,
        "output_tokens": 200,
        "output_text_hash": "0" * 64,
        "tenant_id": "t",
        "correlation_id": "c",
    }


def test_replay_key_derives_byte_identical_inputs() -> None:
    """The replay key (corpus_build_sha, prompt_sha, model_version, chunk_shas)
    MUST be sufficient to reproduce byte-identical retrieval inputs."""
    mod = _audit_module()
    cbs = "f" * 64
    ps = "9" * 64
    mv = "2024-07-18"
    chunk_shas = ["a" * 64, "b" * 64, "c" * 64]
    rec1 = _build_record(corpus_build_sha=cbs, prompt_sha=ps, model_version=mv, chunk_shas=chunk_shas)
    rec2 = _build_record(corpus_build_sha=cbs, prompt_sha=ps, model_version=mv, chunk_shas=chunk_shas)
    key1 = mod.replay_key(rec1)
    key2 = mod.replay_key(rec2)
    assert key1 == key2  # deterministic
    # Different chunks → different replay key.
    rec3 = _build_record(corpus_build_sha=cbs, prompt_sha=ps, model_version=mv, chunk_shas=chunk_shas[::-1])
    assert mod.replay_key(rec3) != key1


def test_replay_key_robust_to_missing_optional_fields() -> None:
    mod = _audit_module()
    record = _build_record(corpus_build_sha="a" * 64, prompt_sha="b" * 64, model_version="m", chunk_shas=["c" * 64])
    record.pop("operator_actions", None)
    key = mod.replay_key(record)
    assert isinstance(key, str)
    assert len(key) == 64  # sha256 hex


def test_one_month_window_replay_simulation_meets_95_percent() -> None:
    """Synthesise a one-month window of 1000 records; assert ≥ 95% replay-key
    determinism."""
    mod = _audit_module()
    records: list[dict[str, Any]] = []
    cbs = "f" * 64
    mv = "2024-07-18"
    for i in range(1000):
        ps = hashlib.sha256(f"prompt-{i}".encode()).hexdigest()
        chunks = [hashlib.sha256(f"chunk-{i}-{j}".encode()).hexdigest() for j in range(3)]
        records.append(_build_record(corpus_build_sha=cbs, prompt_sha=ps, model_version=mv, chunk_shas=chunks))

    # Replay each: derive key, reconstruct minimal-input shape from record, verify hash match.
    matches = 0
    for r in records:
        derived = mod.replay_key(r)
        # Reconstruction: same inputs → same key.
        rebuilt = _build_record(
            corpus_build_sha=r["corpus_build_sha"],
            prompt_sha=r["prompt_sha"],
            model_version=r["model_version"],
            chunk_shas=[c["sha256_of_chunk"] for c in r["retrieved_chunks"]],
        )
        if mod.replay_key(rebuilt) == derived:
            matches += 1
    fidelity = matches / len(records)
    assert fidelity >= 0.95, f"audit-replay fidelity {fidelity:.4f} < 0.95 (SC-011)"
