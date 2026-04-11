"""Handoff deduplication service — TTL-based in-memory cache with dual dedup keys.

Uses an LRU-ordered dictionary with time-based expiry. The dedup window
is configurable via ``HANDOFF_DEDUP_WINDOW_MINUTES`` (default 30).

Dual dedup:
- By handoff_id (exact match)
- By incident_id + hazard_type combination (semantic dedup)

Fail-open on cache full/restart per CHK056 — accept handoff rather than reject.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class HandoffDeduplicator:
    """Time-bounded idempotency checker for incoming handoffs."""

    def __init__(self, window_minutes: int = 30, max_size: int = 100_000) -> None:
        self._window_seconds = window_minutes * 60
        self._max_size = max_size
        self._id_cache: OrderedDict[str, float] = OrderedDict()
        self._incident_cache: OrderedDict[str, float] = OrderedDict()

    def _evict_expired(self, cache: OrderedDict[str, float]) -> None:
        """Remove entries older than the TTL window."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        while cache:
            key, ts = next(iter(cache.items()))
            if ts < cutoff:
                cache.pop(key)
            else:
                break

    def is_duplicate_by_id(self, handoff_id: str) -> bool:
        """Return True if ``handoff_id`` was already seen within the dedup window.

        If not a duplicate, marks it as seen automatically.
        Fail-open on cache full per CHK056.
        """
        self._evict_expired(self._id_cache)
        if handoff_id in self._id_cache:
            return True
        # Mark as seen
        self._id_cache[handoff_id] = time.monotonic()
        # Enforce max capacity via LRU eviction (fail-open: accept, just evict old)
        while len(self._id_cache) > self._max_size:
            self._id_cache.popitem(last=False)
        return False

    def is_duplicate_by_incident(self, incident_id: str, hazard_type: str) -> bool:
        """Return True if incident+hazard combination was seen within the dedup window.

        If not a duplicate, marks it as seen automatically.
        Fail-open on cache full per CHK056.
        """
        key = f"{incident_id}:{hazard_type}"
        self._evict_expired(self._incident_cache)
        if key in self._incident_cache:
            return True
        # Mark as seen
        self._incident_cache[key] = time.monotonic()
        while len(self._incident_cache) > self._max_size:
            self._incident_cache.popitem(last=False)
        return False

    @property
    def size(self) -> int:
        """Current number of entries in both dedup caches."""
        return len(self._id_cache) + len(self._incident_cache)

    @property
    def id_cache_size(self) -> int:
        """Current number of entries in the handoff ID dedup cache."""
        return len(self._id_cache)

    @property
    def incident_cache_size(self) -> int:
        """Current number of entries in the incident+hazard dedup cache."""
        return len(self._incident_cache)
