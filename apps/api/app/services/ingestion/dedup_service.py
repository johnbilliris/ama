import hashlib
import logging
from typing import Any

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
        self._local_cache: dict[str, str] = {}
        self._redis_warned = False  # suppress repeated warnings

    async def check(self, dedup_hash: str) -> bool:
        if self._redis:
            try:
                result = self._redis.get(f"dedup:{dedup_hash}")
                return result is not None
            except Exception:
                if not self._redis_warned:
                    logger.warning("Redis unavailable for dedup — falling back to local cache")
                    self._redis_warned = True
        return dedup_hash in self._local_cache

    async def store(self, dedup_hash: str, signal_id: str, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._default_ttl
        value = signal_id
        if self._redis:
            try:
                self._redis.set(f"dedup:{dedup_hash}", value, ex=ttl)
                if self._redis_warned:
                    logger.info("Redis dedup connection restored")
                    self._redis_warned = False
                return
            except Exception:
                if not self._redis_warned:
                    logger.warning("Redis unavailable for dedup — falling back to local cache")
                    self._redis_warned = True
        self._local_cache[dedup_hash] = value

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
