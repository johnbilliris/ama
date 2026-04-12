
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
    async def test_store_then_check_returns_true(self, dedup):
        await dedup.store("testhash", "sig-abc123")
        result = await dedup.check("testhash")
        assert result is True

    @pytest.mark.asyncio
    async def test_different_hash_not_found(self, dedup):
        await dedup.store("hash_a", "sig-001")
        result = await dedup.check("hash_b")
        assert result is False
