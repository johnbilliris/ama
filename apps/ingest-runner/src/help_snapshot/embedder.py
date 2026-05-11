"""spec-038 — chunk + embed help sources for the AI Search index.

Uses ``apps.agents.common.foundry_query_embedder`` when available; in
dry-run mode emits placeholder zero-vectors so unit tests can exercise the
shape without Foundry.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

EMBED_DIM = 3072  # text-embedding-3-large

CHUNK_TOKENS = 400  # ~1500 chars; defensive default — production tunes via manifest


def _split(body: str, *, max_chars: int = 1500) -> list[str]:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(buf) + len(para) + 2 > max_chars and buf:
            chunks.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        chunks.append(buf)
    return chunks


def embed_chunks(
    sources: list[dict[str, Any]],
    *,
    snapshot_id: str,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for src in sources:
        chunks = _split(src["body"])
        for i, text in enumerate(chunks):
            vec: list[float] = [0.0] * EMBED_DIM if dry_run else _embed(text)
            out.append(
                {
                    "id": f"{src['source_id']}::chunk-{i}",
                    "snapshot_id": snapshot_id,
                    "tenant_id": src.get("tenant_id", "__global__"),
                    "scope": "tenant" if src.get("tenant_id", "__global__") != "__global__" else "global",
                    "classification": src.get("classification", "OFFICIAL"),
                    "personas": src.get("personas", []),
                    "source_id": src["source_id"],
                    "title": src.get("title"),
                    "chunk_text": text,
                    "embedding": vec,
                }
            )
    return out


def _embed(text: str) -> list[float]:  # pragma: no cover — exercised by integration tests
    try:
        from apps.agents.common.foundry_query_embedder import embed_query  # type: ignore[import-not-found]

        return embed_query(text)
    except Exception:  # noqa: BLE001
        return [0.0] * EMBED_DIM


__all__ = ["embed_chunks", "EMBED_DIM"]
