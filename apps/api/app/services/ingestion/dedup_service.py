import asyncio
import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.middleware.resilience import retry_transient_dependency_call

logger = logging.getLogger(__name__)


class DedupService:
    """Redis-backed content-hash deduplication for ingestion pipelines.

    Uses a configurable TTL per source to bound Redis memory. Canonical keys
    are source-specific (e.g. BoM product code + issue timestamp, GeoJSON
    feature ID + last-updated timestamp).
    """

    def __init__(self, redis_client: Any = None, default_ttl_seconds: int = 120):
        self._redis = redis_client
        self._default_ttl = default_ttl_seconds
        self._local_cache: dict[str, tuple[str, datetime]] = {}
        self._max_local_entries = 50000
        self._redis_warned = False  # suppress repeated warnings

    @staticmethod
    @retry_transient_dependency_call
    def _redis_get(redis_client: Any, key: str) -> Any:
        return redis_client.get(key)

    @staticmethod
    @retry_transient_dependency_call
    def _redis_set(redis_client: Any, key: str, value: str, ttl: int) -> None:
        redis_client.set(key, value, ex=ttl)

    @staticmethod
    @retry_transient_dependency_call
    def _redis_set_nx(redis_client: Any, key: str, value: str, ttl: int) -> bool:
        return bool(redis_client.set(key, value, nx=True, ex=ttl))

    @staticmethod
    @retry_transient_dependency_call
    def _redis_delete(redis_client: Any, key: str) -> None:
        redis_client.delete(key)

    def _prune_local_cache(self) -> None:
        now = datetime.now(UTC)
        expired = [k for k, (_, expiry) in self._local_cache.items() if expiry <= now]
        for key in expired:
            self._local_cache.pop(key, None)

        if len(self._local_cache) <= self._max_local_entries:
            return

        # Drop oldest-expiring keys first to keep local fallback bounded.
        ordered = sorted(self._local_cache.items(), key=lambda item: item[1][1])
        trim_count = len(self._local_cache) - self._max_local_entries
        for key, _ in ordered[:trim_count]:
            self._local_cache.pop(key, None)

    async def try_claim(self, key: str, ttl_seconds: int | None = None) -> bool:
        ttl = ttl_seconds or self._default_ttl
        redis_key = key if key.startswith("dedup:") else f"dedup:{key}"

        if self._redis:
            try:
                claimed = await asyncio.to_thread(self._redis_set_nx, self._redis, redis_key, "claim", ttl)
                if self._redis_warned:
                    logger.info("Redis dedup connection restored")
                    self._redis_warned = False
                return claimed
            except Exception:
                if not self._redis_warned:
                    logger.warning("Redis unavailable for dedup claim — falling back to local expiry cache")
                    self._redis_warned = True

        self._prune_local_cache()
        if redis_key in self._local_cache:
            return False
        self._local_cache[redis_key] = ("claim", datetime.now(UTC) + timedelta(seconds=ttl))
        return True

    async def commit(self, key: str, signal_id: str, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._default_ttl
        redis_key = key if key.startswith("dedup:") else f"dedup:{key}"
        if self._redis:
            try:
                await asyncio.to_thread(self._redis_set, self._redis, redis_key, signal_id, ttl)
                if self._redis_warned:
                    logger.info("Redis dedup connection restored")
                    self._redis_warned = False
                return
            except Exception:
                if not self._redis_warned:
                    logger.warning("Redis unavailable for dedup commit — falling back to local expiry cache")
                    self._redis_warned = True

        self._prune_local_cache()
        self._local_cache[redis_key] = (signal_id, datetime.now(UTC) + timedelta(seconds=ttl))

    async def release(self, key: str) -> None:
        redis_key = key if key.startswith("dedup:") else f"dedup:{key}"
        if self._redis:
            try:
                await asyncio.to_thread(self._redis_delete, self._redis, redis_key)
                if self._redis_warned:
                    logger.info("Redis dedup connection restored")
                    self._redis_warned = False
                return
            except Exception:
                if not self._redis_warned:
                    logger.warning("Redis unavailable for dedup release — falling back to local expiry cache")
                    self._redis_warned = True

        self._prune_local_cache()
        self._local_cache.pop(redis_key, None)

    async def check(self, dedup_hash: str) -> bool:
        redis_key = dedup_hash if dedup_hash.startswith("dedup:") else f"dedup:{dedup_hash}"
        if self._redis:
            try:
                result = await asyncio.to_thread(self._redis_get, self._redis, redis_key)
                return result is not None
            except Exception:
                if not self._redis_warned:
                    logger.warning("Redis unavailable for dedup check — falling back to local expiry cache")
                    self._redis_warned = True
        self._prune_local_cache()
        return redis_key in self._local_cache

    async def store(self, dedup_hash: str, signal_id: str, ttl_seconds: int | None = None) -> None:
        await self.commit(dedup_hash, signal_id, ttl_seconds)

    @staticmethod
    def compute_hash(canonical_key: str) -> str:
        return hashlib.sha256(canonical_key.encode("utf-8")).hexdigest()

    @staticmethod
    def canonical_key_bom(product_code: str, issue_timestamp: str) -> str:
        return f"bom:{product_code}:{issue_timestamp}"

    @staticmethod
    def canonical_key_geojson(feature_id: str, updated_at: str) -> str:
        return f"geojson:{feature_id}:{updated_at}"

    @staticmethod
    def canonical_key_sensor(station_id: str, observation_timestamp: str) -> str:
        return f"sensor:{station_id}:{observation_timestamp}"

    @staticmethod
    def canonical_key_social(platform: str, post_id: str) -> str:
        return f"social:{platform}:{post_id}"
