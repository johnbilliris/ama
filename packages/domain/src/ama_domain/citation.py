"""Spec 036 — Citation entity (T004 stub → T072 fill).

Pydantic-v2 mirror of ``packages/schemas/spec_036/citation-envelope.json``.
Used by both recommendation cards (FR-RAG-AG-03) and simulation SSE
``citation`` events (FR-RAG-SIM-02).

Validation rules per data-model.md §Citation + R-11:
- ``snippet`` REQUIRED iff ``licence_mode == FULL_TEXT``;
  OMITTED iff ``licence_mode == METADATA_ONLY``.
- ``licence_mode == EXCLUDED`` MUST never appear (server-side filter).
- ``confidence ∈ [0.0, 1.0]`` per R-16.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .retrieval import Jurisdiction, LicenceMode


class Citation(BaseModel):
    """Citation envelope (T004 stub — T072 fills the full surface).

    Frozen + extra=forbid to match JSON Schema ``additionalProperties: false``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    jurisdiction: Jurisdiction
    topic: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]{1,128}$")
    page: int = Field(..., ge=1)
    source_url: str = Field(..., min_length=1)
    rendered_url: str = Field(..., pattern=r"^/docs/corpus/[a-z]+/[a-z0-9-]+/handbook\.md#page-\d+$")
    sha256_of_chunk: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    licence_mode: LicenceMode
    confidence: float = Field(..., ge=0.0, le=1.0)
    snippet: str | None = Field(default=None, min_length=1, max_length=800)

    @model_validator(mode="after")
    def _enforce_snippet_licence_invariant(self) -> Citation:
        # FR-RAG-IDX-02 — excluded never persisted; defence-in-depth here.
        if self.licence_mode is LicenceMode.EXCLUDED:
            raise ValueError("licence_mode 'excluded' cannot appear in a Citation")
        # R-11 conditional snippet requirement.
        if self.licence_mode is LicenceMode.FULL_TEXT and self.snippet is None:
            raise ValueError("snippet is REQUIRED when licence_mode == 'full-text'")
        if self.licence_mode is LicenceMode.METADATA_ONLY and self.snippet is not None:
            raise ValueError(
                "snippet is FORBIDDEN when licence_mode == 'metadata-only' "
                "(publisher does not grant excerpt redistribution)"
            )
        return self


__all__ = ["Citation", "LicenceMode"]
