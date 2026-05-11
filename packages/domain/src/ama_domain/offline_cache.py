"""Spec 036 — OfflineCacheManifest entity (T004 stub → T074 fill).

Pydantic-v2 mirror of ``packages/schemas/spec_036/offline-cache-manifest.json``.
Built by ``apps/ingest-runner/src/ama_ingest/offline_bundle.py`` (T047);
consumed by ``apps/agents/common/offline_cache.py`` (T129).

Validation rules per FR-RAG-LS-02 + R-07:
- ``ttl_days == 14`` (hard expiry).
- ``stale_warning_days == 11`` (soft warning).
- ``size_bytes_total ≤ 524_288_000`` (500 MB cap).
- ``signatures`` MUST carry both ``cosign_keyless`` and ``age_detached``;
  verification fails closed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .retrieval import Jurisdiction, LicenceMode


class OfflineCacheEntry(BaseModel):
    """One chunk index entry inside the offline bundle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str = Field(..., min_length=1)
    jurisdiction: Jurisdiction
    topic: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)
    sha256_of_chunk: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    licence_mode: Literal[LicenceMode.FULL_TEXT, LicenceMode.METADATA_ONLY]
    byte_offset: int = Field(..., ge=0)
    byte_length: int = Field(..., ge=1)


class OfflineCacheSignatures(BaseModel):
    """Dual-signature envelope. BOTH MUST be present and valid (R-07)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cosign_keyless: str = Field(..., min_length=1)
    age_detached: str = Field(..., min_length=1)
    cosign_signed_at: datetime | None = None
    age_recipients: list[str] | None = None


class OfflineCacheManifest(BaseModel):
    """Spec 036 offline cache manifest. T004 stub — T074 fills final surface."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1] = 1
    generated_at: datetime
    corpus_build_sha: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    ttl_days: Literal[14] = 14
    stale_warning_days: Literal[11] = 11
    embedding_model_id: str = Field(..., min_length=1)
    entries: list[OfflineCacheEntry] = Field(..., min_length=1)
    size_bytes_total: int = Field(..., ge=1, le=524_288_000)
    signatures: OfflineCacheSignatures


__all__ = [
    "OfflineCacheEntry",
    "OfflineCacheManifest",
    "OfflineCacheSignatures",
]
