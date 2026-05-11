"""Spec 036 — EquivalenceTestResult entity (T143, FR-RAG-FM-06).

Extends spec-033 FR-023 shape with citation-fidelity fields per
``data-model.md §EquivalenceTestResult`` (R-10, Quality-memo R2). The
pydantic-v2 model below is the canonical wire shape for the per-agent
canary gate output that is uploaded to Application Insights as the
``spec036_per_agent_canary`` custom event.

All four thresholds MUST pass for ``passed == True``; any one failing
blocks the canary flip (FR-RAG-FM-06). The result is keyed by
``(corpus_build_sha, embedding_model_id)`` so re-runs are reproducible
(SC-011, Quality-memo §test data §E2E).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Thresholds bound to the spec — duplicated here so the entity validates
# in isolation (without importing the eval-runner package, which is not
# in the domain package's dependency surface).
DECISION_EQUIVALENCE_MIN: float = 0.95
SCHEMA_EQUIVALENCE_MIN: float = 1.00
CITATION_FIDELITY_MIN: float = 0.70
VERBATIM_SOURCE_MATCH_MIN: float = 0.90


class EquivalenceTestResult(BaseModel):
    """Per-agent equivalence-test result emitted by ``apps/eval-runner``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_name: str = Field(..., min_length=1)
    golden_qa_fixture_id: str = Field(..., min_length=1)
    corpus_build_sha: str = Field(..., min_length=1)
    embedding_model_id: str = Field(..., min_length=1)
    decision_equivalence_pct: float = Field(..., ge=0.0, le=1.0)
    schema_equivalence_pct: float = Field(..., ge=0.0, le=1.0)
    citation_fidelity_pct: float = Field(..., ge=0.0, le=1.0)
    verbatim_source_match_pct: float = Field(..., ge=0.0, le=1.0)
    hallucinated_citation_count: int = Field(..., ge=0)
    passed: bool

    @model_validator(mode="after")
    def _enforce_passed_invariant(self) -> EquivalenceTestResult:
        """``passed`` MUST be the AND of all four thresholds AND zero hallucinations."""
        thresholds_met = (
            self.decision_equivalence_pct >= DECISION_EQUIVALENCE_MIN
            and self.schema_equivalence_pct >= SCHEMA_EQUIVALENCE_MIN
            and self.citation_fidelity_pct >= CITATION_FIDELITY_MIN
            and self.verbatim_source_match_pct >= VERBATIM_SOURCE_MATCH_MIN
            and self.hallucinated_citation_count == 0
        )
        if self.passed != thresholds_met:
            raise ValueError(
                f"`passed` MUST be the AND of all four thresholds + zero hallucinations: "
                f"got passed={self.passed}, thresholds_met={thresholds_met}"
            )
        return self


__all__ = [
    "CITATION_FIDELITY_MIN",
    "DECISION_EQUIVALENCE_MIN",
    "EquivalenceTestResult",
    "SCHEMA_EQUIVALENCE_MIN",
    "VERBATIM_SOURCE_MATCH_MIN",
]
