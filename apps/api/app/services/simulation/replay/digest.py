"""Spec-039 T077: replay digest sidecar verification.

Each canonical NDJSON file under ``fixtures/sim_replays/`` is paired with
a ``<file>.sha256`` sidecar (BSD ``shasum`` format: ``<hex>  <basename>``).

:func:`verify_sidecar` recomputes the file's SHA-256 and compares against
the sidecar; mismatch raises :class:`DigestMismatchError`. CI runs this on
every committed replay (T161 / Phase 7) and the CLI runs it after each
replay write (T078).
"""

from __future__ import annotations

import hashlib
from pathlib import Path


class DigestMismatchError(RuntimeError):
    """Raised when a replay file's SHA-256 disagrees with its sidecar."""


def _read_sidecar_digest(sidecar: Path) -> str:
    raw = sidecar.read_text(encoding="utf-8").strip()
    if not raw:
        raise DigestMismatchError(f"{sidecar}: empty sidecar")
    head = raw.splitlines()[0].strip()
    digest = head.split()[0]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise DigestMismatchError(f"{sidecar}: sidecar does not contain a 64-char lowercase hex digest")
    return digest


def compute_sha256(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sidecar(path: str | Path) -> str:
    """Verify ``<path>`` matches its ``<path>.sha256`` sidecar.

    Returns the digest on success; raises :class:`DigestMismatchError` on
    failure.
    """
    p = Path(path)
    sidecar = p.with_suffix(p.suffix + ".sha256")
    if not sidecar.exists():
        raise DigestMismatchError(f"{sidecar}: sidecar missing")
    expected = _read_sidecar_digest(sidecar)
    actual = compute_sha256(p)
    if expected != actual:
        raise DigestMismatchError(f"{p}: sha256 mismatch — expected {expected}, got {actual}")
    return actual


__all__ = ["DigestMismatchError", "compute_sha256", "verify_sidecar"]
