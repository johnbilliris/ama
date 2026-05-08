"""Manifest builder (Spec 036 T045; FR-RAG-IDX-03; spec 032 FR-AI09).

Computes the deterministic ``corpus_build_sha`` over the ``docs/corpus/`` tree
and produces a ``corpus_build.manifest.json`` describing the run for downstream
audit + provenance + cosign signing.

The manifest is the single source-of-truth for replay (``audit_record`` carries
``corpus_build_sha`` so a recommendation rendered at time T can be replayed
deterministically against the index that was active at T).

Hash strategy (deterministic; matches ``git ls-tree HEAD docs/corpus/`` style):

1. Sort every ``source.json`` under ``docs/corpus/`` by relative path.
2. For each, hash ``(relative_path, sha256_field)`` line-by-line into a
   stable canonical UTF-8 stream.
3. ``corpus_build_sha = sha256(stream)``.

Cosign keyless signing is delegated to the CI step (the ``cosign`` CLI with
GitHub OIDC credentials per spec 032 FR-AI09); this module emits the manifest
and the signature placeholder, then the CI workflow attaches the cosign output.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Manifest dataclass
# --------------------------------------------------------------------------- #


@dataclass
class IngestManifest:
    """Provenance manifest for one ingest run.

    Mirrors the fields the audit-record (FR-RAG-AG-02) and the offline-cache
    manifest (FR-RAG-LS-02) read from disk during downstream consumption.
    """

    corpus_build_sha: str
    embedding_model_id: str
    target_index: str
    alias_name: str
    chunk_count: int
    chunks_skipped_idempotent: int
    embedding_calls: int
    embedded_token_count: int
    embedding_total_cost_usd: float
    blue_green: bool
    started_at: str
    completed_at: str
    parity_gate_status: str  # "PASS" | "FAIL" | "N/A"
    parity_gate_signals: dict[str, Any] = field(default_factory=dict)
    cosign_signature: str | None = None  # populated by CI
    age_signature: str | None = None  # populated by offline_bundle

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


# --------------------------------------------------------------------------- #
# Build SHA — deterministic over ``docs/corpus/``
# --------------------------------------------------------------------------- #


def compute_corpus_build_sha(corpus_root: Path) -> str:
    """Compute the corpus-tree SHA from every ``source.json``'s ``sha256``.

    Deterministic: invocation against an unchanged tree returns the same value
    bit-for-bit. This is the idempotency key surfaced on every chunk and the
    audit record.
    """
    sources = sorted(corpus_root.rglob("source.json"))
    hasher = hashlib.sha256()
    for src in sources:
        rel = src.relative_to(corpus_root).as_posix()
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"corpus integrity error: {src}: {exc}") from exc
        sha = data.get("sha256") or data.get("hash") or ""
        line = f"{rel}|{sha}\n".encode()
        hasher.update(line)
    return hasher.hexdigest()


def iter_corpus_entries(corpus_root: Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    """Iterate over ``(source.json path, parsed entry)`` pairs sorted by path."""
    for src in sorted(corpus_root.rglob("source.json")):
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("failed to parse %s: %s", src, exc)
            continue
        yield src, data


def derive_jurisdiction_topic(source_path: Path, corpus_root: Path) -> tuple[str, str]:
    """Derive ``(jurisdiction, topic)`` from a ``source.json`` path.

    Convention: ``docs/corpus/<jurisdiction>/<topic>/source.json``.
    """
    rel = source_path.relative_to(corpus_root)
    parts = rel.parts
    if len(parts) < 3:
        raise ValueError(f"corpus path {rel} does not match <jurisdiction>/<topic>/source.json")
    jurisdiction = parts[0]
    topic = parts[1]
    return jurisdiction, topic


# --------------------------------------------------------------------------- #
# Manifest factory
# --------------------------------------------------------------------------- #


def build_manifest(
    *,
    corpus_build_sha: str,
    embedding_model_id: str,
    target_index: str,
    alias_name: str,
    chunk_count: int,
    chunks_skipped_idempotent: int,
    embedding_calls: int,
    embedded_token_count: int,
    embedding_total_cost_usd: float,
    blue_green: bool,
    started_at: datetime,
    completed_at: datetime | None = None,
    parity_gate_status: str = "N/A",
    parity_gate_signals: dict[str, Any] | None = None,
) -> IngestManifest:
    """Construct an ``IngestManifest`` with ISO-8601 UTC timestamps."""
    if completed_at is None:
        completed_at = datetime.now(tz=UTC)
    return IngestManifest(
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedding_model_id,
        target_index=target_index,
        alias_name=alias_name,
        chunk_count=chunk_count,
        chunks_skipped_idempotent=chunks_skipped_idempotent,
        embedding_calls=embedding_calls,
        embedded_token_count=embedded_token_count,
        embedding_total_cost_usd=embedding_total_cost_usd,
        blue_green=blue_green,
        started_at=started_at.astimezone(UTC).isoformat(),
        completed_at=completed_at.astimezone(UTC).isoformat(),
        parity_gate_status=parity_gate_status,
        parity_gate_signals=parity_gate_signals or {},
    )


def write_manifest(manifest: IngestManifest, *, path: Path) -> None:
    """Persist the manifest deterministically (sorted keys, UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.to_json(), encoding="utf-8")


__all__ = [
    "IngestManifest",
    "build_manifest",
    "compute_corpus_build_sha",
    "derive_jurisdiction_topic",
    "iter_corpus_entries",
    "write_manifest",
]
