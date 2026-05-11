"""Pre-rendered Speech MP3 catalog — spec-036 T-W03 / FR-039 / FR-058.

Provides the inventory of pre-rendered ``[SIMULATION]`` watermark audio
prefixes per locale so the audio-watermark service (FR-058) can resolve a
Blob pointer at runtime instead of synthesising on demand.

Per **task description**: the production pipeline (driven by
``tools/speech_prerender.py``) uploads each locale's MP3 to a staging Blob
under the AU residency boundary (FR-062) and records the pointer in this
catalog. Until the staging upload is performed, the catalog still ships
with a non-empty entry per locale recording either:

* an explicit ``mp3_pointer`` (Blob URI) when staging upload is complete; or
* ``staging_promotion_blocker = true`` when the locale is part of the
  NT/Aboriginal expansion backlog (Yolŋu Matha, Warlpiri, Pitjantjatjara,
  Arrernte, Kriol, Torres Strait Creole) — these locales are flagged
  per CHK023 so they are not silently degraded.

Either way, every locale in :func:`required_locales` resolves to *some*
MP3 (its own or its fallback chain's first available MP3) per FR-058 step
3. The contract test (T-W04) asserts coverage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

DEFAULT_MANIFEST_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "data" / "speech_prerender_catalog.json"
)


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """A single locale's pre-render record."""

    bcp47: str
    mp3_pointer: str | None
    staging_promotion_blocker: bool
    notes: str = ""


@lru_cache(maxsize=1)
def load_catalog(path: Path | None = None) -> dict[str, CatalogEntry]:
    """Load the pre-render catalog manifest from disk."""

    target = path or DEFAULT_MANIFEST_PATH
    if not target.exists():
        return {}
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(
            f"speech_prerender_catalog.json at {target} must be a JSON array."
        )
    out: dict[str, CatalogEntry] = {}
    for raw in payload:
        if not isinstance(raw, dict):
            raise ValueError(
                f"Invalid catalog row in {target}: expected object, got {type(raw).__name__}"
            )
        out[raw["bcp47"]] = CatalogEntry(
            bcp47=raw["bcp47"],
            mp3_pointer=raw.get("mp3_pointer"),
            staging_promotion_blocker=bool(raw.get("staging_promotion_blocker", False)),
            notes=raw.get("notes", ""),
        )
    return out


def reachable(
    bcp47: str,
    *,
    fallback_chain: tuple[str, ...] | list[str],
) -> tuple[str | None, str]:
    """Return ``(mp3_pointer, source_locale)`` for the first reachable MP3.

    Walks the fallback chain in order; the first locale with a non-empty
    ``mp3_pointer`` is returned. When **no** locale on the chain has an
    MP3 pointer (e.g. backlog only), returns ``(None, bcp47)``.
    """

    catalog = load_catalog()
    chain = (bcp47, *fallback_chain) if bcp47 not in fallback_chain else tuple(fallback_chain)
    for candidate in chain:
        entry = catalog.get(candidate)
        if entry is not None and entry.mp3_pointer:
            return (entry.mp3_pointer, candidate)
    return (None, bcp47)


__all__ = [
    "CatalogEntry",
    "DEFAULT_MANIFEST_PATH",
    "load_catalog",
    "reachable",
]
