"""Deterministic summariser adapter (T-S10). FR-030 / Research D6."""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Iterable

logger = logging.getLogger(__name__)


def _fallback_summary(blocks: Iterable[str]) -> str:
    joined = "\n\n".join(b.strip() for b in blocks if b and b.strip())
    return textwrap.dedent(joined).strip()


def summarise_blocks(blocks: list[str], *, max_chars: int = 800) -> str:
    raw = _fallback_summary(blocks)
    try:
        from apps.agents.common import llm_client  # noqa: WPS433

        if hasattr(llm_client, "summarise"):
            text = llm_client.summarise(raw, max_chars=max_chars)  # type: ignore[attr-defined]
            if isinstance(text, str) and text.strip():
                return text.strip()
    except Exception as exc:  # pragma: no cover
        logger.debug("LLM summariser unavailable; using deterministic fallback: %s", exc)
    return raw[:max_chars]
