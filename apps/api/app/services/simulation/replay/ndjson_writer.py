"""Spec-039 T076: canonical-NDJSON writer + mandatory ``.sha256`` sidecar.

The writer is the only blessed way for Phase 5 to materialise an NDJSON
replay file. It guarantees:

  * Every record encoded via :func:`_canonical.encode_ndjson` (RFC 8785 +
    LF) so two runs with the same inputs produce byte-identical files.
  * A sidecar ``<file>.sha256`` is written next to ``<file>`` containing
    the SHA-256 of the file bytes (one line: ``<hex>  <basename>``) — the
    BSD ``shasum`` format so ``shasum -c`` works in CI.
  * Returns the digest hex string for in-process assertions (T070, T077).

Records may be either Pydantic ``CanonicalRecord`` instances (the normal
path from the feed modules) or plain ``dict`` objects (used by tests).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..feeds._canonical import encode_ndjson


def _to_dict(rec: Any) -> dict[str, Any]:
    """Coerce supported record shapes to a plain ``dict`` for canonical encoding."""
    if hasattr(rec, "model_dump"):  # Pydantic v2
        return rec.model_dump()
    if isinstance(rec, dict):
        return rec
    raise TypeError(f"replay writer only accepts dicts or pydantic models, got {type(rec).__name__}")


def write_ndjson(records: Iterable[Any], path: str | Path) -> str:
    """Write ``records`` as canonical NDJSON to ``path`` and emit a sidecar.

    Returns the SHA-256 hex digest of the written file.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with p.open("wb") as fh:
        for rec in records:
            chunk = encode_ndjson(_to_dict(rec))
            fh.write(chunk)
            h.update(chunk)
    digest = h.hexdigest()
    sidecar = p.with_suffix(p.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {p.name}\n", encoding="utf-8")
    return digest


__all__ = ["write_ndjson"]
