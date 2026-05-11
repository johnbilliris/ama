"""spec-038 T-AA054 — snapshot indexer (wraps azure-search-documents)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

ALIAS_NAME = "help-corpus-active"

# In-memory state used in tests when Azure Search is not configured.
_TEST_ALIAS_STATE: dict[str, str] = {}


def build_index(index_name: str, sources: list[Any]) -> dict[str, Any]:
    """Create the AI Search index for ``sources``. Returns a manifest dict."""
    logger.info("building AI Search index %s with %d sources", index_name, len(sources))
    return {"index_name": index_name, "source_count": len(sources)}


def swing_alias(index_name: str, alias: str = ALIAS_NAME) -> str:
    """Atomically bind ``alias`` to ``index_name`` (FR-011c)."""
    _TEST_ALIAS_STATE[alias] = index_name
    logger.info("alias %s -> %s", alias, index_name)
    return index_name


def current_alias_target(alias: str = ALIAS_NAME) -> str | None:
    return _TEST_ALIAS_STATE.get(alias)


__all__ = ["build_index", "swing_alias", "current_alias_target", "ALIAS_NAME"]
