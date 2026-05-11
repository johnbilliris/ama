"""spec-038 T-AA188 — pattern_id stable across re-runs but changes when citation order changes."""

from __future__ import annotations

from ama_domain import compute_pattern_id


def test_pattern_id_stable() -> None:
    a = compute_pattern_id(question_intent_cluster_id="qic-1", citation_source_ids=["x", "y", "z"])
    b = compute_pattern_id(question_intent_cluster_id="qic-1", citation_source_ids=["x", "y", "z"])
    assert a == b


def test_pattern_id_order_sensitive() -> None:
    """FR-022a-AMEND: citation ORDER is part of the pattern key."""
    a = compute_pattern_id(question_intent_cluster_id="qic-1", citation_source_ids=["x", "y", "z"])
    b = compute_pattern_id(question_intent_cluster_id="qic-1", citation_source_ids=["z", "y", "x"])
    assert a != b


def test_pattern_id_changes_with_intent_cluster() -> None:
    a = compute_pattern_id(question_intent_cluster_id="qic-1", citation_source_ids=["x"])
    b = compute_pattern_id(question_intent_cluster_id="qic-2", citation_source_ids=["x"])
    assert a != b
