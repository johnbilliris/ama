import time
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.services.governance_cache import GovernanceCacheService

from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition, HandoffStep


def _make_chain(ds_id: str = "ds-test") -> HandoffChainDefinition:
    return HandoffChainDefinition(
        chain_id=f"chain-{uuid4().hex[:12]}", data_source_id=ds_id,
        steps=[HandoffStep(step_order=1, source_agent="monitoring", target_agent="risk_assessment")],
        created_by="arch", created_at=datetime.now(UTC),
    )


class TestCacheHitMiss:
    def test_cache_miss_then_hit(self) -> None:
        cache = GovernanceCacheService(ttl_seconds=60)
        assert cache.get("ds-1") is None
        assert cache.misses == 1
        cache.put("ds-1", _make_chain("ds-1"))
        result = cache.get("ds-1")
        assert result is not None
        assert cache.hits == 1

    def test_cache_ttl_expiry(self) -> None:
        cache = GovernanceCacheService(ttl_seconds=0)
        cache.put("ds-1", _make_chain("ds-1"))
        time.sleep(0.01)
        assert cache.get("ds-1") is None
        assert cache.misses == 1


class TestCacheInvalidation:
    def test_invalidate_removes_entry(self) -> None:
        cache = GovernanceCacheService(ttl_seconds=60)
        cache.put("ds-1", _make_chain("ds-1"))
        cache.invalidate("ds-1")
        assert cache.get("ds-1") is None

    def test_clear_removes_all(self) -> None:
        cache = GovernanceCacheService(ttl_seconds=60)
        cache.put("ds-1", _make_chain("ds-1"))
        cache.put("ds-2", _make_chain("ds-2"))
        cache.clear()
        assert cache.get("ds-1") is None
        assert cache.get("ds-2") is None


class TestHitRate:
    def test_hit_rate_calculation(self) -> None:
        cache = GovernanceCacheService(ttl_seconds=60)
        cache.put("ds-1", _make_chain("ds-1"))
        cache.get("ds-1")
        cache.get("ds-1")
        cache.get("ds-missing")
        assert cache.hit_rate == pytest.approx(2 / 3, abs=0.01)
