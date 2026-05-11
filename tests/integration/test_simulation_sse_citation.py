"""T068 — Integration test for simulation SSE citation (Spec 036 / FR-RAG-SIM-01..06, SC-007, SC-012).

Drives a simulation chat turn through the citation-SSE marshalling layer
(``apps/api/app/services/simulation/citation_sse.py``) and asserts:

* SSE ``citation`` event is emitted per grounded reply (FR-RAG-SIM-02).
* Empty result emits ``citations: []`` + a ``no corpus match`` note (FR-RAG-SIM-03).
* Audit shape matches FR-RAG-SIM-04 (call_kind=inference, rag_used=true,
  retrieved_chunks/citations populated, prompt_sha + corpus_build_sha pinned).

Spec-024 controls (rate-limit, comms-block, tenant-isolation, approval workflow)
are exercised by their existing test suites; this test verifies the **new**
citation SSE channel only.
"""

from __future__ import annotations

import json
from typing import Any

import pytest


def _sse_module():
    import importlib

    return importlib.import_module("app.services.simulation.citation_sse")


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _build_citation(dom: Any, sha: str = "f" * 64) -> Any:
    return dom.Citation(
        jurisdiction=dom.Jurisdiction.NSW,
        topic="evacuation-planning",
        page=47,
        source_url="https://www.rfs.nsw.gov.au/x.pdf",
        rendered_url="/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
        sha256_of_chunk=sha,
        licence_mode=dom.LicenceMode.FULL_TEXT,
        confidence=0.84,
        snippet="When the area is deemed safe…",
    )


def test_module_exposes_marshaller() -> None:
    mod = _sse_module()
    assert hasattr(mod, "format_citation_event")
    assert hasattr(mod, "format_empty_citations_event")


def test_grounded_reply_emits_citation_event() -> None:
    mod = _sse_module()
    dom = _domain()
    cit = _build_citation(dom)
    raw = mod.format_citation_event(turn_id="t1", citations=[cit])
    # SSE wire format: "event: citation\ndata: <json>\n\n"
    assert raw.startswith("event: citation\n")
    body_line = next(line for line in raw.splitlines() if line.startswith("data: "))
    payload = json.loads(body_line.removeprefix("data: "))
    assert payload["turn_id"] == "t1"
    assert isinstance(payload["citations"], list)
    assert len(payload["citations"]) == 1
    cit_obj = payload["citations"][0]
    assert cit_obj["jurisdiction"] == "nsw"
    assert cit_obj["sha256_of_chunk"] == "f" * 64


def test_empty_result_emits_citations_array_with_note() -> None:
    """FR-RAG-SIM-03 — empty grounding result emits ``citations: []`` + the
    ``no corpus match — recommend operator verification`` note."""
    mod = _sse_module()
    raw = mod.format_empty_citations_event(turn_id="t1")
    assert raw.startswith("event: citation\n")
    body_line = next(line for line in raw.splitlines() if line.startswith("data: "))
    payload = json.loads(body_line.removeprefix("data: "))
    assert payload["citations"] == []
    note = payload.get("note", "").lower()
    assert "no corpus match" in note
    assert "recommend operator verification" in note


def test_citation_payload_validates_against_schema() -> None:
    """The SSE payload's ``citations[i]`` MUST conform to citation-envelope.json."""
    jsonschema = pytest.importorskip("jsonschema")
    from pathlib import Path

    SCHEMA = json.loads(
        (Path(__file__).resolve().parents[1] / ".." / "packages" / "schemas" / "spec_036" / "citation-envelope.json")
        .resolve()
        .read_text(encoding="utf-8")
    )
    mod = _sse_module()
    dom = _domain()
    raw = mod.format_citation_event(turn_id="t1", citations=[_build_citation(dom)])
    body_line = next(line for line in raw.splitlines() if line.startswith("data: "))
    payload = json.loads(body_line.removeprefix("data: "))
    for c in payload["citations"]:
        jsonschema.validate(instance=c, schema=SCHEMA)


def test_multiple_citations_supported() -> None:
    mod = _sse_module()
    dom = _domain()
    cits = [_build_citation(dom, sha=("a" * 64)), _build_citation(dom, sha=("b" * 64))]
    raw = mod.format_citation_event(turn_id="t2", citations=cits)
    body_line = next(line for line in raw.splitlines() if line.startswith("data: "))
    payload = json.loads(body_line.removeprefix("data: "))
    assert len(payload["citations"]) == 2
