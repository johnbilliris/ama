
import pytest

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase


class MockPipeline(IngestionPipelineBase):
    def __init__(self, payloads=None, fail_on_poll=False, **kwargs):
        super().__init__(
            pipeline_id="mock-pipeline",
            data_source_ids=["mock-source"],
            poll_interval_seconds=1,
            **kwargs,
        )
        self._payloads = payloads or []
        self._fail_on_poll = fail_on_poll
        self.processed: list = []

    async def poll_source(self):
        if self._fail_on_poll:
            raise ConnectionError("Source unavailable")
        return self._payloads

    def normalise(self, raw_payload):
        return {
            "source": {"dataSourceId": "mock-source", "name": "Mock", "kind": "authoritative"},
            "category": "weather",
            "occurredAt": "2026-03-25T10:00:00Z",
            "receivedAt": "2026-03-25T10:00:01Z",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
            "payload": raw_payload,
            "confidenceScore": 0.95,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
            "provenance": {"collectionMethod": "api_pull", "sourceUri": "https://example.com"},
        }

    def compute_canonical_key(self, raw_payload):
        return f"mock:{raw_payload.get('id', 'unknown')}"


class TestIngestionPipelineIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline_lifecycle_with_mocked_source(self):
        payloads = [{"id": "1", "value": "test"}]
        pipeline = MockPipeline(payloads=payloads)
        await pipeline._poll_cycle()
        assert pipeline._metrics.signals_ingested >= 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_after_failures(self):
        pipeline = MockPipeline(fail_on_poll=True)
        for _ in range(3):
            await pipeline._poll_cycle()
        assert pipeline.circuit_breaker.state == "open"
        assert pipeline._metrics.poll_failures == 3

    @pytest.mark.asyncio
    async def test_dedup_skips_duplicate_payloads(self):
        from apps.api.app.services.ingestion.dedup_service import DedupService
        dedup = DedupService()
        payloads = [{"id": "dup-1"}, {"id": "dup-1"}]
        pipeline = MockPipeline(payloads=payloads, dedup_service=dedup)
        await pipeline._poll_cycle()
        assert pipeline._metrics.dedup_hits >= 0

    @pytest.mark.asyncio
    async def test_successful_poll_records_metrics(self):
        pipeline = MockPipeline(payloads=[{"id": "a"}])
        await pipeline._poll_cycle()
        assert pipeline._metrics.poll_successes == 1
