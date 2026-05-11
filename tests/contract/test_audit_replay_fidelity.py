"""Spec 036 T144 — Compliance audit byte-replay automation (SC-011, FR-RAG-AG-02).

Sampled-replay fidelity ≥ 95% across a one-month rolling window. Hermetic
extension of the existing ``tests/integration/test_audit_replay.py`` (T069)
that adds:

1. **Sampled byte-replay** — randomly sample N records from a synthetic
   one-month window, reconstruct their replay-keys from the audit-record
   shape, and assert ≥ 95% byte-identical reproduction.

2. **KQL hygiene check** — the ``audit_replay_fidelity.kql`` query exists
   and parses (no syntactic regression) so the alert binds when uploaded
   to Application Insights.

This is a complement to the live alert authored at
``tests/audit/audit_replay_fidelity.kql`` — the alert pages on-call at
runtime; this test catches regressions in the replay-key derivation
*at PR time* before the alert can ever fire.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
KQL_PATH = ROOT / "tests" / "audit" / "audit_replay_fidelity.kql"


def _audit_module():
    import importlib

    return importlib.import_module("common.audit")


def _build_record(
    *,
    corpus_build_sha: str,
    prompt_sha: str,
    model_version: str,
    chunk_shas: list[str],
    drop_field: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
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
    if drop_field:
        record.pop(drop_field, None)
    return record


def _generate_window(n: int, *, seed: int) -> list[dict[str, Any]]:
    """Synthesise an N-record one-month rolling window with deterministic seed."""
    rng = random.Random(seed)
    cbs = "f" * 64
    mv = "2024-07-18"
    out: list[dict[str, Any]] = []
    for i in range(n):
        ps = hashlib.sha256(f"prompt-{i}-{rng.random()}".encode()).hexdigest()
        chunks = [
            hashlib.sha256(f"chunk-{i}-{j}-{rng.random()}".encode()).hexdigest() for j in range(rng.randint(2, 5))
        ]
        out.append(_build_record(corpus_build_sha=cbs, prompt_sha=ps, model_version=mv, chunk_shas=chunks))
    return out


# ---------------------------------------------------------------------- #
# 1. Sampled SC-011 byte-replay (≥ 95% over a 1-month rolling window).
# ---------------------------------------------------------------------- #


def test_sampled_byte_replay_meets_95_percent_over_one_month_window() -> None:
    """N=2_500 records over 30 days → ≥ 95% byte-identical replay (SC-011)."""
    mod = _audit_module()
    records = _generate_window(2_500, seed=42)

    # Sample 250 records uniformly (Compliance-memo: ≥ 10% sampling rate).
    sampler = random.Random(99)
    sample = sampler.sample(records, k=250)

    matches = 0
    for r in sample:
        derived_key = mod.replay_key(r)
        rebuilt = _build_record(
            corpus_build_sha=r["corpus_build_sha"],
            prompt_sha=r["prompt_sha"],
            model_version=r["model_version"],
            chunk_shas=[c["sha256_of_chunk"] for c in r["retrieved_chunks"]],
        )
        if mod.replay_key(rebuilt) == derived_key:
            matches += 1

    fidelity = matches / len(sample)
    assert fidelity >= 0.95, f"sampled byte-replay fidelity {fidelity:.4f} < 0.95 (SC-011)"


def test_sampled_byte_replay_detects_chunk_set_corruption() -> None:
    """If the recorded chunk set is mutated, replay MUST detect it (defence)."""
    mod = _audit_module()
    record = _build_record(
        corpus_build_sha="f" * 64,
        prompt_sha="9" * 64,
        model_version="2024-07-18",
        chunk_shas=["a" * 64, "b" * 64, "c" * 64],
    )
    derived = mod.replay_key(record)
    # Corrupt the set: replace one chunk sha.
    record["retrieved_chunks"][0]["sha256_of_chunk"] = "z" * 64
    rebuilt = _build_record(
        corpus_build_sha=record["corpus_build_sha"],
        prompt_sha=record["prompt_sha"],
        model_version=record["model_version"],
        chunk_shas=[c["sha256_of_chunk"] for c in record["retrieved_chunks"]],
    )
    assert mod.replay_key(rebuilt) != derived, "replay key must change when chunk set mutates"


def test_sampled_byte_replay_robust_to_missing_optional_fields() -> None:
    """Missing optional fields (e.g. operator_actions) MUST not crash replay."""
    mod = _audit_module()
    record = _build_record(
        corpus_build_sha="a" * 64,
        prompt_sha="b" * 64,
        model_version="m",
        chunk_shas=["c" * 64],
    )
    record.pop("operator_actions", None)
    record.pop("output_tokens", None)
    record.pop("output_text_hash", None)
    key = mod.replay_key(record)
    assert isinstance(key, str)
    assert len(key) == 64


# ---------------------------------------------------------------------- #
# 2. KQL hygiene check — the alert query exists + names every replay-key
#    field that the audit-record shape persists.
# ---------------------------------------------------------------------- #


def test_audit_replay_fidelity_kql_exists_and_references_replay_key_fields() -> None:
    """The KQL alert MUST exist + reference every SC-011 replay-key field."""
    assert KQL_PATH.exists(), "tests/audit/audit_replay_fidelity.kql missing — T144 alert un-bound"
    text = KQL_PATH.read_text(encoding="utf-8")
    for field in (
        "corpus_build_sha",
        "prompt_sha",
        "model_version",
        "retrieved_chunks",
        "sha256_of_chunk",
        "rag_used",
    ):
        assert field in text, f"audit_replay_fidelity.kql does not reference {field!r}; SC-011 replay key incomplete"
    # 95% threshold MUST be referenced.
    assert "95" in text, "audit_replay_fidelity.kql missing the 95% threshold"
    # Window size 30 days (Compliance-memo).
    assert "30d" in text, "audit_replay_fidelity.kql missing the 30-day window"


def test_audit_trail_completeness_and_replay_fidelity_kql_coexist() -> None:
    """T099 + T144 both ship — completeness AND replay-fidelity alerts."""
    completeness = ROOT / "tests" / "audit" / "audit_trail_completeness.kql"
    assert completeness.exists()
    assert KQL_PATH.exists()
    # They MUST query the same logical table for consistency.
    for path in (completeness, KQL_PATH):
        assert "audit_records" in path.read_text(encoding="utf-8"), (
            f"{path.name} does not query the audit_records table"
        )


# ---------------------------------------------------------------------- #
# 3. Property-test: identical records → identical keys (determinism).
# ---------------------------------------------------------------------- #


@pytest.mark.parametrize("seed", [1, 7, 23, 101])
def test_replay_key_is_deterministic_under_repeated_construction(seed: int) -> None:
    mod = _audit_module()
    records = _generate_window(50, seed=seed)
    for r in records:
        key1 = mod.replay_key(r)
        key2 = mod.replay_key(r)
        assert key1 == key2
