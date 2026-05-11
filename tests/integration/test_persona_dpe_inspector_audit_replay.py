"""Spec 036 T102 — NSW DPE Inspector audit-replay persona scenario (SC-001, SC-011).

Validates that an operator can audit-replay any recommendation in ≤ 60s
using the spec-036 audit fields. The harness is hermetic:

* Fakes a corpus build SHA, prompt SHA, model version, chunk SHA set.
* Builds an AuditRecord through ``apps/agents/common/audit.make_inference_record``.
* Round-trips through ``replay_key(...)`` and asserts deterministic output.

The 60s wall-clock budget is asserted separately (the slow path is the
operator UI rendering the linked rendered_url; see T086). The
machine-side replay is sub-millisecond.
"""

from __future__ import annotations

import time

import pytest


def _audit():
    import importlib

    return importlib.import_module("common.audit")


def test_dpe_inspector_audit_replay_under_60s_budget() -> None:
    mod = _audit()
    cbs = "f" * 64
    ps = "9" * 64
    record = mod.make_inference_record(
        agent_name="RiskAssessmentAgent",
        prompt_sha=ps,
        model_id="gpt-4o-mini",
        model_version="2024-07-18",
        deployment_alias="ama-prod-v1",
        output_text_hash="0" * 64,
        output_tokens=120,
        tenant_id="nsw-dpe",
        correlation_id="cor-1",
        rag_used=True,
        embedding_model_id="text-embedding-3-large",
        corpus_build_sha=cbs,
        retrieved_chunks=[
            {
                "chunk_id": "c1",
                "sha256_of_chunk": "a" * 64,
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "licence_mode": "full-text",
                "confidence": 0.84,
            },
            {
                "chunk_id": "c2",
                "sha256_of_chunk": "b" * 64,
                "jurisdiction": "national",
                "topic": "aiims",
                "page": 12,
                "licence_mode": "metadata-only",
                "confidence": 0.78,
            },
        ],
        citations=[
            {
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "source_url": "https://www.rfs.nsw.gov.au/x.pdf",
                "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
                "sha256_of_chunk": "a" * 64,
                "licence_mode": "full-text",
                "confidence": 0.84,
                "snippet": "When the area is deemed safe…",
            },
        ],
    )
    start = time.perf_counter()
    key = mod.replay_key(record)
    elapsed = time.perf_counter() - start
    # Hard ceiling: 1s (we expect sub-ms; 1s is generous defence against
    # CI scheduler noise).
    assert elapsed < 1.0, f"replay_key too slow: {elapsed * 1000:.1f}ms"
    assert isinstance(key, str)
    assert len(key) == 64

    # Idempotent — same record returns the same key.
    key2 = mod.replay_key(record)
    assert key == key2


def test_dpe_inspector_replay_remains_stable_after_operator_action() -> None:
    """SC-011: post-hoc operator_actions[] mutations preserve the replay key."""
    mod = _audit()
    record = mod.make_inference_record(
        agent_name="RiskAssessmentAgent",
        prompt_sha="9" * 64,
        model_id="gpt-4o-mini",
        model_version="2024-07-18",
        deployment_alias="ama-prod-v1",
        output_text_hash="0" * 64,
        output_tokens=120,
        tenant_id="nsw-dpe",
        correlation_id="cor-1",
        rag_used=True,
        embedding_model_id="text-embedding-3-large",
        corpus_build_sha="f" * 64,
        retrieved_chunks=[
            {
                "chunk_id": "c1",
                "sha256_of_chunk": "a" * 64,
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "licence_mode": "full-text",
                "confidence": 0.84,
            },
        ],
        citations=[
            {
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "source_url": "https://www.rfs.nsw.gov.au/x.pdf",
                "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
                "sha256_of_chunk": "a" * 64,
                "licence_mode": "full-text",
                "confidence": 0.84,
                "snippet": "When the area is deemed safe…",
            },
        ],
    )
    key_before = mod.replay_key(record)
    record["operator_actions"] = [
        {"actor_oid": "u1", "action": "approved", "timestamp_utc": "2026-05-15T03:55:11Z"},
    ]
    key_after = mod.replay_key(record)
    assert key_before == key_after, "operator_actions mutations must not alter replay key"


@pytest.mark.parametrize(
    "agent_name",
    [
        "MonitoringAgent",
        "RiskAssessmentAgent",
        "EvacuationAgent",
        "ResourceAllocationAgent",
        "CommunicationAgent",
        "SimulationController",
    ],
)
def test_replay_key_for_every_grounded_agent(agent_name: str) -> None:
    mod = _audit()
    record = mod.make_inference_record(
        agent_name=agent_name,
        prompt_sha="9" * 64,
        model_id="gpt-4o-mini",
        model_version="2024-07-18",
        deployment_alias="ama-prod-v1",
        output_text_hash="0" * 64,
        output_tokens=42,
        tenant_id="t",
        correlation_id="c",
        rag_used=True,
        embedding_model_id="text-embedding-3-large",
        corpus_build_sha="f" * 64,
        retrieved_chunks=[
            {
                "chunk_id": "c1",
                "sha256_of_chunk": "a" * 64,
                "jurisdiction": "national",
                "topic": "aiims",
                "page": 12,
                "licence_mode": "metadata-only",
                "confidence": 0.7,
            },
        ],
    )
    key = mod.replay_key(record)
    assert len(key) == 64
