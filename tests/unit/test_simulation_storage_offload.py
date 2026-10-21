"""AUD-031 — simulation storage I/O must not monopolise the shared API event loop.

Each test drives a real code path with a deliberately slow storage double that
records the thread it executed on, while an independent "live" ticker coroutine
runs on the event loop. The assertions are structural (off-loop execution,
bounded fan-out, loop progress), not latency or throughput measurements.
"""

import asyncio
import threading
import time
from datetime import UTC, datetime

import pytest
from app.core.async_io import gather_bounded, run_blocking, storage_io_limit
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.exercise_report_service import ExerciseReportService
from app.services.scenario_seeding_service import ScenarioSeedingService
from app.services.simulation_service import SimulationService

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant

pytestmark = pytest.mark.spec007_isolation

BLOCK_SECONDS = 0.25
TICK_SECONDS = 0.01


class _LiveTicker:
    """Stand-in for unrelated live traffic sharing the event loop."""

    def __init__(self) -> None:
        self.ticks = 0
        self._task: asyncio.Task[None] | None = None

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(TICK_SECONDS)
            self.ticks += 1

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass


class _BlockingContainer:
    """Synchronous Cosmos container double that sleeps and records its thread."""

    def __init__(self, items: list[dict] | None = None) -> None:
        self.items = items or []
        self.threads: list[int] = []

    def _block(self):
        self.threads.append(threading.get_ident())
        time.sleep(BLOCK_SECONDS)

    def query_items(self, *args, **kwargs):
        self._block()
        return list(self.items)

    def upsert_item(self, document):
        self._block()
        return document


class _BlockingCosmosClient:
    def __init__(self, container: _BlockingContainer) -> None:
        self._container = container

    def get_database_client(self, _name):
        return self

    def get_container_client(self, _name):
        return self._container


TENANT_ONE = "sim-aaaaaaaa-0000-4000-8000-000000000001"
TENANT_TWO = "sim-aaaaaaaa-0000-4000-8000-000000000002"
TENANT_THREE = "sim-aaaaaaaa-0000-4000-8000-000000000003"
TENANT_FOUR = "sim-aaaaaaaa-0000-4000-8000-000000000004"


def _tenant(tenant_id: str = TENANT_ONE) -> SimulationTenant:
    return SimulationTenant(
        tenant_id=tenant_id,
        scenario_id=tenant_id.removeprefix("sim-"),
        scenario_run_id=tenant_id.removeprefix("sim-"),
        scenario_type="Bushfire",
        created_by="user-001",
        created_at=datetime.now(UTC),
        participants=["user-001"],
        jurisdictions=["nsw"],
        status="Active",
    )


@pytest.mark.asyncio
async def test_repository_query_runs_off_the_loop_while_live_traffic_progresses():
    container = _BlockingContainer([_tenant().model_dump(mode="json")])
    repo = SimulationRepository(cosmos_client=_BlockingCosmosClient(container))
    ticker = _LiveTicker()
    ticker.start()

    loaded = await repo.get_by_tenant_id(TENANT_ONE)

    await ticker.stop()
    assert loaded is not None and loaded.tenant_id == TENANT_ONE
    assert container.threads and threading.get_ident() not in container.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_repository_update_and_signal_write_run_off_the_loop():
    container = _BlockingContainer([_tenant().model_dump(mode="json")])
    client = _BlockingCosmosClient(container)
    repo = SimulationRepository(cosmos_client=client)
    signals = SignalRepository(cosmos_client=client, tenant_id=TENANT_ONE)

    await repo.update(_tenant())
    await signals.create_signal(TENANT_ONE, {"signal_id": "sig-1"})

    assert len(container.threads) == 2
    assert threading.get_ident() not in container.threads


@pytest.mark.asyncio
async def test_report_timeline_read_runs_off_the_loop():
    class _BlockingEventRepository:
        def __init__(self) -> None:
            self.threads: list[int] = []

        def list_events(self, tenant_id, **kwargs):
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)
            return []

    repo = SimulationRepository()
    tenant = await repo.create(_tenant())
    events = _BlockingEventRepository()
    service = ExerciseReportService(
        simulation_repository=repo,
        signal_repository=SignalRepository(tenant_id=tenant.tenant_id),
        event_repository=events,
    )
    ticker = _LiveTicker()
    ticker.start()

    report = await service.generate_report(tenant.tenant_id)

    await ticker.stop()
    assert report.tenant_id == tenant.tenant_id
    assert events.threads and threading.get_ident() not in events.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_archive_manifest_hashes_and_uploads_off_the_loop():
    class _BlockingBlobContainer:
        def __init__(self) -> None:
            self.threads: list[int] = []

        def upload_blob(self, *args, **kwargs):
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)

    class _BlockingBlobService:
        def __init__(self, container) -> None:
            self._container = container

        def get_container_client(self, _name):
            return self._container

    repo = SimulationRepository()
    tenant = await repo.create(_tenant(TENANT_TWO))
    for index in range(50):
        await repo.upsert_document(
            {"id": f"{tenant.tenant_id}:doc:{index}", "tenant_id": tenant.tenant_id, "document_type": "seed"}
        )
    blob_container = _BlockingBlobContainer()
    service = ExerciseReportService(
        simulation_repository=repo,
        signal_repository=SignalRepository(tenant_id=tenant.tenant_id),
        blob_service_client=_BlockingBlobService(blob_container),
    )
    report = await service.generate_report(tenant.tenant_id)
    ticker = _LiveTicker()
    ticker.start()

    uri = await service.persist_archive_manifest(tenant.tenant_id, report)

    await ticker.stop()
    assert uri.endswith(f"{tenant.tenant_id}/archive/manifest.json")
    assert blob_container.threads and threading.get_ident() not in blob_container.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_seed_context_writes_respect_the_configured_batch_limit(monkeypatch):
    monkeypatch.setenv("SIMULATION_STORAGE_IO_WORKERS", "2")

    class _CountingRepository:
        def __init__(self) -> None:
            self.documents: list[dict] = []
            self.in_flight = 0
            self.peak_in_flight = 0

        async def upsert_document(self, document):
            self.in_flight += 1
            self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
            await asyncio.sleep(0.01)
            self.documents.append(document)
            self.in_flight -= 1
            return document

    class _Scheduler:
        def __init__(self) -> None:
            self.threads: list[int] = []
            self.started: list[str] = []

        def initialize(self, tenant_id, timeline, warp_speed=1.0):
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)

        def start_delivery_loop(self, tenant_id):
            self.started.append(tenant_id)
            return True

    class _Signals:
        async def save(self, signal, *, scope):  # pragma: no cover - unused in scheduled seeding
            raise AssertionError("scheduled seeding must not write signals inline")

    simulations = _CountingRepository()
    scheduler = _Scheduler()
    service = ScenarioSeedingService(
        signal_repository=_Signals(),
        simulation_repository=simulations,
        warp_scheduler=scheduler,
    )
    ticker = _LiveTicker()
    ticker.start()

    result = await service.seed_from_template("sim-12345678-1234-1234-1234-123456789012", "nsw-bushfire-multi-agency")

    await ticker.stop()
    assert result["signals_injected"] == 0
    assert result["signals_scheduled"] > 0
    assert scheduler.started == ["sim-12345678-1234-1234-1234-123456789012"]
    assert scheduler.threads and threading.get_ident() not in scheduler.threads
    assert len(simulations.documents) > 2
    assert simulations.peak_in_flight <= 2
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_archive_offloads_event_repository_purge():
    class _BlockingEventRepository:
        def __init__(self) -> None:
            self.threads: list[int] = []

        def delete_tenant(self, tenant_id):
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)
            return 1

    repo = SimulationRepository()
    tenant = await repo.create(_tenant(TENANT_THREE))
    events = _BlockingEventRepository()
    report_service = ExerciseReportService(
        simulation_repository=repo,
        signal_repository=SignalRepository(tenant_id=tenant.tenant_id),
    )
    service = SimulationService(
        simulation_repository=repo,
        report_service=report_service,
        event_repository=events,
    )
    ticker = _LiveTicker()
    ticker.start()

    archived = await service.archive_tenant(tenant.tenant_id)

    await ticker.stop()
    assert archived.status == "Archived"
    assert archived.archive_job_state == "completed"
    assert events.threads and threading.get_ident() not in events.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_scheduler_delivery_persists_state_off_the_loop():
    from app.repositories.simulation_event_repository import SimulationEventRepository
    from app.services.simulation_clock_service import SimulationClockService
    from app.services.simulation_event_recorder import SimulationEventRecorder
    from app.services.warp_scheduler import WarpScheduler

    class _RecordingEventRepository(SimulationEventRepository):
        def __init__(self) -> None:
            super().__init__()
            self.threads: list[int] = []

        def save_scheduler_state(self, state):
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)
            return super().save_scheduler_state(state)

    repo = SimulationRepository()
    events = _RecordingEventRepository()
    clock = SimulationClockService()
    tenant = clock.start_clock(_tenant(TENANT_FOUR), warp_speed=1.0)
    await repo.create(tenant)
    scheduler = WarpScheduler(
        signal_repository=SignalRepository(),
        event_repository=events,
        simulation_repository=repo,
        clock_service=clock,
        event_recorder=SimulationEventRecorder(events),
    )
    scheduler.initialize(
        tenant.tenant_id,
        [
            {
                "offset_seconds": 0.0,
                "signal_envelope": {"signal_id": "sig-0", "data_source_id": "ds-1", "category": "bushfire"},
            }
        ],
    )
    events.threads.clear()
    ticker = _LiveTicker()
    ticker.start()

    delivered = await scheduler.deliver_next_signal(tenant.tenant_id)

    await ticker.stop()
    assert delivered is True
    assert events.threads and threading.get_ident() not in events.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_storage_offload_helper_bounds_concurrent_threads(monkeypatch):
    monkeypatch.setenv("SIMULATION_STORAGE_IO_WORKERS", "3")
    state = {"in_flight": 0, "peak": 0}
    lock = threading.Lock()

    def _blocking_call():
        with lock:
            state["in_flight"] += 1
            state["peak"] = max(state["peak"], state["in_flight"])
        time.sleep(0.05)
        with lock:
            state["in_flight"] -= 1

    assert storage_io_limit() == 3
    await asyncio.gather(*(run_blocking(_blocking_call) for _ in range(12)))

    assert state["peak"] <= 3


@pytest.mark.asyncio
async def test_gather_bounded_preserves_result_order(monkeypatch):
    monkeypatch.setenv("SIMULATION_STORAGE_IO_WORKERS", "2")

    async def _value(index: int) -> int:
        await asyncio.sleep(0)
        return index

    assert await gather_bounded([_value(index) for index in range(5)]) == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Remaining AUD-031 surface: scheduler control, spec-036 repositories, sim chat.
# ---------------------------------------------------------------------------


def _scheduler_with_blocking_events():
    from app.repositories.simulation_event_repository import SimulationEventRepository
    from app.services.simulation_clock_service import SimulationClockService
    from app.services.simulation_event_recorder import SimulationEventRecorder
    from app.services.warp_scheduler import WarpScheduler

    class _BlockingEventRepository(SimulationEventRepository):
        def __init__(self) -> None:
            super().__init__()
            self.threads: list[int] = []

        def _block(self) -> None:
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)

        def get_scheduler_state(self, tenant_id):
            self._block()
            return super().get_scheduler_state(tenant_id)

        def save_scheduler_state(self, state):
            self._block()
            return super().save_scheduler_state(state)

        def get_scheduler_timeline(self, tenant_id):
            self._block()
            return super().get_scheduler_timeline(tenant_id)

    events = _BlockingEventRepository()
    scheduler = WarpScheduler(
        signal_repository=SignalRepository(),
        event_repository=events,
        simulation_repository=SimulationRepository(),
        clock_service=SimulationClockService(),
        event_recorder=SimulationEventRecorder(events),
    )
    return scheduler, events


@pytest.mark.asyncio
async def test_scheduler_control_offloads_state_writes():
    scheduler, events = _scheduler_with_blocking_events()
    scheduler.initialize(TENANT_ONE, [{"offset_seconds": 0.0, "signal_envelope": {"signal_id": "sig-0"}}])
    events.threads.clear()
    ticker = _LiveTicker()
    ticker.start()

    await scheduler.pause_async(TENANT_ONE)
    await scheduler.resume_async(TENANT_ONE)
    await scheduler.update_speed_async(TENANT_ONE, 10.0)

    await ticker.stop()
    assert events.threads and threading.get_ident() not in events.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_start_delivery_loop_async_offloads_the_timeline_cache_miss():
    scheduler, events = _scheduler_with_blocking_events()
    scheduler.initialize(TENANT_TWO, [{"offset_seconds": 0.0, "signal_envelope": {"signal_id": "sig-0"}}])
    scheduler._timelines.pop(TENANT_TWO)  # force the persisted-timeline read
    events.threads.clear()
    ticker = _LiveTicker()
    ticker.start()

    started = await scheduler.start_delivery_loop_async(TENANT_TWO)

    await ticker.stop()
    await scheduler.stop_delivery_loop(TENANT_TWO)
    assert started is True
    assert events.threads and threading.get_ident() not in events.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_start_delivery_loop_async_caches_an_empty_timeline():
    scheduler, events = _scheduler_with_blocking_events()

    assert await scheduler.start_delivery_loop_async("sim-unknown") is False
    events.threads.clear()

    # A second attempt must not re-read the store from the event loop.
    assert await scheduler.start_delivery_loop_async("sim-unknown") is False
    assert events.threads == []


@pytest.mark.asyncio
async def test_synthetic_signals_repository_offloads_cosmos_calls():
    from app.repositories.synthetic_signals_repository import SyntheticSignalsRepository

    from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

    container = _BlockingContainer()
    repo = SyntheticSignalsRepository(cosmos_client=_BlockingCosmosClient(container))
    signal = SyntheticSignal(
        signal_id="syn-1",
        simulation_id=TENANT_ONE,
        tenant_id=TENANT_ONE,
        category="weather",
        observed_at=datetime.now(UTC),
        freshness_window_seconds=600,
        confidence="high",
    )
    ticker = _LiveTicker()
    ticker.start()

    await repo.persist(signal)
    await repo.list_recent(TENANT_ONE, 600)

    await ticker.stop()
    assert len(container.threads) == 2
    assert threading.get_ident() not in container.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_idempotency_repository_offloads_cosmos_calls():
    from app.repositories.simulation_idempotency_repository import CacheMiss, IdempotencyCacheRepository

    class _NotFound(Exception):
        status_code = 404

    class _BlockingCacheContainer:
        def __init__(self) -> None:
            self.threads: list[int] = []

        def _block(self) -> None:
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)

        def read_item(self, item, partition_key):
            self._block()
            raise _NotFound()

        def upsert_item(self, document):
            self._block()
            return document

    container = _BlockingCacheContainer()
    repo = IdempotencyCacheRepository(cosmos_client=_BlockingCosmosClient(container))
    ticker = _LiveTicker()
    ticker.start()

    result = await repo.lookup_or_store(
        sim_id=TENANT_ONE,
        verb="pause",
        route=f"/api/simulations/{TENANT_ONE}/pause",
        idempotency_key="key-1",
        body={"reason": "drill"},
        rbac_subject_id="user-001",
        current_state="active",
        response_status=200,
        response_body={"status": "Paused"},
    )

    await ticker.stop()
    assert isinstance(result, CacheMiss)
    assert len(container.threads) == 2
    assert threading.get_ident() not in container.threads
    assert ticker.ticks > 1


@pytest.mark.asyncio
async def test_sequence_repository_offloads_under_the_shared_bound(monkeypatch):
    monkeypatch.setenv("SIMULATION_STORAGE_IO_WORKERS", "2")
    from app.repositories.simulation_sequence_repository import SimulationSequenceRepository

    class _CounterContainer:
        def __init__(self) -> None:
            self.threads: list[int] = []
            self.values: dict[str, int] = {}
            self.in_flight = 0
            self.peak = 0
            self._lock = threading.Lock()

        def _block(self) -> None:
            self.threads.append(threading.get_ident())
            with self._lock:
                self.in_flight += 1
                self.peak = max(self.peak, self.in_flight)
            time.sleep(0.02)
            with self._lock:
                self.in_flight -= 1

        def read_item(self, item, partition_key):
            self._block()
            return {"id": item, "value": self.values.get(item, 0), "_etag": "etag-1"}

        def create_item(self, body):  # pragma: no cover - bootstrap path unused here
            self._block()
            return {**body, "_etag": "etag-1"}

        def replace_item(self, item, body, if_match):
            self._block()
            self.values[item] = int(body["value"])
            return {"_etag": "etag-2"}

    container = _CounterContainer()
    repo = SimulationSequenceRepository(cosmos_client=_BlockingCosmosClient(container))

    results = await asyncio.gather(*(repo.allocate(f"sim-seq-{index}") for index in range(6)))

    assert results == [1, 1, 1, 1, 1, 1]
    assert container.threads and threading.get_ident() not in container.threads
    assert container.peak <= 2


@pytest.mark.asyncio
async def test_sim_chat_history_calls_are_offloaded_from_the_async_controller():
    from app.services.simulation.controller_service import SimulationControllerService

    from packages.domain.src.domain.models.sim_chat_turn import SimChatTurn

    class _BlockingHistory:
        def __init__(self) -> None:
            self.threads: list[int] = []
            self.turns: list[SimChatTurn] = []

        def _block(self) -> None:
            self.threads.append(threading.get_ident())
            time.sleep(BLOCK_SECONDS)

        def next_sequence(self, tenant_id):
            self._block()
            return len(self.turns) + 1

        def append_turn(self, turn):
            self._block()
            self.turns.append(turn)
            return turn

        def list_turns(self, tenant_id, *, limit=None):
            self._block()
            return list(self.turns)

    history = _BlockingHistory()
    controller = SimulationControllerService(history_repo=history, retrieval_service=object())
    ticker = _LiveTicker()
    ticker.start()

    persisted = await controller._persist_turn_async(
        tenant_id=TENANT_ONE,
        simulation_id=TENANT_ONE,
        role="user",
        content="status report",
        actor_oid="user-001",
    )
    messages = await controller._load_history_messages_async(TENANT_ONE)

    await ticker.stop()
    assert persisted is not None
    assert messages == [{"role": "user", "content": "status report"}]
    assert history.threads and threading.get_ident() not in history.threads
    assert ticker.ticks > 1
