import asyncio
from datetime import UTC, datetime

import pytest

from packages.domain.src.domain.repositories.signal_repository import SignalRepository, SIGNALS_STORE, _SIGNAL_SCOPES
from packages.domain.src.domain.models.signal import Signal


@pytest.fixture(autouse=True)
def clean_store():
    SIGNALS_STORE.clear()
    _SIGNAL_SCOPES.clear()
    yield
    SIGNALS_STORE.clear()
    _SIGNAL_SCOPES.clear()


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
        results = await repo.query_by_incident("inc-001")
        assert len(results) == 1
        assert results[0].signal_id == "sig-001"

    @pytest.mark.asyncio
    async def test_partition_isolation_by_jurisdiction(self, repo):
        nsw_signal = make_signal(signal_id="sig-nsw", jurisdiction_id="nsw")
        vic_signal = make_signal(signal_id="sig-vic", jurisdiction_id="vic")
        await repo.save(nsw_signal)
        await repo.save(vic_signal)

        nsw_results = await repo.query_by_jurisdiction("nsw")
        vic_results = await repo.query_by_jurisdiction("vic")
        assert any(s.signal_id == "sig-nsw" for s in nsw_results)
        assert not any(s.signal_id == "sig-vic" for s in nsw_results)

    @pytest.mark.asyncio
    async def test_simulation_scope_isolation(self, repo):
        live_signal = make_signal(signal_id="sig-live")
        sim_signal = make_signal(signal_id="sig-sim")
        await repo.save(live_signal, scope="live")
        await repo.save(sim_signal, scope="sim_run-001")

        live_results = await repo.query_by_incident("inc-001", scope="live")
        sim_results = await repo.query_by_incident("inc-001", scope="sim_run-001")

        live_ids = {s.signal_id for s in live_results}
        assert "sig-live" in live_ids
        assert "sig-sim" not in live_ids

    @pytest.mark.asyncio
    async def test_national_signal_fanout(self, repo):
        signal = make_signal(signal_id="sig-national", jurisdiction_id="national")
        await repo.save_with_fanout(signal, affected_jurisdiction_ids=["nsw", "vic", "qld"])

        assert "sig-national" in SIGNALS_STORE
        nsw = await repo.query_by_jurisdiction("nsw")
        assert any(s.signal_id == "sig-national" for s in nsw)

    @pytest.mark.asyncio
    async def test_query_unassociated_signals(self, repo):
        unassoc = make_signal(signal_id="sig-unassoc", incident_id=None)
        assoc = make_signal(signal_id="sig-assoc", incident_id="inc-001")
        await repo.save(unassoc)
        await repo.save(assoc)

        results = await repo.query_unassociated("nsw", since=datetime.min.replace(tzinfo=UTC))
        assert any(s.signal_id == "sig-unassoc" for s in results)
        assert not any(s.signal_id == "sig-assoc" for s in results)

    @pytest.mark.asyncio
    async def test_update_incident_id(self, repo):
        signal = make_signal(signal_id="sig-update", incident_id=None)
        await repo.save(signal)
        assert SIGNALS_STORE["sig-update"].incident_id is None

        await repo.update_incident_id("sig-update", "inc-new")
        assert SIGNALS_STORE["sig-update"].incident_id == "inc-new"
