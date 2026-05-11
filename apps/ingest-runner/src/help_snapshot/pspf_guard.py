"""spec-038 — PSPF DENY admission gate.

Any source whose ``classification`` is above ``OFFICIAL`` is dropped before
embedding. This implements FR-011 R2 + R3 at the admission boundary; the
runtime ``content_classification_guard`` repeats the check at retrieval time
(defence in depth).
"""

from __future__ import annotations

from typing import Any

# PSPF ranks — anything strictly above 'OFFICIAL' is denied.
RANK = {
    "UNOFFICIAL": 0,
    "OFFICIAL": 1,
    "OFFICIAL:SENSITIVE": 2,
    "PROTECTED": 3,
    "SECRET": 4,
    "TOP_SECRET": 5,
}
CEILING_RANK = RANK["OFFICIAL"]


def enforce_official_ceiling(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only sources at or below the ``OFFICIAL`` ceiling."""
    return [
        s
        for s in sources
        if RANK.get((s.get("classification") or "OFFICIAL").upper().replace(" ", "_"), 99) <= CEILING_RANK
    ]


__all__ = ["enforce_official_ceiling", "RANK", "CEILING_RANK"]
