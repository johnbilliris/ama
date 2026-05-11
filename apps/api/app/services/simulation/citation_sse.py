"""Spec 036 T088 — SSE ``citation`` event marshalling for the Simulation chat
channel (FR-RAG-SIM-02, FR-RAG-SIM-03, R-11).

The Simulation Controller streams chat completion tokens as SSE
``message`` events. Spec 036 adds a parallel ``citation`` event channel:

  event: citation
  data: {"turn_id": "...", "citations": [...], "note": "..."}\n\n

* **Grounded turn** (FR-RAG-SIM-02): ``format_citation_event`` packs the
  filtered citation list (post-hallucination filter; T080) into a single
  event keyed by ``turn_id``.
* **Empty-result turn** (FR-RAG-SIM-03): ``format_empty_citations_event``
  emits ``citations: []`` and the operator-facing note
  ``"no corpus match — recommend operator verification"``.

Each citation in the wire payload conforms to
``packages/schemas/spec_036/citation-envelope.json`` (R-11). The
``Citation`` pydantic-v2 model already enforces the licence / snippet
invariant — we just dump it.

This module is **the only** SSE marshaller for citation events; the
controller_service imports it directly.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

# Operator-facing note for the empty-grounding case (FR-RAG-SIM-03). Kept as
# a module-level constant so audit + UI components can reference the same
# string verbatim.
EMPTY_RESULT_NOTE: str = "no corpus match — recommend operator verification"


def _citation_to_dict(citation: Any) -> dict[str, Any]:
    """Coerce a Citation (pydantic) or already-dict object into the wire shape."""
    if hasattr(citation, "model_dump"):
        # pydantic v2
        return citation.model_dump(mode="json", by_alias=False, exclude_none=True)
    if isinstance(citation, dict):
        return citation
    raise TypeError(f"Unsupported citation type: {type(citation)!r}")


def _sse_frame(event: str, data: dict[str, Any]) -> str:
    """Encode a single SSE frame.

    SSE wire format:
        event: <name>\n
        data: <json>\n
        \n
    """
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'), ensure_ascii=False)}\n\n"


def format_citation_event(*, turn_id: str, citations: Iterable[Any]) -> str:
    """Format a populated ``citation`` SSE event for the simulation channel.

    Args:
        turn_id: Stable identifier for the chat turn the citations belong to;
            allows the UI to associate each citation with the streamed
            completion that produced it (FR-RAG-SIM-02).
        citations: Iterable of ``Citation`` (or dict) objects, **already**
            filtered through the hallucinated-citation suppression
            (T080 / FR-RAG-AG-05). The marshaller assumes its input is the
            "allowed" list — no re-filtering happens here.

    Returns:
        SSE wire frame (``event: citation\\ndata: <json>\\n\\n``).
    """
    payload = {
        "turn_id": turn_id,
        "citations": [_citation_to_dict(c) for c in citations],
    }
    return _sse_frame("citation", payload)


def format_empty_citations_event(*, turn_id: str) -> str:
    """Format the ``citation`` SSE event for an empty-grounding turn (FR-RAG-SIM-03).

    Emits ``citations: []`` plus the operator-facing
    "no corpus match — recommend operator verification" note. The UI surfaces
    this note as a degraded-confidence indicator on the chat panel.
    """
    payload = {
        "turn_id": turn_id,
        "citations": [],
        "note": EMPTY_RESULT_NOTE,
    }
    return _sse_frame("citation", payload)


__all__ = [
    "EMPTY_RESULT_NOTE",
    "format_citation_event",
    "format_empty_citations_event",
]
