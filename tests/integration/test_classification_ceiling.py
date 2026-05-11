"""T070 — Classification-ceiling integration test (Spec 036 / FR-RAG-NS-07, contracts/retrieval-service.md §2.5).

Asserts that ``RetrievalService.retrieve(...)`` raises
``ClassificationCeilingError`` when ``classification_max != "OFFICIAL"``.

The pydantic ``RetrievalRequest`` enforces the ceiling at the entity boundary
via ``Literal["OFFICIAL"]`` — but the retrieval client MUST also enforce it
defensively so non-pydantic callers (e.g. the simulation Controller wiring an
inline shape) cannot bypass the ceiling.
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


class _ProtoReq:
    """Inline duck-typed request — bypasses the pydantic Literal guard."""

    agent_name = "MonitoringAgent"
    jurisdictions: list = []
    hazard_type = "fire"
    query_text = "x"
    top_k = 5
    classification_max = "OFFICIAL"
    tenant_id = "t"
    correlation_id = "c"


def _ok_request(dom: Any) -> Any:
    return dom.RetrievalRequest(
        agent_name="MonitoringAgent",
        jurisdictions=["nsw"],
        hazard_type="fire",
        query_text="x",
        tenant_id="t",
        correlation_id="c",
    )


def test_official_classification_passes_through() -> None:
    mod = _retrieval()
    dom = _domain()
    fake = mod.FakeRetrievalService()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(fake.retrieve(_ok_request(dom)))
    finally:
        loop.close()
    assert result.chunks == []  # empty fixture; passes the ceiling


@pytest.mark.parametrize("ceiling", ["PROTECTED", "SECRET", "TOP SECRET", "OFFICIAL: SENSITIVE"])
def test_above_official_raises_classification_ceiling_error(ceiling: str) -> None:
    mod = _retrieval()
    dom = _domain()
    fake = mod.FakeRetrievalService()

    class _Req(_ProtoReq):
        jurisdictions = [dom.Jurisdiction.NSW]
        classification_max = ceiling  # bypasses the pydantic Literal["OFFICIAL"] guard

    loop = asyncio.new_event_loop()
    try:
        with pytest.raises(mod.ClassificationCeilingError):
            loop.run_until_complete(fake.retrieve(_Req()))
    finally:
        loop.close()


def test_classification_ceiling_error_carries_attempted_value() -> None:
    """The error MUST carry the attempted classification value for audit."""
    mod = _retrieval()
    dom = _domain()
    fake = mod.FakeRetrievalService()

    class _Req(_ProtoReq):
        jurisdictions = [dom.Jurisdiction.NSW]
        classification_max = "PROTECTED"

    loop = asyncio.new_event_loop()
    try:
        with pytest.raises(mod.ClassificationCeilingError) as exc_info:
            loop.run_until_complete(fake.retrieve(_Req()))
    finally:
        loop.close()
    assert "PROTECTED" in str(exc_info.value)
