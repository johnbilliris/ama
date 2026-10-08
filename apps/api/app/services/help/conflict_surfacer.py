"""spec-038 T-AA062 — conflict surfacer (FR-016)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Conflict:
    citations: tuple[str, ...]
    notice: str


def detect_conflict(retrieved_chunks: Iterable[Mapping[str, object]]) -> Conflict | None:
    """Heuristic: a conflict exists when ≥2 chunks tagged with mutually-
    exclusive ``stance`` values cover the same ``topic``.

    Inputs are chunk dicts with fields ``citation_id``, ``topic``, ``stance``.
    """
    by_topic: dict[str, dict[str, list[str]]] = {}
    for c in retrieved_chunks:
        topic = c.get("topic")
        stance = c.get("stance")
        cid = c.get("citation_id")
        if not (topic and stance and cid):
            continue
        if not isinstance(topic, str) or not isinstance(stance, str) or not isinstance(cid, str):
            raise ValueError("Retrieved conflict fields topic, stance, and citation_id must be strings")
        by_topic.setdefault(topic, {}).setdefault(stance, []).append(cid)
    for topic, stances in by_topic.items():
        if len(stances) >= 2:
            cits = tuple(c for v in stances.values() for c in v)
            return Conflict(
                citations=cits,
                notice=(
                    f"Sources disagree on '{topic}'. Review the cited material before acting; "
                    "if uncertain, contact your support handoff."
                ),
            )
    return None


__all__ = ["Conflict", "detect_conflict"]
