"""Spec 036 T087 — Vulnerable-population grounding helper for the
Communication agent (FR-RAG-AG-06, US8).

Before composing a public warning, the Communication agent SHOULD surface
the ATSI / CALD / Auslan / Easy-Read / TIS-National corpus entries that
shape inclusive-language and accessible-format guidance. This module
encapsulates **how** to issue that retrieval call so the pipeline stays
short and the topic slugs stay in one place.

Topic slugs (locked here so the corpus build can validate them):

* ``atsi-engagement`` — Aboriginal & Torres Strait Islander engagement
  protocols (NIAA + state-level guidance).
* ``cald-translations`` — Culturally & Linguistically Diverse community
  translations and lectern guidance.
* ``auslan-broadcast`` — Auslan interpreter sourcing + broadcast standards.
* ``easy-read`` — Easy Read accessible-format authoring rules.
* ``tis-national`` — Translating & Interpreting Service contact + escalation
  pathway.

Usage (called from Stage 5 of `pipeline.py` when the per-agent flag is on):

    from communication.grounding import gather_inclusion_chunks

    chunks = await gather_inclusion_chunks(
        retrieval_service=svc,
        jurisdictions=["nsw"],
        tenant_id=tenant_id,
        correlation_id=event.event_id,
    )

The result is the **union** of retrieval results across the 5 topic slugs,
deduplicated by ``sha256_of_chunk``. Empty result → return empty list (the
caller handles the FR-RAG-SIM-03 "no corpus match" note independently).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


# Locked topic slugs — keep in sync with corpus build manifest.
INCLUSION_TOPIC_SLUGS: tuple[str, ...] = (
    "atsi-engagement",
    "cald-translations",
    "auslan-broadcast",
    "easy-read",
    "tis-national",
)


async def gather_inclusion_chunks(
    *,
    retrieval_service: Any,
    jurisdictions: list[str],
    tenant_id: str,
    correlation_id: str,
    hazard_type: str | None = None,
    top_k_per_topic: int = 3,
) -> list[Any]:
    """Issue parallel retrieval calls for each inclusion topic.

    Returns the union of the per-topic results, deduplicated by
    ``sha256_of_chunk``. Failures on any single topic are logged and skipped
    — the rest of the topics still inform the warning composition.

    The retrieval client itself unions ``national`` + ``aidr`` server-side
    (FR-RAG-AG-04, R-03), so the caller need not include those in
    ``jurisdictions``.
    """
    try:
        from ama_domain import RetrievalRequest  # type: ignore[import-not-found]
    except ImportError:
        logger.warning("ama_domain not importable; skipping inclusion grounding")
        return []

    async def _one(topic: str) -> list[Any]:
        try:
            req = RetrievalRequest(
                agent_name="CommunicationAgent",
                jurisdictions=jurisdictions,
                hazard_type=hazard_type,
                topic_slug=topic,
                query_text=f"public warning {topic} inclusive-language",
                top_k=top_k_per_topic,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            )
            result = await retrieval_service.retrieve(req)
            return list(getattr(result, "chunks", []) or [])
        except TypeError:
            # RetrievalRequest may not accept ``topic_slug`` (older builds);
            # fall back to a plain query that mentions the topic.
            try:
                req = RetrievalRequest(
                    agent_name="CommunicationAgent",
                    jurisdictions=jurisdictions,
                    hazard_type=hazard_type,
                    query_text=f"public warning {topic} inclusive-language",
                    top_k=top_k_per_topic,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
                result = await retrieval_service.retrieve(req)
                return list(getattr(result, "chunks", []) or [])
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "communication_inclusion_topic_failed topic=%s err=%s",
                    topic,
                    exc,
                )
                return []
        except Exception as exc:  # noqa: BLE001
            logger.warning("communication_inclusion_topic_failed topic=%s err=%s", topic, exc)
            return []

    results = await asyncio.gather(*(_one(t) for t in INCLUSION_TOPIC_SLUGS))
    seen: set[str] = set()
    deduped: list[Any] = []
    for chunks in results:
        for chunk in chunks:
            sha = getattr(chunk, "sha256_of_chunk", None) or (
                chunk.get("sha256_of_chunk") if isinstance(chunk, dict) else None
            )
            if sha and sha not in seen:
                seen.add(sha)
                deduped.append(chunk)
    return deduped


__all__ = ["INCLUSION_TOPIC_SLUGS", "gather_inclusion_chunks"]
