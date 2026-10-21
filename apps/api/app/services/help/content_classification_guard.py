"""spec-038 T-AA063 / T-AA091 — content classification guard.

Defence in depth: drops any retrieval result whose ``classification`` is above
``OFFICIAL`` (the FR-011 ceiling). The admission gate at snapshot publish
already filters; this layer is a runtime safety-net so a misconfigured ingest
manifest cannot leak SENSITIVE content into a chat answer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

ALLOWED = frozenset({"OFFICIAL"})


def filter_by_classification(chunks: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    return [c for c in chunks if (c.get("classification") or "OFFICIAL") in ALLOWED]


__all__ = ["filter_by_classification", "ALLOWED"]
