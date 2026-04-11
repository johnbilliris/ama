"""Handoff deduplication service — TTL-based in-memory cache.

Uses an LRU-ordered dictionary with time-based expiry. The dedup window
is configurable via ``HANDOFF_DEDUP_WINDOW_MINUTES`` (default 10).
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class HandoffDeduplicator:
    """Time-bounded idempotency checker for incoming handoffs."""

    def __init__(self, window_minutes: int = 10, max_size: int = 100_000) -> None:
        self._window_seconds = window_minutes * 60
        self._max_size = max_size
        self._cache: OrderedDict[str, float] = OrderedDict()

    def _evict_expired(self) -> None:
        """Remove entries older than the TTL window."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        while self._cache:
            key, ts = next(iter(self._cache.items()))
            if ts < cutoff:
                self._cache.pop(key)
            else:
                break

    def is_duplicate(self, handoff_id: str) -> bool:
        """Return True if ``handoff_id`` was already seen within the dedup window.

        If not a duplicate, marks it as seen automatically.
        """
        self._evict_expired()
        if handoff_id in self._cache:
            return True
        # Mark as seen on first encounter
        self._cache[handoff_id] = time.monotonic()
        # Enforce max capacity via LRU eviction
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
        return False

    @property
    def size(self) -> int:
        """Current number of entries in the dedup cache."""
        return len(self._cache)
