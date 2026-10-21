import asyncio

import pytest

from apps.api.app.services.ingestion.dedup_service import DedupService


class TestDedupService:
    @pytest.fixture
    def dedup(self):
        return DedupService(redis_client=None, default_ttl_seconds=120)

    def test_canonical_key_bom(self):
        key = DedupService.canonical_key_bom("IDN11060", "2026-03-25T10:00:00Z")
        assert key == "bom:IDN11060:2026-03-25T10:00:00Z"

    def test_canonical_key_geojson(self):
        key = DedupService.canonical_key_geojson("fire-123", "2026-03-25T10:05:00Z")
        assert key == "geojson:fire-123:2026-03-25T10:05:00Z"

    def test_canonical_key_sensor(self):
        key = DedupService.canonical_key_sensor("AWS-066214", "2026-03-25T10:10:00Z")
        assert key == "sensor:AWS-066214:2026-03-25T10:10:00Z"

    def test_canonical_key_social(self):
        key = DedupService.canonical_key_social("twitter", "1234567890")
        assert key == "social:twitter:1234567890"

    def test_compute_hash_deterministic(self):
        h1 = DedupService.compute_hash("bom:IDN11060:2026-03-25T10:00:00Z")
        h2 = DedupService.compute_hash("bom:IDN11060:2026-03-25T10:00:00Z")
        assert h1 == h2
        assert len(h1) == 64

    def test_compute_hash_different_for_different_keys(self):
        h1 = DedupService.compute_hash("bom:IDN11060:2026-03-25T10:00:00Z")
        h2 = DedupService.compute_hash("bom:IDN11060:2026-03-25T11:00:00Z")
        assert h1 != h2

    @pytest.mark.asyncio
    async def test_check_returns_false_for_new_hash(self, dedup):
        result = await dedup.check("newhash123")
        assert result is False

    @pytest.mark.asyncio
    async def test_try_claim_then_commit_sets_key(self, dedup):
        claimed = await dedup.try_claim("dedup:live:bom-warnings:testhash", ttl_seconds=30)
        assert claimed is True

        await dedup.commit("dedup:live:bom-warnings:testhash", "sig-abc123", ttl_seconds=30)
        result = await dedup.check("dedup:live:bom-warnings:testhash")
        assert result is True

    @pytest.mark.asyncio
    async def test_release_clears_claim(self, dedup):
        key = "dedup:live:bom-warnings:hash_a"
        assert await dedup.try_claim(key, ttl_seconds=30) is True
        await dedup.release(key)
        assert await dedup.check(key) is False

    @pytest.mark.asyncio
    async def test_concurrent_claims_have_single_winner(self, dedup):
        key = "dedup:live:bom-warnings:race"

        async def _claim() -> bool:
            return await dedup.try_claim(key, ttl_seconds=60)

        results = await asyncio.gather(*[_claim() for _ in range(8)])
        assert sum(1 for item in results if item) == 1

    @pytest.mark.asyncio
    async def test_local_fallback_expiry(self):
        dedup = DedupService(redis_client=None, default_ttl_seconds=1)
        key = "dedup:live:twitter:test-expiry"
        assert await dedup.try_claim(key, ttl_seconds=1) is True
        assert await dedup.try_claim(key, ttl_seconds=1) is False
        await asyncio.sleep(1.1)
        assert await dedup.try_claim(key, ttl_seconds=1) is True

    @pytest.mark.asyncio
    async def test_scopes_and_sources_are_independent(self, dedup):
        key_live = "dedup:live:bom-warnings:samehash"
        key_sim = "dedup:sim-nsw:bom-warnings:samehash"
        key_other_source = "dedup:live:bom-radar:samehash"

        assert await dedup.try_claim(key_live, ttl_seconds=30) is True
        assert await dedup.try_claim(key_sim, ttl_seconds=30) is True
        assert await dedup.try_claim(key_other_source, ttl_seconds=30) is True
