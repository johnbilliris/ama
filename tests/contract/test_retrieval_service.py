"""T060 — Contract test for ``RetrievalService`` (Spec 036 / FR-RAG-AG-01, FR-RAG-AG-04, R-03, R-06).

Asserts the Protocol shape declared by ``contracts/retrieval-service.md`` §1
and the semantics in §2 (jurisdiction union, RRF fusion default 0.7/0.3,
empty-result handling, classification ceiling).

This test goes RED before T071/T075/T076/T077 land and GREEN immediately after.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import Mock

import pytest


def _retrieval_module() -> Any:
    """Import the retrieval-client seam — REQUIRED to exist post-T075."""
    import importlib

    return importlib.import_module("common.retrieval_client")


def _domain_module() -> Any:
    import importlib

    return importlib.import_module("ama_domain")


def test_live_search_client_supports_the_configured_corpus_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    import azure.search.documents.aio

    constructor = Mock()
    monkeypatch.setattr(azure.search.documents.aio, "SearchClient", constructor)
    credential = Mock()
    service = _retrieval_module().AzureSearchRetrievalService(
        endpoint="https://search.example.test", credential=credential, index_alias="corpus"
    )
    assert service._ensure_search_client() is constructor.return_value
    constructor.assert_called_once_with(
        endpoint="https://search.example.test",
        index_name="corpus",
        credential=credential,
        api_version="2024-05-01-preview",
    )


# --------------------------------------------------------------------------- #
# T071 — domain entities
# --------------------------------------------------------------------------- #


def test_retrieval_request_full_field_set() -> None:
    """RetrievalRequest MUST carry the full surface defined in data-model.md §RetrievalRequest."""
    dom = _domain_module()
    req = dom.RetrievalRequest(
        agent_name="RiskAssessmentAgent",
        jurisdictions=["nsw"],
        hazard_type="bushfire",
        query_text="aiims span of control",
        top_k=5,
        classification_max="OFFICIAL",
        tenant_id="agency-nsw-rfs",
        correlation_id="550e8400-e29b-41d4-a716-446655440000",
    )
    assert req.agent_name == "RiskAssessmentAgent"
    assert req.jurisdictions == [dom.Jurisdiction.NSW]
    assert req.hazard_type == "bushfire"
    assert req.top_k == 5
    assert req.tenant_id == "agency-nsw-rfs"
    assert req.correlation_id == "550e8400-e29b-41d4-a716-446655440000"


def test_retrieval_request_top_k_bounds() -> None:
    """top_k MUST be ∈ [1, 20] per data-model.md §RetrievalRequest."""
    dom = _domain_module()
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest(
            agent_name="MonitoringAgent",
            jurisdictions=["nsw"],
            hazard_type="fire",
            query_text="x",
            top_k=0,
            tenant_id="t",
            correlation_id="c",
        )
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest(
            agent_name="MonitoringAgent",
            jurisdictions=["nsw"],
            hazard_type="fire",
            query_text="x",
            top_k=21,
            tenant_id="t",
            correlation_id="c",
        )


def test_retrieval_request_jurisdictions_required() -> None:
    """jurisdictions[] MUST have min_length=1."""
    dom = _domain_module()
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.RetrievalRequest(
            agent_name="MonitoringAgent",
            jurisdictions=[],
            hazard_type="fire",
            query_text="x",
            tenant_id="t",
            correlation_id="c",
        )


def test_retrieval_request_classification_ceiling_locked_to_official() -> None:
    """classification_max MUST equal 'OFFICIAL' (FR-RAG-NS-07; contract §2.5)."""
    dom = _domain_module()
    req = dom.RetrievalRequest(
        agent_name="MonitoringAgent",
        jurisdictions=["national"],
        hazard_type="fire",
        query_text="x",
        tenant_id="t",
        correlation_id="c",
    )
    assert req.classification_max == "OFFICIAL"


# --------------------------------------------------------------------------- #
# T060 — Protocol shape, Fake stub, jurisdiction union, empty-result, ceiling
# --------------------------------------------------------------------------- #


def test_retrieval_service_protocol_exposed() -> None:
    mod = _retrieval_module()
    for name in (
        "RetrievalService",
        "FakeRetrievalService",
        "AzureSearchRetrievalService",
        "ClassificationCeilingError",
    ):
        assert hasattr(mod, name), f"common.retrieval_client missing {name!r}"


def test_fake_retrieval_service_conforms_to_protocol() -> None:
    mod = _retrieval_module()
    fake = mod.FakeRetrievalService()
    assert isinstance(fake, mod.RetrievalService)


def _build_chunk(dom: Any, **overrides: Any) -> Any:
    base = {
        "chunk_id": "c1",
        "sha256_of_chunk": "a" * 64,
        "jurisdiction": dom.Jurisdiction.NSW,
        "topic": "evacuation-planning",
        "page": 1,
        "licence_mode": dom.LicenceMode.FULL_TEXT,
        "confidence": 0.8,
        "text": "snippet body",
        "source_url": "https://example.gov.au/x",
        "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-1",
    }
    base.update(overrides)
    return dom.RetrievedChunk(**base)


def test_jurisdiction_union_applied_in_fake() -> None:
    """Fake stub MUST honour the jurisdiction-union semantics (contract §6).

    Input ``jurisdictions=["nsw"]`` → match chunks from nsw, national, aidr;
    other states (vic, qld, …) MUST be excluded.
    """
    mod = _retrieval_module()
    dom = _domain_module()
    chunks = [
        _build_chunk(
            dom,
            chunk_id="n1",
            sha256_of_chunk="b" * 64,
            jurisdiction=dom.Jurisdiction.NATIONAL,
            rendered_url="/docs/corpus/national/aiims/handbook.md#page-12",
            topic="aiims",
            page=12,
        ),
        _build_chunk(
            dom,
            chunk_id="v1",
            sha256_of_chunk="c" * 64,
            jurisdiction=dom.Jurisdiction.VIC,
            rendered_url="/docs/corpus/vic/evacuation-planning/handbook.md#page-3",
            page=3,
        ),
        _build_chunk(
            dom,
            chunk_id="a1",
            sha256_of_chunk="d" * 64,
            jurisdiction=dom.Jurisdiction.AIDR,
            rendered_url="/docs/corpus/aidr/handbooks/handbook.md#page-5",
            topic="handbooks",
            page=5,
        ),
    ]
    fake = mod.FakeRetrievalService(fixture=chunks)
    req = dom.RetrievalRequest(
        agent_name="RiskAssessmentAgent",
        jurisdictions=["nsw"],
        hazard_type="bushfire",
        query_text="aiims span of control",
        top_k=5,
        tenant_id="t",
        correlation_id="c",
    )
    result = asyncio.run(fake.retrieve(req))
    ids = [c.chunk_id for c in result.chunks]
    assert "n1" in ids
    assert "a1" in ids
    assert "v1" not in ids


def test_empty_result_handling() -> None:
    """No matches → return ``RetrievalResult(chunks=[], …)`` (contract §2.3)."""
    mod = _retrieval_module()
    dom = _domain_module()
    fake = mod.FakeRetrievalService(fixture=[])
    req = dom.RetrievalRequest(
        agent_name="MonitoringAgent",
        jurisdictions=["nsw"],
        hazard_type="fire",
        query_text="x",
        tenant_id="t",
        correlation_id="c",
    )
    result = asyncio.run(fake.retrieve(req))
    assert result.chunks == []


def test_classification_ceiling_error_raised_above_official() -> None:
    """``classification_max != 'OFFICIAL'`` MUST raise ClassificationCeilingError (FR-RAG-NS-07)."""
    mod = _retrieval_module()
    dom = _domain_module()
    fake = mod.FakeRetrievalService()

    # Bypass Pydantic frozen Literal["OFFICIAL"] guard by mutating a dict-source.
    # The raise MUST come from the service, not the request model — defence-in-depth.
    class _ProtoReq:
        agent_name = "MonitoringAgent"
        jurisdictions = [dom.Jurisdiction.NSW]
        hazard_type = "fire"
        query_text = "x"
        top_k = 5
        classification_max = "PROTECTED"
        tenant_id = "t"
        correlation_id = "c"

    with pytest.raises(mod.ClassificationCeilingError):
        asyncio.run(fake.retrieve(_ProtoReq()))


def test_rrf_default_weights() -> None:
    """The RRF default weights MUST be vector=0.7, lexical=0.3 per R-06."""
    mod = _retrieval_module()
    assert mod.RRF_VECTOR_WEIGHT_DEFAULT == 0.7
    assert mod.RRF_LEXICAL_WEIGHT_DEFAULT == 0.3
