"""Spec 036 T143 — EquivalenceTestResult entity test (FR-RAG-FM-06).

Validates the pydantic-v2 mirror of ``data-model.md §EquivalenceTestResult``
against the wire-shape contract:

- All four thresholds present and bounded ``[0, 1]``.
- ``hallucinated_citation_count >= 0``.
- ``passed`` is the AND of all four thresholds AND zero hallucinations.
- Reproducibility key ``(corpus_build_sha, embedding_model_id)`` carried
  per row (SC-011, Quality-memo §test data).
- ``additionalProperties: false`` semantics (extra=forbid).
"""

from __future__ import annotations

import pytest
from ama_domain import EquivalenceTestResult
from ama_domain.equivalence_test_result import (
    CITATION_FIDELITY_MIN,
    DECISION_EQUIVALENCE_MIN,
    SCHEMA_EQUIVALENCE_MIN,
    VERBATIM_SOURCE_MATCH_MIN,
)
from pydantic import ValidationError


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "agent_name": "RiskAssessmentAgent",
        "golden_qa_fixture_id": "036-risk-v3",
        "corpus_build_sha": "f9c3a8" + "0" * 58,
        "embedding_model_id": "text-embedding-3-large",
        "decision_equivalence_pct": 0.96,
        "schema_equivalence_pct": 1.00,
        "citation_fidelity_pct": 0.78,
        "verbatim_source_match_pct": 0.92,
        "hallucinated_citation_count": 0,
        "passed": True,
    }
    base.update(overrides)
    return base


def test_construction_round_trips_data_model_example() -> None:
    """The example in data-model.md §EquivalenceTestResult must validate."""
    res = EquivalenceTestResult(**_payload())
    assert res.passed is True
    assert res.agent_name == "RiskAssessmentAgent"
    assert res.corpus_build_sha.startswith("f9c3a8")
    assert res.embedding_model_id == "text-embedding-3-large"


def test_passed_must_match_threshold_and_zero_hallucination_rule() -> None:
    """passed=True with thresholds-not-met MUST raise (FR-RAG-FM-06)."""
    with pytest.raises(ValidationError, match="thresholds_met"):
        EquivalenceTestResult(**_payload(decision_equivalence_pct=0.80, passed=True))

    with pytest.raises(ValidationError, match="thresholds_met"):
        EquivalenceTestResult(**_payload(citation_fidelity_pct=0.50, passed=True))

    with pytest.raises(ValidationError, match="thresholds_met"):
        EquivalenceTestResult(**_payload(verbatim_source_match_pct=0.50, passed=True))

    with pytest.raises(ValidationError, match="thresholds_met"):
        EquivalenceTestResult(**_payload(hallucinated_citation_count=1, passed=True))

    # passed=False must match thresholds-not-met too.
    with pytest.raises(ValidationError, match="thresholds_met"):
        EquivalenceTestResult(**_payload(passed=False))


def test_passed_false_when_any_threshold_misses() -> None:
    """A consistent passed=False record (any threshold missed) MUST validate."""
    res = EquivalenceTestResult(**_payload(decision_equivalence_pct=0.90, passed=False))
    assert res.passed is False
    assert res.decision_equivalence_pct == 0.90


def test_threshold_bounds_enforced() -> None:
    """All ``*_pct`` fields MUST be in ``[0.0, 1.0]``."""
    with pytest.raises(ValidationError):
        EquivalenceTestResult(**_payload(decision_equivalence_pct=1.5))

    with pytest.raises(ValidationError):
        EquivalenceTestResult(**_payload(citation_fidelity_pct=-0.1))


def test_extra_keys_forbidden_matches_schema_additional_properties_false() -> None:
    """extra='forbid' enforces the contract's ``additionalProperties: false``."""
    with pytest.raises(ValidationError):
        EquivalenceTestResult(**_payload(unknown_field="x"))


def test_hallucinated_count_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        EquivalenceTestResult(**_payload(hallucinated_citation_count=-1))


def test_reproducibility_key_carried() -> None:
    """SC-011: every row carries the (corpus_build_sha, embedding_model_id) pair."""
    res = EquivalenceTestResult(
        **_payload(corpus_build_sha="abc123" + "0" * 58, embedding_model_id="text-embedding-3-large@1")
    )
    assert res.corpus_build_sha == "abc123" + "0" * 58
    assert res.embedding_model_id == "text-embedding-3-large@1"


def test_thresholds_match_published_constants() -> None:
    """The constants exported by the module match data-model.md (defence against drift)."""
    assert DECISION_EQUIVALENCE_MIN == 0.95
    assert SCHEMA_EQUIVALENCE_MIN == 1.00
    assert CITATION_FIDELITY_MIN == 0.70
    assert VERBATIM_SOURCE_MATCH_MIN == 0.90


def test_frozen_instance() -> None:
    """The model is frozen — fields cannot be reassigned post-construction."""
    res = EquivalenceTestResult(**_payload())
    with pytest.raises(ValidationError):
        res.passed = False  # type: ignore[misc]
