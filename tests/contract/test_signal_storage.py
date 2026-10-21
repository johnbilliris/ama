from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from packages.domain.src.domain.models.signal import Signal
from packages.domain.src.domain.repositories.signal_repository import (
    SIGNALS_STORE,
    SignalRepository,
)
from packages.domain.src.domain.repositories.signal_wire import partition_key_of, to_signal_document


@pytest.fixture(autouse=True)
def clean_store():
    SIGNALS_STORE.clear()
    yield
    SIGNALS_STORE.clear()


@pytest.fixture
def repo():
    return SignalRepository(cosmos_client=None)


def make_signal(
    signal_id: str = "sig-001",
    incident_id: str | None = "inc-001",
    jurisdiction_id: str = "nsw",
    data_source_id: str = "bom-warnings",
    category: str = "weather",
) -> Signal:
    return Signal(
        signal_id=signal_id,
        incident_id=incident_id,
        data_source_id=data_source_id,
        category=category,
        occurred_at=datetime.now(UTC),
        received_at=datetime.now(UTC),
        jurisdiction_id=jurisdiction_id,
        location={"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        payload={"headline": "Storm warning"},
        classification="official",
        retention_until=datetime.now(UTC),
        confidence_score=0.95,
        freshness_score=0.9,
        validation_status="validated",
        provenance={"collectionMethod": "api_pull", "sourceUri": "https://example.com"},
    )


class TestSignalRepository:
    @pytest.mark.asyncio
    async def test_save_and_query_by_incident(self, repo):
        signal = make_signal()
        await repo.save(signal)
        results = await repo.query_by_incident("inc-001", scope="live")
        assert len(results) == 1
        assert results[0].signal_id == "sig-001"

    @pytest.mark.asyncio
    async def test_partition_isolation_by_jurisdiction(self, repo):
        nsw_signal = make_signal(signal_id="sig-nsw", jurisdiction_id="nsw")
        vic_signal = make_signal(signal_id="sig-vic", jurisdiction_id="vic")
        await repo.save(nsw_signal)
        await repo.save(vic_signal)

        nsw_results = await repo.query_by_jurisdiction("nsw", scope="live")
        vic_results = await repo.query_by_jurisdiction("vic", scope="live")
        assert any(s.signal_id == "sig-nsw" for s in nsw_results)
        assert not any(s.signal_id == "sig-vic" for s in nsw_results)
        assert any(s.signal_id == "sig-vic" for s in vic_results)

    @pytest.mark.asyncio
    async def test_simulation_scope_isolation(self, repo):
        live_signal = make_signal(signal_id="sig-live")
        sim_signal = make_signal(signal_id="sig-sim")
        await repo.save(live_signal, scope="live")
        await repo.save(sim_signal, scope="sim_run-001")

        live_results = await repo.query_by_incident("inc-001", scope="live")
        sim_results = await repo.query_by_incident("inc-001", scope="sim_run-001")

        live_ids = {s.signal_id for s in live_results}
        sim_ids = {s.signal_id for s in sim_results}
        assert "sig-live" in live_ids
        assert "sig-sim" not in live_ids
        assert "sig-sim" in sim_ids

    @pytest.mark.asyncio
    async def test_national_signal_fanout(self, repo):
        signal = make_signal(signal_id="sig-national", jurisdiction_id="national")
        await repo.save_with_fanout(signal, affected_jurisdiction_ids=["nsw", "vic", "qld"])

        assert ("live", "sig-national") in SIGNALS_STORE
        assert ("live", "sig-national:ref:nsw") in SIGNALS_STORE
        assert ("live", "sig-national:ref:vic") in SIGNALS_STORE
        nsw = await repo.query_by_jurisdiction("nsw", scope="live")
        vic = await repo.query_by_jurisdiction("vic", scope="live")
        assert any(s.signal_id == "sig-national:ref:nsw" for s in nsw)
        assert any(s.signal_id == "sig-national:ref:vic" for s in vic)

    @pytest.mark.asyncio
    async def test_query_unassociated_signals(self, repo):
        unassoc = make_signal(signal_id="sig-unassoc", incident_id=None)
        assoc = make_signal(signal_id="sig-assoc", incident_id="inc-001")
        await repo.save(unassoc)
        await repo.save(assoc)

        results = await repo.query_unassociated("nsw", since=datetime.min.replace(tzinfo=UTC), scope="live")
        assert any(s.signal_id == "sig-unassoc" for s in results)
        assert not any(s.signal_id == "sig-assoc" for s in results)

    @pytest.mark.asyncio
    async def test_update_incident_id(self, repo):
        signal = make_signal(signal_id="sig-update", incident_id=None)
        await repo.save(signal)
        assert SIGNALS_STORE[("live", "sig-update")].incident_id is None

        await repo.update_incident_id("sig-update", "inc-new", scope="live")
        assert SIGNALS_STORE[("live", "sig-update")].incident_id == "inc-new"

    @pytest.mark.asyncio
    async def test_same_signal_id_in_multiple_scopes_remains_isolated(self, repo):
        live_signal = make_signal(signal_id="sig-dup", incident_id="inc-live")
        sim_signal = make_signal(signal_id="sig-dup", incident_id="inc-sim")

        await repo.save(live_signal, scope="live")
        await repo.save(sim_signal, scope="sim_run-003")

        live_results = await repo.query_by_incident("inc-live", scope="live")
        sim_results = await repo.query_by_incident("inc-sim", scope="sim_run-003")

        assert len(live_results) == 1
        assert len(sim_results) == 1
        assert live_results[0].incident_id == "inc-live"
        assert sim_results[0].incident_id == "inc-sim"

    @pytest.mark.asyncio
    async def test_same_signal_id_is_isolated_across_live_and_three_simulation_scopes(self, repo):
        scopes = {
            "live": "inc-live",
            "sim-run-1": "inc-sim-1",
            "sim-run-2": "inc-sim-2",
            "sim-run-3": "inc-sim-3",
        }

        for scope, incident_id in scopes.items():
            await repo.save(make_signal(signal_id="sig-shared", incident_id=incident_id), scope=scope)

        for scope, incident_id in scopes.items():
            results = await repo.query_by_incident(incident_id, scope=scope)
            assert len(results) == 1
            assert results[0].signal_id == "sig-shared"
            assert results[0].incident_id == incident_id


def test_signal_wire_hpk_keys_align_with_bicep_partition_paths() -> None:
    signal = make_signal(signal_id="sig-wire")
    document = to_signal_document(signal, "live")
    partition_paths = set(partition_key_of(document))

    bicep = Path("infra/main.bicep").read_text(encoding="utf-8")
    assert "paths: ['/scope', '/jurisdictionId', '/dataSourceId']" in bicep
    assert partition_paths == {"live", "nsw", "bom-warnings"}
    assert document["scope"] == "live"
    assert document["jurisdictionId"] == "nsw"
    assert document["dataSourceId"] == "bom-warnings"


class _FakeAsyncItems:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows
        self._idx = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx >= len(self._rows):
            raise StopAsyncIteration
        row = self._rows[self._idx]
        self._idx += 1
        return row


class _FakeCosmosContainer:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def query_items(self, **_: Any) -> _FakeAsyncItems:
        return _FakeAsyncItems(self._rows)


class _FakeCosmosDatabase:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def get_container_client(self, _: str) -> _FakeCosmosContainer:
        return _FakeCosmosContainer(self._rows)


class _FakeCosmosClient:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def get_database_client(self, _: str) -> _FakeCosmosDatabase:
        return _FakeCosmosDatabase(self._rows)


class _FailingReadContainer:
    def read_item(self, **_: Any) -> dict[str, Any]:
        raise RuntimeError("cosmos unavailable")


class _FailingReadDatabase:
    def get_container_client(self, _: str) -> _FailingReadContainer:
        return _FailingReadContainer()


class _FailingReadClient:
    def get_database_client(self, _: str) -> _FailingReadDatabase:
        return _FailingReadDatabase()


def _make_cosmos_row(signal_id: str, *, incident_id: str | None) -> dict[str, Any]:
    scope = "live"
    signal = make_signal(signal_id=signal_id, incident_id=incident_id)
    return to_signal_document(signal, scope)


@pytest.mark.asyncio
async def test_query_by_incident_caps_total_results_across_fake_cosmos_pages() -> None:
    rows = [_make_cosmos_row(f"sig-{idx:02d}", incident_id="inc-cap") for idx in range(9)]
    repo = SignalRepository(cosmos_client=_FakeCosmosClient(rows))

    results = await repo.query_by_incident("inc-cap", scope="live", limit=5)

    assert len(results) == 5
    assert all(signal.incident_id == "inc-cap" for signal in results)


@pytest.mark.asyncio
async def test_query_unassociated_limit_matches_memory_and_cosmos_cap() -> None:
    now = datetime.now(UTC)

    memory_repo = SignalRepository(cosmos_client=None)
    for idx in range(7):
        await memory_repo.save(
            make_signal(
                signal_id=f"mem-{idx}",
                incident_id=None,
                jurisdiction_id="nsw",
            ),
            scope="live",
        )

    memory_results = await memory_repo.query_unassociated(
        "nsw",
        since=now.replace(year=2000),
        scope="live",
        limit=4,
    )
    assert len(memory_results) == 4

    cosmos_rows = [_make_cosmos_row(f"cos-{idx}", incident_id=None) for idx in range(7)]
    cosmos_repo = SignalRepository(cosmos_client=_FakeCosmosClient(cosmos_rows))
    cosmos_results = await cosmos_repo.query_unassociated(
        "nsw",
        since=now.replace(year=2000),
        scope="live",
        limit=4,
    )

    assert len(cosmos_results) == 4


@pytest.mark.asyncio
async def test_domain_hpk_read_propagates_cosmos_service_failure() -> None:
    repo = SignalRepository(cosmos_client=_FailingReadClient())

    with pytest.raises(RuntimeError, match="cosmos unavailable"):
        await repo.get_by_hpk(
            signal_id="sig-1",
            scope="live",
            jurisdiction_id="nsw",
            data_source_id="bom-warnings",
        )
