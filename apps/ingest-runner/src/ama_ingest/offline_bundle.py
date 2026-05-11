"""Offline cache bundle (Spec 036 T047; FR-RAG-LS-02; R-04, R-07).

Builds the per-build offline-cache bundle delivered to Field-Coordinator-aligned
devices. Conforms to ``contracts/offline-cache-manifest.json``:

- ≤ 500 MB total (``size_bytes_total`` <= ``524_288_000``).
- 14-day hard TTL (``ttl_days``).
- 11-day stale-warning crossover (``stale_warning_days``).
- Single ``embedding_model_id`` (matches the index R-05 invariant).
- Dual-signed envelope: cosign keyless (Sigstore + GitHub OIDC) **and**
  age-encrypted detached signature. Both signatures are produced by the
  upstream CI step; this module emits manifest + signature placeholders that
  the CI workflow attaches before publishing.

Selection priority (per Field Coordinator persona memo + FR-RAG-LS-02):

1. AIDR core doctrine (highest density of multi-jurisdiction reference).
2. National-level handbooks.
3. Per-jurisdiction "most-cited" handbooks — hazard thresholds, AIIMS
   span-of-control, evacuation-centre setup, sector boundaries.

Selection iterates in priority order and stops as soon as adding the next
chunk would breach the 500 MB cap; the dropped tail is logged so persona-memo
prioritisation can be re-balanced if the manifest churns.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants — bound by ``contracts/offline-cache-manifest.json``.
# --------------------------------------------------------------------------- #

MANIFEST_VERSION: int = 1
TTL_DAYS: int = 14
STALE_WARNING_DAYS: int = 11
SIZE_BYTES_CAP: int = 524_288_000  # 500 × 1024 × 1024

#: Jurisdiction priority — AIDR, national, then alpha-sorted state/territory.
JURISDICTION_PRIORITY: tuple[str, ...] = (
    "aidr",
    "national",
    "act",
    "nsw",
    "nt",
    "qld",
    "sa",
    "tas",
    "vic",
    "wa",
)


# --------------------------------------------------------------------------- #
# Dataclasses mirroring the manifest contract.
# --------------------------------------------------------------------------- #


@dataclass
class ManifestEntry:
    chunk_id: str
    jurisdiction: str
    topic: str
    page: int
    sha256_of_chunk: str
    licence_mode: str  # "full-text" | "metadata-only"
    byte_offset: int
    byte_length: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ManifestSignatures:
    cosign_keyless: str
    age_detached: str
    cosign_signed_at: str | None = None
    age_recipients: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "cosign_keyless": self.cosign_keyless,
            "age_detached": self.age_detached,
        }
        if self.cosign_signed_at is not None:
            out["cosign_signed_at"] = self.cosign_signed_at
        if self.age_recipients:
            out["age_recipients"] = list(self.age_recipients)
        return out


@dataclass
class OfflineCacheManifest:
    """In-memory mirror of ``contracts/offline-cache-manifest.json``."""

    corpus_build_sha: str
    embedding_model_id: str
    entries: list[ManifestEntry]
    size_bytes_total: int
    signatures: ManifestSignatures
    generated_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    version: int = MANIFEST_VERSION
    ttl_days: int = TTL_DAYS
    stale_warning_days: int = STALE_WARNING_DAYS

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "corpus_build_sha": self.corpus_build_sha,
            "ttl_days": self.ttl_days,
            "stale_warning_days": self.stale_warning_days,
            "embedding_model_id": self.embedding_model_id,
            "entries": [e.to_dict() for e in self.entries],
            "size_bytes_total": self.size_bytes_total,
            "signatures": self.signatures.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


# --------------------------------------------------------------------------- #
# Builder
# --------------------------------------------------------------------------- #


def build_offline_bundle(
    *,
    chunks: list[dict[str, Any]],
    corpus_build_sha: str,
    embedding_model_id: str,
    cosign_keyless: str = "<placeholder-cosign-signature>",
    age_detached: str = "<placeholder-age-detached>",
    age_recipients: list[str] | None = None,
    size_cap_bytes: int = SIZE_BYTES_CAP,
) -> OfflineCacheManifest:
    """Construct an offline-cache manifest under the size cap.

    Args:
        chunks: Iterable of ``{chunk_id, jurisdiction, topic, page,
            sha256_of_chunk, licence_mode, byte_length}`` dicts (the indexer
            output). ``byte_length`` is used to compute the size cap.
        corpus_build_sha: Pin to the corpus build under which the bundle
            was produced (FR-RAG-LS-02 replay-parity invariant).
        embedding_model_id: MUST match every chunk's ``embedding_model_id``;
            ingest fails on a mismatch (R-05 single-model invariant).
        cosign_keyless: Cosign-keyless signature string; defaults to a
            placeholder that the CI step replaces.
        age_detached: ``age``-encrypted detached signature (R-07 fail-closed).
        age_recipients: Optional list of age recipients (informational).
        size_cap_bytes: Hard cap (500 MB); chunks beyond this are dropped.

    Returns:
        ``OfflineCacheManifest`` ready to serialise + sign.
    """
    if not chunks:
        raise ValueError("offline bundle requires ≥ 1 chunk")

    # Sort by jurisdiction priority then page, deterministically.
    priority = {j: i for i, j in enumerate(JURISDICTION_PRIORITY)}
    sorted_chunks = sorted(
        chunks,
        key=lambda c: (
            priority.get(c.get("jurisdiction", ""), len(priority)),
            c.get("topic", ""),
            int(c.get("page", 1)),
        ),
    )

    entries: list[ManifestEntry] = []
    running_offset = 0
    dropped = 0
    for chunk in sorted_chunks:
        if chunk.get("licence_mode") == "excluded":
            # Defence in depth: licence_filter should already have stripped
            # these but we never want one in a Field Coordinator's bundle.
            continue
        if chunk.get("embedding_model_id") and chunk["embedding_model_id"] != embedding_model_id:
            raise ValueError(
                "offline bundle requires homogeneous embedding_model_id "
                f"(expected {embedding_model_id!r}, "
                f"got {chunk['embedding_model_id']!r})"
            )
        byte_length = int(chunk.get("byte_length") or _estimate_bytes(chunk))
        if running_offset + byte_length > size_cap_bytes:
            dropped += 1
            continue
        entries.append(
            ManifestEntry(
                chunk_id=str(chunk["chunk_id"]),
                jurisdiction=str(chunk["jurisdiction"]),
                topic=str(chunk["topic"]),
                page=int(chunk["page"]),
                sha256_of_chunk=str(chunk["sha256_of_chunk"]),
                licence_mode=str(chunk["licence_mode"]),
                byte_offset=running_offset,
                byte_length=byte_length,
            )
        )
        running_offset += byte_length

    if dropped:
        logger.warning(
            "offline bundle truncated: %d chunks dropped (size cap=%d bytes)",
            dropped,
            size_cap_bytes,
        )

    if not entries:
        raise ValueError("offline bundle empty after size-cap filtering — increase cap or shed lower-priority entries")

    return OfflineCacheManifest(
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedding_model_id,
        entries=entries,
        size_bytes_total=running_offset,
        signatures=ManifestSignatures(
            cosign_keyless=cosign_keyless,
            age_detached=age_detached,
            cosign_signed_at=datetime.now(tz=UTC).isoformat(),
            age_recipients=list(age_recipients or []),
        ),
    )


def write_offline_bundle(
    manifest: OfflineCacheManifest,
    *,
    path: Path,
) -> None:
    """Write the manifest deterministically (sorted keys, UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.to_json(), encoding="utf-8")


def _estimate_bytes(chunk: dict[str, Any]) -> int:
    """Estimate the on-disk size of a chunk for the size-cap check."""
    text_len = len((chunk.get("text") or chunk.get("summary") or "").encode("utf-8"))
    embedding_len = (
        len(chunk.get("embedding") or []) * 4  # float32 = 4 bytes
    )
    return text_len + embedding_len + 256  # 256 bytes overhead per entry


__all__ = [
    "JURISDICTION_PRIORITY",
    "MANIFEST_VERSION",
    "ManifestEntry",
    "ManifestSignatures",
    "OfflineCacheManifest",
    "SIZE_BYTES_CAP",
    "STALE_WARNING_DAYS",
    "TTL_DAYS",
    "build_offline_bundle",
    "write_offline_bundle",
]
