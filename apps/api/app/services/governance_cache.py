import time
from typing import Any

from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition

DEFAULT_TTL_SECONDS = 300


class GovernanceCacheService:
    """In-memory governance cache. Swap for Redis client in production."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[HandoffChainDefinition, float]] = {}
        # Dashboard-level cache per tenant_id
        self._dashboard_store: dict[str, tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, data_source_id: str) -> HandoffChainDefinition | None:
        entry = self._store.get(data_source_id)
        if entry is None:
            self.misses += 1
            return None
        chain, expiry = entry
        if time.monotonic() >= expiry:
            del self._store[data_source_id]
            self.misses += 1
            return None
        self.hits += 1
        return chain

    def put(self, data_source_id: str, chain: HandoffChainDefinition) -> None:
        self._store[data_source_id] = (chain, time.monotonic() + self._ttl)

    def invalidate(self, data_source_id: str, *, tenant_id: str | None = None) -> None:
        self._store.pop(data_source_id, None)

    def clear(self) -> None:
        self._store.clear()
        self._dashboard_store.clear()

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    # --- Dashboard cache (021-governance-dashboard) ---

    def get_dashboard(self, cache_key: str, *, bypass: bool = False) -> Any | None:
        """Get cached dashboard data by key. bypass=True skips cache."""
        if bypass:
            self.misses += 1
            return None
        entry = self._dashboard_store.get(cache_key)
        if entry is None:
            self.misses += 1
            return None
        data, expiry = entry
        if time.monotonic() >= expiry:
            del self._dashboard_store[cache_key]
            self.misses += 1
            return None
        self.hits += 1
        return data

    def put_dashboard(self, cache_key: str, data: Any, ttl_seconds: int | None = None) -> None:
        """Cache dashboard data with optional custom TTL (default: 5 minutes)."""
        ttl = ttl_seconds or self._ttl
        self._dashboard_store[cache_key] = (data, time.monotonic() + ttl)

    def invalidate_dashboard(self, tenant_id: str) -> None:
        """Invalidate all dashboard cache entries for a tenant."""
        keys_to_remove = [k for k in self._dashboard_store if k.startswith(f"dash:{tenant_id}:")]
        for k in keys_to_remove:
            del self._dashboard_store[k]
