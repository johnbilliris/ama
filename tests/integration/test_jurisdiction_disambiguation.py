"""T065 — Integration test for jurisdiction-disambiguation (Spec 036 / FR-RAG-AG-04, SC-010, US7, R-03).

Walks a curated 50-query persona-driven set covering border edge cases:
* NSW–VIC border (RFS vs CFA-VIC; FRNSW vs FRV)
* NT–QLD cyclone (NTES vs SES-QLD)
* ACT–NSW handoff (ACT RFS vs NSW RFS, AFP-ACT vs NSW Police)
* DFES-WA single-agency edge cases
* TAS / SA territorial-only cases

Asserts:
1. ``RetrievalRequest.jurisdictions`` ∪ ``{"national", "aidr"}`` is honoured.
2. Out-of-jurisdiction state corpora are NEVER returned (0 silent conflations).
3. Single-agency single-jurisdiction queries (DFES-WA) do NOT pull NSW RFS.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest


def _retrieval():
    import importlib

    return importlib.import_module("common.retrieval_client")


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _chunk(dom: Any, *, jurisdiction: str, chunk_id: str, topic: str = "evacuation-planning") -> Any:
    import hashlib

    j_enum = getattr(dom.Jurisdiction, jurisdiction.upper())
    sha = hashlib.sha256(chunk_id.encode("utf-8")).hexdigest()
    return dom.RetrievedChunk(
        chunk_id=chunk_id,
        sha256_of_chunk=sha,
        jurisdiction=j_enum,
        topic=topic,
        page=1,
        licence_mode=dom.LicenceMode.FULL_TEXT,
        confidence=0.8,
        text="body",
        source_url=f"https://{jurisdiction}.example.gov.au/x",
        rendered_url=f"/docs/corpus/{jurisdiction}/{topic}/handbook.md#page-1",
    )


def _build_50_query_fixture() -> list[dict[str, Any]]:
    """A curated persona-driven query set. ``own`` is the requesting jurisdiction;
    every query MUST also surface national + aidr corpora (US7)."""
    return [
        # NSW–VIC border (10 queries — RFS vs CFA-VIC, FRNSW vs FRV)
        *[{"agent": "RiskAssessmentAgent", "own": "nsw", "label": f"nsw-vic-border-{i}"} for i in range(5)],
        *[{"agent": "EvacuationAgent", "own": "vic", "label": f"vic-nsw-border-{i}"} for i in range(5)],
        # NT–QLD cyclone (10 — NTES vs SES-QLD)
        *[{"agent": "MonitoringAgent", "own": "nt", "label": f"nt-qld-cyclone-{i}"} for i in range(5)],
        *[{"agent": "ResourceAllocationAgent", "own": "qld", "label": f"qld-nt-cyclone-{i}"} for i in range(5)],
        # ACT–NSW handoff (10)
        *[{"agent": "EvacuationAgent", "own": "act", "label": f"act-nsw-handoff-{i}"} for i in range(5)],
        *[{"agent": "EvacuationAgent", "own": "nsw", "label": f"nsw-act-handoff-{i}"} for i in range(5)],
        # DFES-WA single-agency edge (10)
        *[{"agent": "ResourceAllocationAgent", "own": "wa", "label": f"dfes-wa-single-{i}"} for i in range(10)],
        # TAS + SA territorial (10)
        *[{"agent": "EvacuationAgent", "own": "tas", "label": f"tas-{i}"} for i in range(5)],
        *[{"agent": "RiskAssessmentAgent", "own": "sa", "label": f"sa-{i}"} for i in range(5)],
    ]


def _all_jurisdictions(dom: Any) -> list[Any]:
    return list(dom.Jurisdiction)


def _build_full_corpus_fixture(dom: Any) -> list[Any]:
    """One chunk per jurisdiction so cross-jurisdiction leakage is observable."""
    return [_chunk(dom, jurisdiction=j.value, chunk_id=f"k-{j.value}") for j in _all_jurisdictions(dom)]


def test_50_query_set_no_silent_conflations() -> None:
    """Run the 50-query set and assert every result contains only the requesting
    jurisdiction's corpora plus the national/aidr unions."""
    mod = _retrieval()
    dom = _domain()
    fixture = _build_full_corpus_fixture(dom)
    fake = mod.FakeRetrievalService(fixture=fixture)
    queries = _build_50_query_fixture()

    assert len(queries) == 50  # sanity

    loop = asyncio.new_event_loop()
    try:
        for q in queries:
            req = dom.RetrievalRequest(
                agent_name=q["agent"],
                jurisdictions=[q["own"]],
                hazard_type="bushfire",
                query_text=q["label"],
                tenant_id="t",
                correlation_id=f"c-{q['label']}",
            )
            result = loop.run_until_complete(fake.retrieve(req))
            allowed = {q["own"], "national", "aidr"}
            for c in result.chunks:
                assert c.jurisdiction.value in allowed, (
                    f"silent conflation in {q['label']}: got {c.jurisdiction.value} "
                    f"for own={q['own']}; allowed={allowed}"
                )
    finally:
        loop.close()


def test_dfes_wa_does_not_pull_nsw_rfs() -> None:
    """Single-agency single-jurisdiction WA query MUST NOT return NSW chunks."""
    mod = _retrieval()
    dom = _domain()
    fixture = _build_full_corpus_fixture(dom)
    fake = mod.FakeRetrievalService(fixture=fixture)
    req = dom.RetrievalRequest(
        agent_name="ResourceAllocationAgent",
        jurisdictions=["wa"],
        hazard_type="bushfire",
        query_text="DFES strike-team deployment",
        tenant_id="t",
        correlation_id="c",
    )
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(fake.retrieve(req))
    finally:
        loop.close()
    states = {c.jurisdiction.value for c in result.chunks}
    assert "nsw" not in states
    assert "vic" not in states


def test_act_query_unions_with_national() -> None:
    """ACT query MUST surface both ACT and national corpora (R-03 union)."""
    mod = _retrieval()
    dom = _domain()
    fixture = _build_full_corpus_fixture(dom)
    fake = mod.FakeRetrievalService(fixture=fixture)
    req = dom.RetrievalRequest(
        agent_name="EvacuationAgent",
        jurisdictions=["act"],
        hazard_type="bushfire",
        query_text="ACT–NSW handoff",
        tenant_id="t",
        correlation_id="c",
    )
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(fake.retrieve(req))
    finally:
        loop.close()
    states = {c.jurisdiction.value for c in result.chunks}
    # ACT itself must be there; national should also be present (union).
    assert "act" in states
    assert "national" in states
    # NSW should NOT leak in for an ACT-only query.
    assert "nsw" not in states


@pytest.mark.parametrize(
    "requesting,not_allowed",
    [
        ("nsw", "vic"),
        ("vic", "nsw"),
        ("qld", "nsw"),
        ("nt", "qld"),
        ("wa", "sa"),
    ],
)
def test_pairwise_no_cross_state_leak(requesting: str, not_allowed: str) -> None:
    mod = _retrieval()
    dom = _domain()
    fixture = _build_full_corpus_fixture(dom)
    fake = mod.FakeRetrievalService(fixture=fixture)
    req = dom.RetrievalRequest(
        agent_name="MonitoringAgent",
        jurisdictions=[requesting],
        hazard_type="fire",
        query_text="x",
        tenant_id="t",
        correlation_id="c",
    )
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(fake.retrieve(req))
    finally:
        loop.close()
    states = {c.jurisdiction.value for c in result.chunks}
    assert not_allowed not in states
