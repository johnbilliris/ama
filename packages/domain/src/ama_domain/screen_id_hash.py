"""spec-038 T-AA051 — deterministic ``screen_id_hash`` computer (FR-010a).

Hash formula::

    sha256(route_id + "|" + "|".join(callout.anchor_dom_path
                                     for callout in sorted_by_callout_number))

Per FR-010a the input is an *ordered set of DOM-element fingerprints*.
**Do not** lexicographically sort the anchors — sort the parent ``Callout``
list by ``Callout.number`` ascending and emit anchors in that order. Reordering
the callout numbers therefore changes the hash, which the build pipeline uses
as the staleness signal.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .annotated_screenshot import Callout


def compute_screen_id_hash(route_id: str, callouts: Iterable[Callout]) -> str:
    """Return the SHA-256 hex digest used as ``AnnotatedScreenshot.screen_id_hash``."""
    if not route_id:
        raise ValueError("route_id is required")
    ordered = sorted(callouts, key=lambda c: c.number)
    payload = route_id + "|" + "|".join(c.anchor_dom_path for c in ordered)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["compute_screen_id_hash"]
