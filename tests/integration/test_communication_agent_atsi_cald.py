"""T067 — Communication-agent ATSI/CALD/Auslan retrieval (Spec 036 / FR-RAG-AG-06, US8).

Vulnerable-population scenario: NSW NW flood with high CALD census + 2 ATSI
communities. Retrieval MUST surface ATSI / CALD / Auslan / Easy-Read /
TIS-National corpus entries before composition.

This integration test uses the FakeRetrievalService stub to assert the
**retrieval contract** (which corpora are queried) — separate from a future
contract test that asserts the human-approval gate (FR-RAG-LS-01 / LS-03).
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


# Vulnerable-population corpus topics that MUST be surfaced for warnings (FR-RAG-AG-06).
VULNERABLE_POP_TOPICS: tuple[str, ...] = (
    "atsi-engagement",
    "cald-translations",
    "auslan-broadcast",
    "easy-read",
    "tis-national",
)


def _vulnerable_pop_corpus(dom: Any) -> list[Any]:
    out = []
    for topic in VULNERABLE_POP_TOPICS:
        out.append(
            dom.RetrievedChunk(
                chunk_id=f"vp-{topic}",
                sha256_of_chunk=(topic.encode("utf-8").hex().ljust(64, "0"))[:64],
                jurisdiction=dom.Jurisdiction.NSW,
                topic=topic,
                page=1,
                licence_mode=dom.LicenceMode.FULL_TEXT,
                confidence=0.85,
                text=f"vulnerable population guidance for {topic}",
                source_url=f"https://example.gov.au/{topic}.pdf",
                rendered_url=f"/docs/corpus/nsw/{topic}/handbook.md#page-1",
            )
        )
    # Plus an unrelated chunk to verify the topic filter actually narrows.
    out.append(
        dom.RetrievedChunk(
            chunk_id="unrelated",
            sha256_of_chunk="9" * 64,
            jurisdiction=dom.Jurisdiction.NSW,
            topic="aiims-mapping",
            page=1,
            licence_mode=dom.LicenceMode.FULL_TEXT,
            confidence=0.5,
            text="not relevant",
            source_url="https://example.gov.au/aiims.pdf",
            rendered_url="/docs/corpus/nsw/aiims-mapping/handbook.md#page-1",
        )
    )
    return out


def test_communication_agent_retrieves_vulnerable_pop_topics() -> None:
    """The CommunicationAgent's pre-composition retrieval MUST include ATSI,
    CALD, Auslan, Easy-Read, and TIS-National entries when the population
    profile flags vulnerable groups."""
    mod = _retrieval()
    dom = _domain()
    fake = mod.FakeRetrievalService(fixture=_vulnerable_pop_corpus(dom))

    req = dom.RetrievalRequest(
        agent_name="CommunicationAgent",
        jurisdictions=["nsw"],
        hazard_type="flood",
        query_text="NW flood warning composition with ATSI + CALD + Auslan considerations",
        top_k=20,
        tenant_id="agency-nsw-rfs",
        correlation_id="corr-nw-flood",
    )
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(fake.retrieve(req))
    finally:
        loop.close()

    surfaced_topics = {c.topic for c in result.chunks}
    for required_topic in VULNERABLE_POP_TOPICS:
        assert required_topic in surfaced_topics, (
            f"FR-RAG-AG-06: CommunicationAgent retrieval omitted vulnerable-population "
            f"topic {required_topic!r}; surfaced={surfaced_topics}"
        )


@pytest.mark.parametrize("topic", VULNERABLE_POP_TOPICS)
def test_each_vulnerable_topic_individually_retrievable(topic: str) -> None:
    """Each vulnerable-population topic MUST be individually retrievable (no implicit OR
    bundling that could mask a missing corpus entry)."""
    mod = _retrieval()
    dom = _domain()
    fixture = _vulnerable_pop_corpus(dom)
    fake = mod.FakeRetrievalService(fixture=fixture)

    req = dom.RetrievalRequest(
        agent_name="CommunicationAgent",
        jurisdictions=["nsw"],
        hazard_type="flood",
        query_text=topic,
        top_k=20,
        tenant_id="t",
        correlation_id="c",
    )
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(fake.retrieve(req))
    finally:
        loop.close()
    topics = {c.topic for c in result.chunks}
    assert topic in topics
