"""Spec 036 — RetrievalRequest, RetrievalResult, RetrievedChunk, Jurisdiction (T071 — full surface).

Pydantic-v2 mirror of ``specs/036-foundry-rag-grounding/data-model.md``
§RetrievalRequest / §RetrievalResult / §Chunk-projection.

Validation rules enforced here:

* ``RetrievalRequest.jurisdictions`` MUST be non-empty (FR-RAG-AG-04 / R-03).
* ``RetrievalRequest.top_k ∈ [1, 20]`` (data-model.md §RetrievalRequest).
* ``RetrievalRequest.classification_max == "OFFICIAL"`` (FR-RAG-NS-07 — the
  pydantic Literal locks the entity boundary; the retrieval client raises
  ``ClassificationCeilingError`` defensively for duck-typed callers).
* ``RetrievedChunk`` carries the union of fields needed by both
  recommendation cards (FR-RAG-AG-03) and the simulation SSE channel
  (FR-RAG-SIM-02): ``rendered_url``, ``source_url``, ``confidence``, etc.
* ``text`` is conditional on ``licence_mode == FULL_TEXT`` and ``summary`` is
  conditional on ``licence_mode == METADATA_ONLY`` (R-11; mirrors the
  Citation envelope rule for the chunk projection).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Jurisdiction(StrEnum):
    """Issuing jurisdiction enum — matches contracts/citation-envelope.json."""

    ACT = "act"
    NSW = "nsw"
    NT = "nt"
    QLD = "qld"
    SA = "sa"
    TAS = "tas"
    VIC = "vic"
    WA = "wa"
    NATIONAL = "national"
    AIDR = "aidr"


class LicenceMode(StrEnum):
    """Licence mode for a CorpusEntry / Chunk / Citation (FR-RAG-IDX-02; R-11).

    ``EXCLUDED`` is never persisted to the index and never appears in a Citation
    (server-side filter at retrieval per FR-RAG-IDX-02). The enum value is kept
    here for the licence_filter pipeline (T043).
    """

    FULL_TEXT = "full-text"
    METADATA_ONLY = "metadata-only"
    EXCLUDED = "excluded"


# --------------------------------------------------------------------------- #
# RetrievedChunk — projection consumed by both citations and grounded prompts
# --------------------------------------------------------------------------- #


class RetrievedChunk(BaseModel):
    """Single chunk returned by ``RetrievalService.retrieve``.

    Field set mirrors ``contracts/retrieval-service.md`` §1 (RetrievedChunk) and
    is rich enough to generate either a Citation envelope (FR-RAG-AG-03) or a
    grounded prompt segment (FR-RAG-AG-01).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str = Field(..., min_length=1)
    sha256_of_chunk: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    jurisdiction: Jurisdiction
    topic: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)
    licence_mode: Literal[LicenceMode.FULL_TEXT, LicenceMode.METADATA_ONLY]
    confidence: float = Field(..., ge=0.0, le=1.0)
    text: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    source_url: str = Field(..., min_length=1)
    rendered_url: str = Field(
        ...,
        pattern=r"^/docs/corpus/[a-z]+/[a-z0-9-]+/handbook\.md#page-\d+$",
    )

    @model_validator(mode="after")
    def _enforce_licence_text_invariant(self) -> RetrievedChunk:
        # R-11: text iff full-text; summary iff metadata-only. Defence-in-depth
        # at the chunk boundary (the index pipeline is the primary enforcement).
        if self.licence_mode is LicenceMode.FULL_TEXT and self.text is None:
            raise ValueError("RetrievedChunk.text is REQUIRED when licence_mode == 'full-text'")
        if self.licence_mode is LicenceMode.METADATA_ONLY and self.summary is None:
            raise ValueError("RetrievedChunk.summary is REQUIRED when licence_mode == 'metadata-only'")
        return self


# --------------------------------------------------------------------------- #
# RetrievalRequest — caller contract (FR-RAG-AG-01)
# --------------------------------------------------------------------------- #


_AgentName = Literal[
    "MonitoringAgent",
    "RiskAssessmentAgent",
    "EvacuationAgent",
    "ResourceAllocationAgent",
    "CommunicationAgent",
    "SimulationController",
]


class RetrievalRequest(BaseModel):
    """Input to ``RetrievalService.retrieve`` (FR-RAG-AG-01, R-03)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_name: _AgentName
    jurisdictions: list[Jurisdiction] = Field(..., min_length=1)
    hazard_type: str = Field(..., min_length=1)
    query_text: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    classification_max: Literal["OFFICIAL"] = "OFFICIAL"
    tenant_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)


# --------------------------------------------------------------------------- #
# RetrievalResult — service output
# --------------------------------------------------------------------------- #


class RetrievalResult(BaseModel):
    """Output of ``RetrievalService.retrieve`` (FR-RAG-AG-01).

    ``chunks`` is empty if no relevant content matched (US3 acceptance scenario
    3). Callers MUST NOT fabricate citations from an empty result
    (FR-RAG-AG-05, FR-RAG-SIM-03).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunks: list[RetrievedChunk] = Field(default_factory=list)
    retrieval_latency_ms: int = Field(default=0, ge=0)
    embedding_model_id: str = Field(..., min_length=1)
    corpus_build_sha: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    classification_filter_applied: bool = False
    cache_hit: bool = False
    alias_active_index: str = Field(..., min_length=1)


__all__ = [
    "Jurisdiction",
    "LicenceMode",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievedChunk",
]
