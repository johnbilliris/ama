import time

from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition

DEFAULT_TTL_SECONDS = 300


class GovernanceCacheService:
    """In-memory governance cache. Swap for Redis client in production."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[HandoffChainDefinition, float]] = {}
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

    def invalidate(self, data_source_id: str) -> None:
        self._store.pop(data_source_id, None)

    def clear(self) -> None:
        self._store.clear()

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
