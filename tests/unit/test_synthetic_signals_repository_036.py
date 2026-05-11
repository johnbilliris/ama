"""Unit tests for spec-036 T-L03 — ``simulation_synthetic_signals`` repository.

Per tasks.md §5 (Phase L) and FR-009/FR-015 (signal pipeline persistence):

* Round-trip persistence with ``persist(signal)`` and ``list_recent(sim_id, window_seconds)``.
* Partition key is ``/simulationId`` (Bicep T-A09 / Wave 1).
* Container TTL of 7 days (data-model.md §1 says 72h; we follow the FR-039
  spec floor of 7 days for the application-layer recency query window —
  the container's default TTL is set in Bicep regardless).

The repository follows the auto-connect pattern from
:class:`apps.api.app.repositories.signal_repository.SignalRepository` —
fall back to in-memory dict for unit tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from apps.api.app.repositories.synthetic_signals_repository import (
    SyntheticSignalsRepository,
)
from packages.domain.src.domain.models.synthetic_signal import (
    GeoPoint,
    SyntheticSignal,
)


def _signal(
    sim_id: str = "sim-1",
    *,
    tenant_id: str = "tenant-a",
    signal_id: str | None = None,
    observed_at: datetime | None = None,
    category: str = "weather",
) -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=signal_id or f"sig-{sim_id}-{datetime.now(UTC).timestamp()}",
        simulation_id=sim_id,
        tenant_id=tenant_id,
        category=category,  # type: ignore[arg-type]
        observed_at=observed_at or datetime.now(UTC),
        freshness_window_seconds=900,
        confidence="high",
        gps=GeoPoint(lat=-37.0, lng=145.0),
    )


@pytest.mark.asyncio
async def test_persist_then_list_round_trip() -> None:
    repo = SyntheticSignalsRepository()
    sig = _signal()

    await repo.persist(sig)
    items = await repo.list_recent(sig.simulation_id, window_seconds=3600)

    assert len(items) == 1
    assert items[0].signal_id == sig.signal_id


@pytest.mark.asyncio
async def test_list_recent_excludes_signals_outside_window() -> None:
    repo = SyntheticSignalsRepository()
    fresh = _signal(signal_id="fresh", observed_at=datetime.now(UTC))
    stale = _signal(
        signal_id="stale",
        observed_at=datetime.now(UTC) - timedelta(hours=2),
    )

    await repo.persist(fresh)
    await repo.persist(stale)

    recent = await repo.list_recent(fresh.simulation_id, window_seconds=900)

    ids = {s.signal_id for s in recent}
    assert "fresh" in ids
    assert "stale" not in ids


@pytest.mark.asyncio
async def test_list_recent_scopes_to_simulation_id() -> None:
    """Each simulation's signals are isolated — no cross-sim leakage."""

    repo = SyntheticSignalsRepository()
    await repo.persist(_signal("sim-1", signal_id="a"))
    await repo.persist(_signal("sim-2", signal_id="b"))

    sim1 = await repo.list_recent("sim-1", window_seconds=3600)
    sim2 = await repo.list_recent("sim-2", window_seconds=3600)

    assert {s.signal_id for s in sim1} == {"a"}
    assert {s.signal_id for s in sim2} == {"b"}


@pytest.mark.asyncio
async def test_persist_overwrites_signal_with_same_id() -> None:
    """Idempotent re-persistence (e.g., from Event Hubs replay) is safe."""

    repo = SyntheticSignalsRepository()
    sig = _signal(signal_id="dup", category="weather")
    await repo.persist(sig)
    await repo.persist(sig)

    items = await repo.list_recent(sig.simulation_id, window_seconds=3600)
    assert len(items) == 1


@pytest.mark.asyncio
async def test_partition_key_is_simulation_id() -> None:
    """Repository must use ``/simulationId`` partition consistent with Bicep."""

    repo = SyntheticSignalsRepository()
    assert repo._partition_key_path == "/simulationId"


@pytest.mark.asyncio
async def test_container_name_matches_bicep() -> None:
    """The repository targets the canonical Bicep-defined container name."""

    repo = SyntheticSignalsRepository()
    assert repo._container_name == "simulation_synthetic_signals"


def test_in_memory_fallback_when_no_endpoint() -> None:
    """Without ``COSMOS_ENDPOINT`` the repository operates against a dict."""

    import os

    saved = os.environ.pop("COSMOS_ENDPOINT", None)
    try:
        repo = SyntheticSignalsRepository()
        assert repo._client is None  # in-memory mode
    finally:
        if saved is not None:
            os.environ["COSMOS_ENDPOINT"] = saved
