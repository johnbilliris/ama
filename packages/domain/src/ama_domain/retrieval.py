"""Spec 036 — RetrievalRequest, RetrievalResult, RetrievedChunk, Jurisdiction (T004 stub → T071 fill).

Scaffolded by T004 with the **enum types** and bare class shells that allow the
schema-mirror contract test (T005) and forbidden-import lints to compile.
T071 fills the field surfaces; T063 entity test enforces invariants.

Source of truth: ``specs/036-foundry-rag-grounding/data-model.md`` §RetrievalRequest, §RetrievalResult.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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
# T004 stubs — minimal class shells. Field surfaces land in T071.
# --------------------------------------------------------------------------- #


class RetrievedChunk(BaseModel):
    """Single chunk returned by ``RetrievalService.retrieve``.

    Stub — full field set lands in T071 per data-model.md §Chunk projection.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str = Field(..., min_length=1)
    sha256_of_chunk: str = Field(..., pattern=r"^[a-f0-9]{64}$")


class RetrievalRequest(BaseModel):
    """Input to ``RetrievalService.retrieve`` (FR-RAG-AG-01, R-03).

    Stub — full field set lands in T071. Validation rules per data-model.md §RetrievalRequest.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_name: str = Field(..., min_length=1)
    jurisdictions: list[Jurisdiction] = Field(..., min_length=1)
    query_text: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    classification_max: str = Field(default="OFFICIAL")


class RetrievalResult(BaseModel):
    """Output of ``RetrievalService.retrieve`` (FR-RAG-AG-01).

    Stub — full field set lands in T071.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunks: list[RetrievedChunk] = Field(default_factory=list)
    embedding_model_id: str = Field(..., min_length=1)
    corpus_build_sha: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    alias_active_index: str = Field(..., min_length=1)


__all__ = [
    "Jurisdiction",
    "LicenceMode",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievedChunk",
]
