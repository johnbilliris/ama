"""T062 — Contract test for the AuditRecord (LLM-call) shape (Spec 036 / FR-RAG-AG-02, FR-RAG-SIM-04, R-13).

Round-trip JSON Schema 2020-12 validation against
``packages/schemas/spec_036/audit-record-llm-call.json``. Exercises:

* the grounded-inference happy path (rag_used=true with retrieved_chunks +
  citations),
* the RAG-OPTOUT path (rag_used=false → rag_optout_reason + adr_pointer),
* the embedding path (call_kind=embedding → no prompt_sha, no chunks),
* the gateway-deny path (gateway_decision=deny → gateway_deny_reason).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "packages" / "schemas" / "spec_036"
SCHEMA_PATH = SCHEMA_DIR / "audit-record-llm-call.json"
CITATION_PATH = SCHEMA_DIR / "citation-envelope.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _make_validator(schema: dict):
    """Build a JSON Schema 2020-12 validator that can resolve the local
    ``./citation-envelope.json`` $ref against the on-disk mirror.
    """
    import jsonschema  # type: ignore[import-untyped]
    from referencing import Registry, Resource  # type: ignore[import-untyped]
    from referencing.jsonschema import DRAFT202012  # type: ignore[import-untyped]

    citation_schema = json.loads(CITATION_PATH.read_text(encoding="utf-8"))
    registry = Registry().with_resources(
        [
            ("./citation-envelope.json", Resource(contents=citation_schema, specification=DRAFT202012)),
            ("citation-envelope.json", Resource(contents=citation_schema, specification=DRAFT202012)),
        ]
    )
    return jsonschema.Draft202012Validator(schema, registry=registry)


def _grounded_inference_example() -> dict:
    return {
        "call_id": "f3e2d1c0-a9b8-7c6d-5e4f-3a2b1c0d9e8f",
        "timestamp_utc": "2026-05-15T03:42:11Z",
        "agent_name": "RiskAssessmentAgent",
        "chat_turn_index": None,
        "call_kind": "inference",
        "prompt_sha": "9c1f3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a2",
        "model_id": "gpt-4o-mini",
        "model_version": "2024-07-18",
        "deployment_alias": "ama-prod-gpt-4o-mini-v1",
        "embedding_model_id": "text-embedding-3-large",
        "corpus_build_sha": "f9c3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a26",
        "retrieved_chunks": [
            {
                "chunk_id": "abc-123",
                "sha256_of_chunk": "f9c3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a26",
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "licence_mode": "full-text",
                "confidence": 0.84,
            }
        ],
        "citations": [
            {
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "source_url": "https://www.rfs.nsw.gov.au/x.pdf",
                "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
                "sha256_of_chunk": "f9c3a8b27da4e9f1c8b93726c4e1a9bc15e3a4d8f9c7b62e5a1d3c8f7e9b4a26",
                "licence_mode": "full-text",
                "confidence": 0.84,
                "snippet": "When the area is deemed safe…",
            }
        ],
        "rag_used": True,
        "gateway_decision": "allow",
        "hallucinated_citation_count": 0,
        "output_tokens": 412,
        "output_text_hash": "1a2b3c4d5e6f70819203a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5",
        "tenant_id": "agency-nsw-rfs",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        # F-A5 / ADR-16 invariant 6: rag_used == true → retrieval_index_name required.
        "retrieval_index_name": "corpus-v3",
    }


def _optout_example() -> dict:
    return {
        "call_id": "11223344-5566-7788-99aa-bbccddeeff00",
        "timestamp_utc": "2026-05-15T03:43:00Z",
        "agent_name": "DependencyNotifierAgent",
        "call_kind": "inference",
        "prompt_sha": "0" * 64,
        "model_id": "gpt-4o-mini",
        "model_version": "2024-07-18",
        "deployment_alias": "ama-prod-gpt-4o-mini-v1",
        "rag_used": False,
        "rag_optout_reason": "structured-signal-pipeline",
        "adr_pointer": "docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md",
        "retrieved_chunks": [],
        "gateway_decision": "allow",
        "hallucinated_citation_count": 0,
        "output_tokens": 86,
        "output_text_hash": "deadbeef" + "0" * 56,
        "tenant_id": "agency-nsw-rfs",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
    }


def _embedding_example() -> dict:
    return {
        "call_id": "aaaa1111-bbbb-2222-cccc-333344445555",
        "timestamp_utc": "2026-05-15T03:44:00Z",
        "agent_name": "SimulationController",
        "call_kind": "embedding",
        "model_id": "text-embedding-3-large",
        "model_version": "2024-01-25",
        "deployment_alias": "ama-prod-embed-v1",
        "embedding_model_id": "text-embedding-3-large",
        "rag_used": False,
        "gateway_decision": "allow",
        "hallucinated_citation_count": 0,
        "output_tokens": 0,
        "output_text_hash": "0" * 64,
        "tenant_id": "agency-nsw-rfs",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440002",
    }


# --------------------------------------------------------------------------- #
# Schema validation — happy paths
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "example",
    [_grounded_inference_example(), _optout_example(), _embedding_example()],
    ids=["grounded_inference", "optout", "embedding"],
)
def test_examples_validate_against_schema(example: dict) -> None:
    pytest.importorskip("jsonschema")
    pytest.importorskip("referencing")
    schema = _load_schema()
    validator = _make_validator(schema)
    validator.validate(example)


# --------------------------------------------------------------------------- #
# Invariants
# --------------------------------------------------------------------------- #


def test_rag_used_true_requires_retrieved_chunks() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    pytest.importorskip("referencing")
    schema = _load_schema()
    validator = _make_validator(schema)
    bad = _grounded_inference_example()
    bad["retrieved_chunks"] = []
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad)


def test_rag_used_false_requires_optout_reason_and_adr() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    pytest.importorskip("referencing")
    schema = _load_schema()
    validator = _make_validator(schema)
    bad = _optout_example()
    bad.pop("rag_optout_reason")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad)
    bad2 = _optout_example()
    bad2.pop("adr_pointer")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad2)


def test_embedding_call_kind_forbids_prompt_sha() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    pytest.importorskip("referencing")
    schema = _load_schema()
    validator = _make_validator(schema)
    bad = _embedding_example()
    bad["prompt_sha"] = "1" * 64
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad)


def test_inference_call_kind_requires_prompt_sha() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    pytest.importorskip("referencing")
    schema = _load_schema()
    validator = _make_validator(schema)
    bad = _grounded_inference_example()
    bad.pop("prompt_sha")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad)


def test_gateway_deny_requires_reason() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    pytest.importorskip("referencing")
    schema = _load_schema()
    validator = _make_validator(schema)
    bad = _grounded_inference_example()
    bad["gateway_decision"] = "deny"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad)


def test_required_top_level_fields() -> None:
    schema = _load_schema()
    required = set(schema["required"])
    expected = {
        "call_id",
        "timestamp_utc",
        "agent_name",
        "call_kind",
        "model_id",
        "model_version",
        "deployment_alias",
        "rag_used",
        "gateway_decision",
        "hallucinated_citation_count",
        "output_tokens",
        "output_text_hash",
        "tenant_id",
        "correlation_id",
    }
    assert expected <= required, f"missing required fields: {expected - required}"


def test_optout_reasons_match_fr_rag_ns_01_to_09() -> None:
    """rag_optout_reason enum maps 1:1 to FR-RAG-NS-01..09 (data-model.md §AuditRecord)."""
    schema = _load_schema()
    enum = set(schema["properties"]["rag_optout_reason"]["enum"])
    expected = {
        "structured-signal-pipeline",
        "bom-live-feed",
        "ga-live-feed",
        "planning-collection",
        "logistics-transactional",
        "scenario-execution",
        "classified-content",
        "lint-required-marker",
        "observer-auditor-replay",
    }
    assert enum == expected
