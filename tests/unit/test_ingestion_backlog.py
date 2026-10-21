from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections import deque
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from apps.api.app.services.ingestion.dedup_service import DedupService
from apps.api.app.services.ingestion.pipeline_base import (
    IngestionPipelineBase,
    PipelineMetrics,
    PipelineProcessingResult,
)
from apps.ingestion.backlog import BlobIngestionBacklog
from apps.ingestion.pipeline_config import IngestionPipelineConfig, resolve_pipeline_configs
from apps.ingestion.pipeline_factory import create_pipeline
from apps.ingestion.worker import PipelineWorker


class _Container:
    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}
        self.leases: dict[str, object] = {}
        self.fail_checkpoint = False
        self.fail_upload = False

    def get_blob_client(self, name: str) -> _Blob:
        return _Blob(self, name)

    def list_blobs(self, *, name_starts_with: str) -> list[SimpleNamespace]:
        return [SimpleNamespace(name=name) for name in self.data if name.startswith(name_starts_with)]


class _Blob:
    def __init__(self, container: _Container, name: str) -> None:
        self.container = container
        self.name = name

    def upload_blob(self, data: str | bytes, *, overwrite: bool, lease: object | None = None) -> None:
        if not overwrite and self.name in self.container.data:
            raise ResourceExistsError()
        if self.container.fail_checkpoint and lease is not None:
            raise ConnectionError("checkpoint unavailable")
        if self.container.fail_upload and "/batches/" in self.name:
            raise ConnectionError("snapshot unavailable")
        if overwrite and self.name.endswith("checkpoint.json"):
            assert self.container.leases[self.name] is lease
        self.container.data[self.name] = data.encode() if isinstance(data, str) else data

    def download_blob(self, *, lease: object | None = None) -> SimpleNamespace:
        if self.name not in self.container.data:
            raise ResourceNotFoundError()
        if lease is not None:
            assert self.container.leases[self.name] is lease
        return SimpleNamespace(readall=lambda: self.container.data[self.name])

    def acquire_lease(self, *, lease_duration: int) -> Mock:
        assert lease_duration == 60
        if self.name in self.container.leases:
            raise ResourceExistsError("lease already held")
        lease = Mock()
        self.container.leases[self.name] = lease
        lease.release.side_effect = lambda: self.container.leases.pop(self.name)
        return lease

    def delete_blob(self) -> None:
        if self.name not in self.container.data:
            raise ResourceNotFoundError()
        del self.container.data[self.name]


class _Pipeline(IngestionPipelineBase):
    def __init__(self, store: BlobIngestionBacklog | None, payloads: list[dict], **kwargs) -> None:
        super().__init__(
            pipeline_id="test-source",
            data_source_ids=["test-source"],
            poll_interval_seconds=60,
            max_records_per_cycle=2,
            backlog_store=store,
            **kwargs,
        )
        self.payloads = payloads
        self.polls = 0
        self.processed: list[int] = []
        self.failure: str | None = None
        self.cancel_at: int | None = None

    async def poll_source(self) -> list[dict]:
        self.polls += 1
        return self.payloads

    def normalise(self, raw_payload: dict) -> dict:
        raise NotImplementedError

    def compute_canonical_key(self, raw_payload: dict) -> str:
        return str(raw_payload["id"])

    async def _process_payload(self, raw_payload: dict) -> PipelineProcessingResult:
        if raw_payload["id"] == self.cancel_at:
            raise asyncio.CancelledError
        if self.failure == "exception":
            raise ConnectionError("storage unavailable")
        if self.failure:
            return PipelineProcessingResult(False, self.failure, "test failure")
        self.processed.append(raw_payload["id"])
        return PipelineProcessingResult(True, "accepted")


def _payloads(count: int = 5) -> list[dict]:
    return [{"id": i} for i in range(count)]


@pytest.mark.asyncio
@pytest.mark.parametrize("durable", [False, True])
async def test_cycle_is_bounded_and_drains_every_record_before_repolling(durable: bool) -> None:
    container = _Container()
    store = BlobIngestionBacklog(container) if durable else None
    pipeline = _Pipeline(store, _payloads())
    for expected in ([0, 1], [0, 1, 2, 3], [0, 1, 2, 3, 4]):
        await pipeline._poll_cycle()
        assert pipeline.processed == expected
        assert pipeline.polls == 1
    assert pipeline._backlog_pending is False
    assert not any("/batches/" in name for name in container.data)


@pytest.mark.asyncio
async def test_restart_resumes_durable_snapshot_instead_of_changed_feed() -> None:
    container = _Container()
    first = _Pipeline(BlobIngestionBacklog(container), _payloads())
    await first._poll_cycle()

    second = _Pipeline(BlobIngestionBacklog(container), [{"id": 99}])
    await second._poll_cycle()
    await second._poll_cycle()
    assert first.processed + second.processed == list(range(5))
    assert second.polls == 0
    await second._poll_cycle()
    assert second.processed[-1] == 99
    assert second.polls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["exception", "degraded", "busy"])
async def test_failed_record_is_retained_across_restart(failure: str) -> None:
    container = _Container()
    first = _Pipeline(BlobIngestionBacklog(container), _payloads())
    first.failure = failure
    await first._poll_cycle()
    assert first._backlog_pending

    second = _Pipeline(BlobIngestionBacklog(container), [])
    await second._poll_cycle()
    assert second.processed == [0, 1]
    assert second.polls == 0


@pytest.mark.asyncio
async def test_cancellation_replays_uncheckpointed_records_without_skipping() -> None:
    container = _Container()
    first = _Pipeline(BlobIngestionBacklog(container), _payloads())
    first.cancel_at = 1
    with pytest.raises(asyncio.CancelledError):
        await first._poll_cycle()
    assert first.processed == [0]
    assert not container.leases

    second = _Pipeline(BlobIngestionBacklog(container), [])
    await second._poll_cycle()
    assert second.processed == [0, 1]


@pytest.mark.asyncio
async def test_snapshot_uploaded_before_checkpoint_failure_is_recovered() -> None:
    container = _Container()
    container.fail_checkpoint = True
    first = _Pipeline(BlobIngestionBacklog(container), _payloads())
    with pytest.raises(ExceptionGroup, match="TaskGroup"):
        await first._poll_cycle()
    assert first.processed == []
    assert any("/batches/" in name for name in container.data)

    container.fail_checkpoint = False
    second = _Pipeline(BlobIngestionBacklog(container), [])
    await second._poll_cycle()
    assert second.processed == [0, 1]
    assert second.polls == 0


@pytest.mark.asyncio
async def test_snapshot_write_failure_does_not_process_or_acknowledge_records() -> None:
    container = _Container()
    container.fail_upload = True
    pipeline = _Pipeline(BlobIngestionBacklog(container), _payloads())
    with pytest.raises(ExceptionGroup):
        await pipeline._poll_cycle()
    assert pipeline.processed == []
    container.fail_upload = False
    pipeline.payloads = []
    await pipeline._poll_cycle()
    assert pipeline.processed == [0, 1]
    assert pipeline.polls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["rejected", "blocked"])
async def test_terminal_rejections_are_retained_durably_before_advancing(status: str) -> None:
    container = _Container()
    pipeline = _Pipeline(BlobIngestionBacklog(container), _payloads(2))
    pipeline.failure = status
    await pipeline._poll_cycle()
    rejected = [json.loads(data) for name, data in container.data.items() if "/rejected/" in name]
    assert [item["payload"]["id"] for item in rejected] == [0, 1]
    assert all(item["status"] == status and item["reason"] == "test failure" for item in rejected)
    assert not pipeline._backlog_pending


@pytest.mark.asyncio
async def test_pending_batch_is_processed_even_when_source_circuit_is_open() -> None:
    container = _Container()
    first = _Pipeline(BlobIngestionBacklog(container), _payloads())
    await first._poll_cycle()
    second = _Pipeline(BlobIngestionBacklog(container), [])
    second.circuit_breaker._trip()
    await second._poll_cycle()
    assert second.processed == [2, 3]
    assert second.polls == 0


@pytest.mark.asyncio
async def test_backlogs_are_isolated_by_tenant_scope() -> None:
    container = _Container()
    first = _Pipeline(BlobIngestionBacklog(container), _payloads(), scope="live")
    await first._poll_cycle()
    second = _Pipeline(BlobIngestionBacklog(container), [{"id": 99}], scope="sim-test", allow_simulation_scope=True)
    await second._poll_cycle()
    assert second.processed == [99]
    assert second.polls == 1


@pytest.mark.asyncio
async def test_only_one_replica_can_hold_a_pipeline_checkpoint_lease() -> None:
    container = _Container()
    async with BlobIngestionBacklog(container).open("live", "source"):
        with pytest.raises(ResourceExistsError):
            async with BlobIngestionBacklog(container).open("live", "source"):
                pytest.fail("second replica obtained an exclusive lease")
    assert not container.leases


@pytest.mark.asyncio
@pytest.mark.parametrize("error_code", ["LeaseAlreadyPresent", "ContainerAlreadyExists", None])
async def test_lease_contention_uses_short_retry_but_other_storage_errors_remain_errors(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, error_code: str | None
) -> None:
    pipeline = _Pipeline(None, [])
    pipeline.poll_interval_seconds = 3600
    error = ResourceExistsError("storage conflict")
    error.error_code = error_code
    cycles = 0

    async def poll_cycle() -> None:
        nonlocal cycles
        cycles += 1
        if cycles == 1:
            raise error
        await pipeline.stop()

    pipeline._poll_cycle = poll_cycle
    wait_for = asyncio.wait_for
    delays = []

    async def quick_wait(awaitable, *, timeout):
        delays.append(timeout)
        return await wait_for(awaitable, timeout=0.001)

    monkeypatch.setattr("apps.api.app.services.ingestion.pipeline_base.asyncio.wait_for", quick_wait)
    jitter = Mock(return_value=10)
    monkeypatch.setattr("apps.api.app.services.ingestion.pipeline_base.random.uniform", jitter)
    with caplog.at_level(logging.INFO):
        await pipeline.run()

    assert cycles == 2
    assert pipeline._backlog_retry is True
    if error_code == "LeaseAlreadyPresent":
        jitter.assert_called_once_with(5, 15)
        assert delays[0] == 10
        assert "backlog lease is held" in caplog.text
        assert not any(record.levelno >= logging.ERROR for record in caplog.records)
    else:
        jitter.assert_not_called()
        assert delays[0] == 3600
        assert any(record.levelno == logging.ERROR and record.exc_info for record in caplog.records)


@pytest.mark.asyncio
@pytest.mark.parametrize("contended", [False, True])
async def test_stop_wakes_pipelines_waiting_for_source_poll_or_lease(contended: bool) -> None:
    pipeline = _Pipeline(None, [])
    pipeline.poll_interval_seconds = 3600
    polled = asyncio.Event()

    async def poll_source() -> list[dict]:
        polled.set()
        return []

    pipeline.poll_source = poll_source
    if contended:

        async def poll_cycle() -> None:
            polled.set()
            error = ResourceExistsError("lease held")
            error.error_code = "LeaseAlreadyPresent"
            raise error

        pipeline._poll_cycle = poll_cycle
    worker = PipelineWorker()
    worker._running = True
    worker._pipelines = {pipeline.pipeline_id: pipeline}
    task = asyncio.create_task(pipeline.run())
    worker._tasks = {pipeline.pipeline_id: task}
    try:
        await asyncio.wait_for(polled.wait(), timeout=1)
        await asyncio.wait_for(worker.stop(), timeout=1)
        assert task.done()
        assert not task.cancelled()
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_graceful_shutdown_finishes_cycle_and_releases_lease() -> None:
    container = _Container()
    pipeline = _Pipeline(BlobIngestionBacklog(container), _payloads(2))
    processing = asyncio.Event()
    finish = asyncio.Event()
    process = pipeline._process_payload

    async def delayed_process(raw: dict) -> PipelineProcessingResult:
        processing.set()
        await finish.wait()
        return await process(raw)

    pipeline._process_payload = delayed_process
    worker = PipelineWorker()
    worker._running = True
    worker._pipelines = {pipeline.pipeline_id: pipeline}
    task = asyncio.create_task(pipeline.run())
    worker._tasks = {pipeline.pipeline_id: task}
    stopping = None
    try:
        await asyncio.wait_for(processing.wait(), timeout=2)
        stopping = asyncio.create_task(worker.stop())
        await asyncio.sleep(0)
        assert not worker._running
        assert not stopping.done()
        assert container.leases
        finish.set()
        await asyncio.wait_for(stopping, timeout=2)

        assert pipeline.processed == [0, 1]
        assert not task.cancelled()
        assert not container.leases
        assert not any("/batches/" in name for name in container.data)
        checkpoint = next(json.loads(data) for name, data in container.data.items() if name.endswith("checkpoint.json"))
        assert checkpoint["offset"] == 2
    finally:
        tasks = [task] + ([stopping] if stopping is not None else [])
        for pending in tasks:
            if not pending.done():
                pending.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_shutdown_shares_deadline_and_awaits_all_lease_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    container = _Container()
    worker = PipelineWorker()
    worker._running = True
    started = []

    for index in range(3):
        pipeline = _Pipeline(BlobIngestionBacklog(container), _payloads(2))
        pipeline.pipeline_id = f"source-{index}"
        processing = asyncio.Event()
        started.append(processing)

        async def process(raw: dict, event: asyncio.Event = processing) -> PipelineProcessingResult:
            event.set()
            await asyncio.Event().wait()
            raise AssertionError("stalled processing should be cancelled")

        pipeline._process_payload = process
        worker._pipelines[pipeline.pipeline_id] = pipeline
        worker._tasks[pipeline.pipeline_id] = asyncio.create_task(pipeline.run())

    try:
        await asyncio.wait_for(asyncio.gather(*(event.wait() for event in started)), timeout=2)
        assert len(container.leases) == 3
        wait = asyncio.wait
        deadlines = []

        async def quick_wait(tasks, *, timeout):
            deadlines.append(timeout)
            return await wait(tasks, timeout=0.01)

        monkeypatch.setattr("apps.ingestion.worker.asyncio.wait", quick_wait)
        await asyncio.wait_for(worker.stop(), timeout=2)

        assert deadlines == [30]
        assert all(task.done() and task.cancelled() for task in worker._tasks.values())
        assert not container.leases
        checkpoints = [json.loads(data) for name, data in container.data.items() if name.endswith("checkpoint.json")]
        assert len(checkpoints) == 3
        assert all(state["offset"] == 0 and state["total"] == 2 for state in checkpoints)
        assert len([name for name in container.data if "/batches/" in name]) == 3
    finally:
        for task in worker._tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*worker._tasks.values(), return_exceptions=True)


@pytest.mark.asyncio
async def test_dedup_claim_is_busy_until_committed_or_expired() -> None:
    dedup = DedupService()
    assert await dedup.claim_status("key", 60) == "claimed"
    assert await dedup.claim_status("key", 60) == "busy"
    await dedup.commit("key", "sig-1", 60)
    assert await dedup.claim_status("key", 60) == "duplicate"
    dedup._local_cache["dedup:key"] = ("claim", datetime.now(UTC) - timedelta(seconds=1))
    assert await dedup.claim_status("key", 60) == "claimed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored,expected", [("claim", "busy"), (b"claim", "busy"), (None, "busy"), ("sig-1", "duplicate")]
)
async def test_redis_claim_distinguishes_inflight_from_completed(stored: object, expected: str) -> None:
    redis = Mock()
    redis.set.return_value = False
    redis.get.return_value = stored
    assert await DedupService(redis_client=redis).claim_status("key", 60) == expected


def test_metrics_pruning_preserves_deques_and_inclusive_window_boundary() -> None:
    metrics = PipelineMetrics("source")
    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=1)
    metrics._dedup_events.extend([(now, False), (cutoff, True), (cutoff - timedelta(microseconds=1), True)])
    metrics._signal_events.extend([now, cutoff, cutoff - timedelta(microseconds=1)])
    dedup_events = metrics._dedup_events
    signal_events = metrics._signal_events
    assert metrics.dedup_window_counts(now=now) == {"total": 2, "hits": 1, "rate": 0.5}
    assert metrics._dedup_events is dedup_events
    assert metrics._signal_events is signal_events
    assert list(signal_events) == [now, cutoff]


def test_metrics_do_not_iterate_retained_entries_during_pruning() -> None:
    class _NoScanDeque(deque):
        def __iter__(self):
            raise AssertionError("pruning scanned retained events")

    metrics = PipelineMetrics("source")
    now = datetime.now(UTC)
    metrics._dedup_events = _NoScanDeque([(now, True)] * 45_000)
    metrics._signal_events = _NoScanDeque([now] * 6_500)
    metrics.record_dedup_hit()
    metrics.record_ingestion(1)
    assert len(metrics._dedup_events) == 45_002
    assert len(metrics._signal_events) == 6_501


class _ActualPipeline(_Pipeline):
    async def _process_payload(self, raw_payload: dict) -> PipelineProcessingResult:
        return await IngestionPipelineBase._process_payload(self, raw_payload)

    def normalise(self, raw_payload: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        return {
            "source": {"dataSourceId": "test-source", "name": "Test", "kind": "sensor"},
            "category": "weather",
            "occurredAt": now,
            "receivedAt": now,
            "location": {"type": "Point", "coordinates": [151.2, -33.8]},
            "payload": raw_payload,
            "validationStatus": "validated",
            "provenance": {"sourceUri": "https://example.com"},
        }


@pytest.mark.asyncio
async def test_crashed_dedup_claim_does_not_acknowledge_unpersisted_record() -> None:
    container = _Container()
    dedup = DedupService()
    key = hashlib.sha256(b"0").hexdigest()
    await dedup.claim_status(key, 60)
    repository = SimpleNamespace(save=AsyncMock())
    pipeline = _ActualPipeline(
        BlobIngestionBacklog(container), _payloads(), dedup_service=dedup, signal_repository=repository
    )
    await pipeline._poll_cycle()
    assert pipeline._backlog_pending
    assert pipeline._backlog_retry
    repository.save.assert_not_awaited()
    checkpoint = next(json.loads(data) for name, data in container.data.items() if name.endswith("checkpoint.json"))
    assert checkpoint["offset"] == 0


@pytest.mark.asyncio
async def test_archival_exception_releases_claim_and_keeps_backlog() -> None:
    container = _Container()
    dedup = DedupService()
    archive = SimpleNamespace(store_raw_payload=AsyncMock(side_effect=ConnectionError("archive unavailable")))
    pipeline = _ActualPipeline(BlobIngestionBacklog(container), _payloads(), dedup_service=dedup, blob_storage=archive)
    await pipeline._poll_cycle()
    key = hashlib.sha256(b"0").hexdigest()
    assert not await dedup.check(key)
    assert pipeline._backlog_pending


@pytest.mark.asyncio
async def test_checkpoint_failure_replays_committed_records_then_advances_without_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("apps.api.app.services.ingestion.pipeline_base.publish_signal_accepted", AsyncMock())
    container = _Container()
    dedup = DedupService()
    repository = SimpleNamespace(save=AsyncMock())
    first = _ActualPipeline(
        BlobIngestionBacklog(container), _payloads(), dedup_service=dedup, signal_repository=repository
    )
    original = first._process_pending_payload

    async def fail_checkpoint_after_processing(raw: dict) -> PipelineProcessingResult | None:
        result = await original(raw)
        if raw["id"] == 1:
            container.fail_checkpoint = True
        return result

    first._process_pending_payload = fail_checkpoint_after_processing
    with pytest.raises(ExceptionGroup):
        await first._poll_cycle()
    assert repository.save.await_count == 2

    container.fail_checkpoint = False
    second = _ActualPipeline(BlobIngestionBacklog(container), [], dedup_service=dedup, signal_repository=repository)
    await second._poll_cycle()
    assert second._metrics.dedup_hits == 2
    assert repository.save.await_count == 2
    await second._poll_cycle()
    await second._poll_cycle()
    assert [call.args[0].payload["id"] for call in repository.save.await_args_list] == list(range(5))
    assert second.polls == 0


@pytest.mark.asyncio
async def test_rejection_storage_failure_does_not_advance_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    container = _Container()
    original = _Blob.upload_blob

    def fail_rejection(self: _Blob, *args, **kwargs) -> None:
        if "/rejected/" in self.name:
            raise ConnectionError("rejection storage unavailable")
        original(self, *args, **kwargs)

    monkeypatch.setattr(_Blob, "upload_blob", fail_rejection)
    pipeline = _Pipeline(BlobIngestionBacklog(container), _payloads(2))
    pipeline.failure = "rejected"
    with pytest.raises(ExceptionGroup):
        await pipeline._poll_cycle()
    checkpoint = next(json.loads(data) for name, data in container.data.items() if name.endswith("checkpoint.json"))
    assert checkpoint["offset"] == 0
    assert any("/batches/" in name for name in container.data)


@pytest.mark.asyncio
async def test_unrecognised_outcome_is_not_acknowledged() -> None:
    container = _Container()
    pipeline = _Pipeline(BlobIngestionBacklog(container), _payloads(2))
    pipeline.failure = "unexpected"
    with pytest.raises(ExceptionGroup):
        await pipeline._poll_cycle()
    checkpoint = next(json.loads(data) for name, data in container.data.items() if name.endswith("checkpoint.json"))
    assert checkpoint["offset"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [1, 3, 5])
async def test_factory_wires_configured_limit_and_durable_backlog(monkeypatch: pytest.MonkeyPatch, limit: int) -> None:
    monkeypatch.setenv("INGESTION_MAX_RECORDS_PER_CYCLE", str(limit))
    container = _Container()
    store = BlobIngestionBacklog(container)
    config = IngestionPipelineConfig(
        pipeline_id="bom-aws-stations",
        source_class="sensor",
        data_source_ids=["bom-aws-stations"],
        poll_interval_seconds=300,
        max_records_per_cycle=3,
        endpoint_url="https://example.com",
        endpoint_format="json",
    )
    resolved = resolve_pipeline_configs([config])[0]
    pipeline = create_pipeline(resolved, backlog_store=store)
    pipeline.poll_source = AsyncMock(return_value=_payloads(7))
    pipeline._process_payload = AsyncMock(return_value=PipelineProcessingResult(True, "accepted"))
    assert pipeline.backlog_store is store
    assert pipeline.max_records_per_cycle == limit
    for offset in range(0, 7, limit):
        await pipeline._poll_cycle()
        assert pipeline._process_payload.await_count == min(offset + limit, 7)
    pipeline.poll_source.assert_awaited_once()


@pytest.mark.asyncio
async def test_lost_lease_cancels_processing_and_preserves_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    container = _Container()
    store = BlobIngestionBacklog(container)
    sleep = asyncio.sleep

    async def immediate_sleep(delay: float) -> None:
        await sleep(0)

    monkeypatch.setattr("apps.ingestion.backlog.asyncio.sleep", immediate_sleep)
    with pytest.raises(ExceptionGroup):
        async with store.open("live", "source") as batch:
            await batch.stage(_payloads())
            batch.lease.renew.side_effect = ConnectionError("lease lost")
            await asyncio.Event().wait()
    assert not container.leases
    assert any("/batches/" in name for name in container.data)
    checkpoint = next(json.loads(data) for name, data in container.data.items() if name.endswith("checkpoint.json"))
    assert checkpoint["offset"] == 0
