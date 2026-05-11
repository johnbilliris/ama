"""T159 — SC-017 acceptance test: 100% override audit completeness
(FR-RAG-AG-02 ext; SC-017; Plan §F-A5.5).

Replays a synthetic stream of 100 audit events and asserts:

* ``operator_override_rationale`` is present in 100% of override events.
* ``approval_workflow_state`` is present in 100% of public-warning events.

The override / public-warning fixtures are emitted via
``apps/agents/common/audit.make_inference_record`` so the wiring through
T163 is exercised end-to-end.
"""

from __future__ import annotations

from typing import Any

import pytest

audit = pytest.importorskip("common.audit")


def _make_override_event(idx: int) -> dict[str, Any]:
    return audit.make_inference_record(
        agent_name="EvacuationAgent",
        prompt_sha=f"{idx:064d}",
        model_id="gpt-4o-mini",
        model_version="2024-07-18",
        deployment_alias="ama-prod-gpt-4o-mini-v1",
        output_text_hash="0" * 64,
        output_tokens=120,
        tenant_id=f"agency-{idx % 8}",
        correlation_id=f"cor-override-{idx}",
        rag_used=True,
        embedding_model_id="text-embedding-3-large",
        corpus_build_sha="f" * 64,
        retrieved_chunks=[
            {
                "chunk_id": f"c-{idx}",
                "sha256_of_chunk": "f" * 64,
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "licence_mode": "full-text",
                "confidence": 0.84,
            }
        ],
        citations=[
            {
                "jurisdiction": "nsw",
                "topic": "evacuation-planning",
                "page": 47,
                "source_url": "https://example.gov.au/x.pdf",
                "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
                "sha256_of_chunk": "f" * 64,
                "licence_mode": "full-text",
                "confidence": 0.84,
            }
        ],
        retrieval_index_name="corpus-v3",
        operator_override_rationale=(
            f"Operator IC overrode shelter-in-place to evacuate based on local weather observations (case {idx})."
        ),
    )


def _make_public_warning_event(idx: int) -> dict[str, Any]:
    state = "pending" if idx % 2 == 0 else "approved"
    return audit.make_inference_record(
        agent_name="CommunicationAgent",
        prompt_sha=f"{idx:064d}",
        model_id="gpt-4o-mini",
        model_version="2024-07-18",
        deployment_alias="ama-prod-gpt-4o-mini-v1",
        output_text_hash="1" * 64,
        output_tokens=86,
        tenant_id=f"agency-{idx % 8}",
        correlation_id=f"cor-warning-{idx}",
        rag_used=True,
        embedding_model_id="text-embedding-3-large",
        corpus_build_sha="a" * 64,
        retrieved_chunks=[
            {
                "chunk_id": f"w-{idx}",
                "sha256_of_chunk": "a" * 64,
                "jurisdiction": "vic",
                "topic": "public-warning-templates",
                "page": 12,
                "licence_mode": "full-text",
                "confidence": 0.91,
            }
        ],
        citations=[
            {
                "jurisdiction": "vic",
                "topic": "public-warning-templates",
                "page": 12,
                "source_url": "https://emv.vic.gov.au/x.pdf",
                "rendered_url": "/docs/corpus/vic/public-warning-templates/handbook.md#page-12",
                "sha256_of_chunk": "a" * 64,
                "licence_mode": "full-text",
                "confidence": 0.91,
            }
        ],
        retrieval_index_name="corpus-v3",
        approval_workflow_state=state,
        approval_authority="ic-vic-1@ama.local" if state in {"approved", "rejected"} else None,
    )


def test_override_completeness_100pct() -> None:
    """Sample 100 override events and assert every record carries
    ``operator_override_rationale`` (SC-017)."""
    events = [_make_override_event(i) for i in range(100)]
    missing = [i for i, ev in enumerate(events) if not ev.get("operator_override_rationale")]
    assert not missing, (
        f"SC-017 violation: {len(missing)}/100 override events missing "
        f"operator_override_rationale. Indices: {missing[:5]}..."
    )


def test_public_warning_completeness_100pct() -> None:
    """Sample 50 public-warning events and assert every record carries
    ``approval_workflow_state`` (SC-017)."""
    events = [_make_public_warning_event(i) for i in range(50)]
    missing = [i for i, ev in enumerate(events) if not ev.get("approval_workflow_state")]
    assert not missing, (
        f"SC-017 violation: {len(missing)}/50 public-warning events missing "
        f"approval_workflow_state. Indices: {missing[:5]}..."
    )


def test_terminal_states_have_approval_authority() -> None:
    """ADR-14 invariant 7: every approved/rejected record carries approval_authority."""
    events = [_make_public_warning_event(i) for i in range(50)]
    terminal = [ev for ev in events if ev.get("approval_workflow_state") in {"approved", "rejected"}]
    assert terminal, "fixture must produce some terminal-state events"
    missing = [ev["correlation_id"] for ev in terminal if not ev.get("approval_authority")]
    assert not missing, f"ADR-14 violation: terminal-state events missing approval_authority: {missing[:5]}..."
