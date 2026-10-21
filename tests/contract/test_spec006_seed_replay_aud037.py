from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.services.scenario_seeding_service import ScenarioSeedingService


class _SignalRepo:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.created: list[dict] = []

    async def list_by_tenant(self, tenant_id: str, limit: int = 20, offset: int = 0, **_kwargs):
        assert tenant_id == "live"
        batch = self.rows[offset : offset + limit]
        return batch, len(self.rows)

    async def save(self, signal, *, scope: str):  # noqa: ANN001, ANN202
        self.created.append({"tenant_id": scope, **signal.model_dump(mode="json")})


class _Scheduler:
    def __init__(self) -> None:
        self.initialized: list[tuple[str, list[dict], float]] = []

    def initialize(self, tenant_id: str, timeline: list[dict], warp_speed: float = 1.0) -> None:
        self.initialized.append((tenant_id, timeline, warp_speed))

    def start_delivery_loop(self, tenant_id: str) -> bool:
        return True


def _row(incident: str, ts: datetime) -> dict:
    return {
        "id": f"sig-{ts.timestamp()}",
        "signal_id": f"sig-{ts.timestamp()}",
        "incident_id": incident,
        "occurred_at": ts.isoformat(),
        "source": {"dataSourceId": "bom-warnings", "kind": "authoritative", "name": "BoM"},
        "category": "weather",
        "receivedAt": ts.isoformat(),
        "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        "payload": {"title": "x"},
        "confidenceScore": 0.9,
        "freshnessScore": 0.9,
        "validationStatus": "validated",
        "provenance": {"collectionMethod": "api_pull", "sourceUri": "x"},
    }


def test_missing_repository_dependency_fails_fast() -> None:
    with pytest.raises(ValueError, match="requires a signal_repository"):
        ScenarioSeedingService(signal_repository=None)  # type: ignore[arg-type]


def test_seed_from_replay_applies_time_window_and_offsets() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        _row("inc-1", start - timedelta(minutes=10)),
        _row("inc-1", start + timedelta(minutes=5)),
        _row("inc-1", start + timedelta(minutes=10)),
        _row("inc-2", start + timedelta(minutes=6)),
    ]
    repo = _SignalRepo(rows)
    scheduler = _Scheduler()
    service = ScenarioSeedingService(signal_repository=repo, cosmos_client=object(), warp_scheduler=scheduler)

    result = asyncio.run(
        service.seed_from_replay(
            "sim-tenant",
            "inc-1",
            start.isoformat(),
            (start + timedelta(minutes=10)).isoformat(),
            time_compression=2.0,
        )
    )

    assert result["signals_injected"] == 0
    assert result["signals_scheduled"] == 2
    assert len(repo.created) == 0
    assert scheduler.initialized
    _, timeline, warp = scheduler.initialized[0]
    assert warp == 2.0
    assert timeline[0]["offset_seconds"] == 150
    assert timeline[1]["offset_seconds"] == 300
    assert len({row["signal_envelope"]["incident_id"] for row in timeline}) == 1
    assert timeline[0]["signal_envelope"]["incident_id"].startswith("siminc-")
    rows[1]["payload"]["title"] = "mutated-live"
    assert timeline[0]["signal_envelope"]["payload"]["title"] == "x"


def test_seed_from_replay_paginates_over_10k_records() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [_row("inc-big", start + timedelta(seconds=i)) for i in range(10050)]
    repo = _SignalRepo(rows)
    service = ScenarioSeedingService(signal_repository=repo, cosmos_client=object(), warp_scheduler=_Scheduler())

    result = asyncio.run(
        service.seed_from_replay(
            "sim-big",
            "inc-big",
            start.isoformat(),
            (start + timedelta(seconds=10049)).isoformat(),
            time_compression=1.0,
        )
    )

    assert result["signals_injected"] == 0
    assert result["signals_scheduled"] == 10000
    assert len(repo.created) == 0
