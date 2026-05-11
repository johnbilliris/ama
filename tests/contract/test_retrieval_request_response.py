"""T063 — Entity test for ``RetrievalRequest`` / ``RetrievalResult`` (Spec 036).

Pydantic-v2 round-trip + invariants per data-model.md §RetrievalRequest /
§RetrievalResult: ``min_length=1`` for jurisdictions, ``top_k ∈ [1, 20]``,
``classification_max == "OFFICIAL"``.
"""

from __future__ import annotations

import pytest


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def test_round_trip_request() -> None:
    dom = _domain()
    payload = {
        "agent_name": "RiskAssessmentAgent",
        "jurisdictions": ["nsw"],
        "hazard_type": "bushfire",
        "query_text": "aiims span of control",
        "top_k": 5,
        "classification_max": "OFFICIAL",
        "tenant_id": "agency-nsw-rfs",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    }
    req = dom.RetrievalRequest.model_validate(payload)
    out = req.model_dump(mode="json")
    # jurisdictions stored as enum strings; round-trip equivalence on the wire.
    assert out["jurisdictions"] == ["nsw"]
    assert out["top_k"] == 5
    assert out["classification_max"] == "OFFICIAL"


def test_top_k_bounds_strict() -> None:
    dom = _domain()
    base = {
        "agent_name": "MonitoringAgent",
        "jurisdictions": ["nsw"],
        "hazard_type": "fire",
        "query_text": "x",
        "tenant_id": "t",
        "correlation_id": "c",
    }
    # below
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest.model_validate({**base, "top_k": 0})
    # above
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest.model_validate({**base, "top_k": 21})
    # within
    ok = dom.RetrievalRequest.model_validate({**base, "top_k": 1})
    assert ok.top_k == 1
    ok2 = dom.RetrievalRequest.model_validate({**base, "top_k": 20})
    assert ok2.top_k == 20


def test_jurisdictions_min_length_one() -> None:
    dom = _domain()
    base = {
        "agent_name": "MonitoringAgent",
        "jurisdictions": [],
        "hazard_type": "fire",
        "query_text": "x",
        "tenant_id": "t",
        "correlation_id": "c",
    }
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest.model_validate(base)


def test_classification_max_locked_to_official() -> None:
    dom = _domain()
    base = {
        "agent_name": "MonitoringAgent",
        "jurisdictions": ["nsw"],
        "hazard_type": "fire",
        "query_text": "x",
        "tenant_id": "t",
        "correlation_id": "c",
    }
    # default
    req = dom.RetrievalRequest.model_validate(base)
    assert req.classification_max == "OFFICIAL"
    # explicit OFFICIAL accepted
    req2 = dom.RetrievalRequest.model_validate({**base, "classification_max": "OFFICIAL"})
    assert req2.classification_max == "OFFICIAL"
    # any other value rejected
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest.model_validate({**base, "classification_max": "PROTECTED"})


def test_retrieval_result_round_trip() -> None:
    dom = _domain()
    chunk = {
        "chunk_id": "c1",
        "sha256_of_chunk": "a" * 64,
        "jurisdiction": "nsw",
        "topic": "evac",
        "page": 1,
        "licence_mode": "full-text",
        "confidence": 0.9,
        "text": "body",
        "source_url": "https://example.gov.au/x",
        "rendered_url": "/docs/corpus/nsw/evac/handbook.md#page-1",
    }
    payload = {
        "chunks": [chunk],
        "retrieval_latency_ms": 187,
        "embedding_model_id": "text-embedding-3-large",
        "corpus_build_sha": "f" * 64,
        "classification_filter_applied": False,
        "cache_hit": False,
        "alias_active_index": "corpus-v2",
    }
    res = dom.RetrievalResult.model_validate(payload)
    assert res.embedding_model_id == "text-embedding-3-large"
    assert res.alias_active_index == "corpus-v2"
    assert len(res.chunks) == 1
    assert res.chunks[0].chunk_id == "c1"


def test_retrieval_result_empty_chunks_allowed() -> None:
    """Empty result is the canonical no-grounding case (FR-RAG-AG-05)."""
    dom = _domain()
    payload = {
        "chunks": [],
        "retrieval_latency_ms": 5,
        "embedding_model_id": "text-embedding-3-large",
        "corpus_build_sha": "f" * 64,
        "classification_filter_applied": False,
        "cache_hit": False,
        "alias_active_index": "corpus-v2",
    }
    res = dom.RetrievalResult.model_validate(payload)
    assert res.chunks == []
