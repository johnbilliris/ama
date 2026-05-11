"""T061 — Contract test for the Citation envelope (Spec 036 / FR-RAG-AG-03, FR-RAG-SIM-02, R-11, R-16).

Round-trip JSON Schema 2020-12 validation against
``packages/schemas/spec_036/citation-envelope.json`` and pydantic-v2 mirror in
``ama_domain.citation``. Covers the snippet/licence_mode invariant (R-11) and
the confidence range (R-16).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "packages" / "schemas" / "spec_036" / "citation-envelope.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _full_text_example() -> dict:
    return {
        "jurisdiction": "nsw",
        "topic": "evacuation-planning",
        "page": 47,
        "source_url": "https://www.rfs.nsw.gov.au/__data/assets/pdf_file/0009/evac-plan.pdf",
        "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
        "sha256_of_chunk": "f9c3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a26",
        "licence_mode": "full-text",
        "confidence": 0.84,
        "snippet": "When the area is deemed safe, the Incident Controller authorises return of evacuees…",
    }


def _metadata_only_example() -> dict:
    return {
        "jurisdiction": "national",
        "topic": "aiims",
        "page": 12,
        "source_url": "https://www.afac.com.au/docs/default-source/doctrine/aiims-handbook.pdf",
        "rendered_url": "/docs/corpus/national/aiims/handbook.md#page-12",
        "sha256_of_chunk": "0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5",
        "licence_mode": "metadata-only",
        "confidence": 0.71,
    }


# --------------------------------------------------------------------------- #
# JSON Schema validation
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("example", [_full_text_example(), _metadata_only_example()])
def test_envelope_examples_validate_against_schema(example: dict) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    jsonschema.validate(instance=example, schema=schema)


def test_full_text_requires_snippet() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    bad = _full_text_example()
    bad.pop("snippet")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_metadata_only_forbids_snippet() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    bad = _metadata_only_example()
    bad["snippet"] = "verboten"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_excluded_licence_mode_forbidden() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    bad = _full_text_example()
    bad["licence_mode"] = "excluded"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_confidence_bounds_enforced() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    bad = _full_text_example()
    bad["confidence"] = 1.5
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_required_fields_present() -> None:
    """The schema MUST require all the fields named in FR-RAG-AG-03."""
    schema = _load_schema()
    required = set(schema["required"])
    assert {
        "jurisdiction",
        "topic",
        "page",
        "source_url",
        "rendered_url",
        "sha256_of_chunk",
        "licence_mode",
        "confidence",
    } <= required


# --------------------------------------------------------------------------- #
# pydantic-v2 mirror parity
# --------------------------------------------------------------------------- #


def test_pydantic_round_trip_full_text() -> None:
    from ama_domain import Citation

    payload = _full_text_example()
    cit = Citation.model_validate(payload)
    dumped = cit.model_dump(mode="json", exclude_none=True)
    assert dumped == payload


def test_pydantic_round_trip_metadata_only() -> None:
    from ama_domain import Citation

    payload = _metadata_only_example()
    cit = Citation.model_validate(payload)
    dumped = cit.model_dump(mode="json", exclude_none=True)
    assert dumped == payload
