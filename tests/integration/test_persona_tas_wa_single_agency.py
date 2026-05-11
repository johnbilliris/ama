"""Spec 036 T103 — TAS SES + WA DFES single-agency edge-case persona scenario (FR-RAG-AG-04, SC-010).

DFES-WA is the single-agency hazard handler in Western Australia (the only
state without a separate RFS sub-unit). The retrieval client must NOT
silently conflate DFES-WA results with the NSW RFS / VIC CFA / QLD QFES
sub-units, even though the topic vocabulary overlaps heavily.

The test exercises the FakeRetrievalService with a fixture that includes
DFES-WA + NSW RFS + VIC CFA chunks, then asserts that a query scoped to
``["wa"]`` returns only DFES-WA / national / aidr — never NSW or VIC
chunks.

TAS SES is exercised similarly for territorial integrity (TAS doesn't share
fire-management infrastructure with VIC; the retrieval scoping must hold).
"""

from __future__ import annotations

import asyncio
import hashlib

import pytest


def _retrieval():
    import importlib

    return importlib.import_module("common.retrieval_client")


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _chunk(dom, *, jurisdiction: str, topic: str, chunk_id: str):
    sha = hashlib.sha256(chunk_id.encode("utf-8")).hexdigest()
    j_enum = getattr(dom.Jurisdiction, jurisdiction.upper())
    return dom.RetrievedChunk(
        chunk_id=chunk_id,
        sha256_of_chunk=sha,
        jurisdiction=j_enum,
        topic=topic,
        page=1,
        licence_mode=dom.LicenceMode.METADATA_ONLY,
        confidence=0.8,
        summary="placeholder",
        source_url=f"https://{jurisdiction}.example.gov.au/{topic}.pdf",
        rendered_url=f"/docs/corpus/{jurisdiction}/{topic}/handbook.md#page-1",
    )


def _make_request(dom, jurisdiction: str, query: str):
    return dom.RetrievalRequest(
        agent_name="ResourceAllocationAgent",
        jurisdictions=[jurisdiction],
        hazard_type="bushfire",
        query_text=query,
        top_k=10,
        tenant_id="t",
        correlation_id="c",
    )


def test_dfes_wa_does_not_silently_conflate_with_nsw_rfs() -> None:
    """SC-010: a WA-scoped query must NOT surface NSW RFS / VIC CFA results."""
    mod = _retrieval()
    dom = _domain()
    fixture = [
        _chunk(dom, jurisdiction="wa", topic="resource-management", chunk_id="dfes-wa-1"),
        _chunk(dom, jurisdiction="nsw", topic="resource-management", chunk_id="rfs-nsw-1"),
        _chunk(dom, jurisdiction="vic", topic="resource-management", chunk_id="cfa-vic-1"),
        _chunk(dom, jurisdiction="national", topic="resource-management", chunk_id="agd-national-1"),
        _chunk(dom, jurisdiction="aidr", topic="resource-management", chunk_id="aidr-1"),
    ]
    fake = mod.FakeRetrievalService(fixture=fixture)
    req = _make_request(dom, "wa", "bushfire surge allocation")
    result = asyncio.run(fake.retrieve(req))
    ids = [c.chunk_id for c in result.chunks]
    assert "dfes-wa-1" in ids
    assert "agd-national-1" in ids
    assert "aidr-1" in ids
    # The single-agency invariant: NSW + VIC chunks are NOT in the WA result set.
    assert "rfs-nsw-1" not in ids
    assert "cfa-vic-1" not in ids


def test_tas_ses_does_not_pull_vic_cfa() -> None:
    mod = _retrieval()
    dom = _domain()
    fixture = [
        _chunk(dom, jurisdiction="tas", topic="storm-surge", chunk_id="ses-tas-1"),
        _chunk(dom, jurisdiction="vic", topic="storm-surge", chunk_id="ses-vic-1"),
        _chunk(dom, jurisdiction="national", topic="storm-surge", chunk_id="agd-national-2"),
    ]
    fake = mod.FakeRetrievalService(fixture=fixture)
    req = _make_request(dom, "tas", "storm-surge response")
    result = asyncio.run(fake.retrieve(req))
    ids = [c.chunk_id for c in result.chunks]
    assert "ses-tas-1" in ids
    assert "agd-national-2" in ids
    assert "ses-vic-1" not in ids


@pytest.mark.parametrize(
    "scoped_jurisdiction,foreign_chunk_id",
    [
        ("wa", "rfs-nsw-1"),
        ("wa", "cfa-vic-1"),
        ("wa", "ses-tas-1"),
        ("tas", "rfs-nsw-1"),
        ("tas", "cfa-vic-1"),
    ],
)
def test_no_silent_cross_state_conflation(scoped_jurisdiction: str, foreign_chunk_id: str) -> None:
    mod = _retrieval()
    dom = _domain()
    fixture = [
        _chunk(dom, jurisdiction="wa", topic="resource-management", chunk_id="dfes-wa-1"),
        _chunk(dom, jurisdiction="nsw", topic="resource-management", chunk_id="rfs-nsw-1"),
        _chunk(dom, jurisdiction="vic", topic="resource-management", chunk_id="cfa-vic-1"),
        _chunk(dom, jurisdiction="tas", topic="resource-management", chunk_id="ses-tas-1"),
        _chunk(dom, jurisdiction="national", topic="resource-management", chunk_id="national-1"),
    ]
    fake = mod.FakeRetrievalService(fixture=fixture)
    req = _make_request(dom, scoped_jurisdiction, "resource allocation")
    result = asyncio.run(fake.retrieve(req))
    ids = [c.chunk_id for c in result.chunks]
    assert foreign_chunk_id not in ids, (
        f"FR-RAG-AG-04 violation: query scoped to {scoped_jurisdiction!r} surfaced foreign chunk {foreign_chunk_id!r}"
    )
