"""Signal deduplication service — TTL-based in-memory cache (FR-029).

Uses an LRU-ordered dictionary with time-based expiry.  The dedup window
is configurable via ``SIGNAL_DEDUP_WINDOW_MINUTES`` (default 10).
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class SignalDeduplicator:
    """Time-bounded idempotency checker for incoming signals."""

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

    def is_duplicate(self, signal_id: str) -> bool:
        """Return True if ``signal_id`` was already seen within the dedup window."""
        self._evict_expired()
        if signal_id in self._cache:
            return True
        return False

    def mark_seen(self, signal_id: str) -> None:
        """Record ``signal_id`` as seen now."""
        self._evict_expired()
        # If already present, move to end and refresh timestamp
        if signal_id in self._cache:
            self._cache.move_to_end(signal_id)
        self._cache[signal_id] = time.monotonic()
        # Enforce max capacity via LRU eviction
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    @property
    def size(self) -> int:
        """Current number of entries in the dedup cache."""
        return len(self._cache)
