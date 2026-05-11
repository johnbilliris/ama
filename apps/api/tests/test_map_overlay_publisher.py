"""Phase D — map-overlay publisher tests (T-D11 / FR-027 / T-R02).

Spec-036 amendment-cycle T-R02 closed C8 (layer-taxonomy mismatch) by
re-pointing the publisher at the canonical
:class:`packages.domain.src.domain.models.sim_layer_taxonomy.SimLayerTaxonomy`
StrEnum. These tests use canonical FR-027 layer-type values
(``wind-arrow``, ``hazard-perimeter``, …) — the legacy *signal-category*
strings (``weather``, ``fire-behaviour``) now travel exclusively through
the ``category`` field which keys the freshness-window lookup.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from apps.api.app.services.simulation.map_overlay_publisher import (
    LAYER_TYPES,
    OverlayChange,
    detect_clusters,
    is_stale,
    publish_changes,
)
from packages.domain.src.domain.models.sim_layer_taxonomy import (
    SimLayerTaxonomy,
)


def test_layer_types_count_is_16() -> None:
    """FR-027 declares exactly 16 SSE map-overlay layer types."""
    assert len(LAYER_TYPES) == 16
    assert len(set(LAYER_TYPES)) == 16  # unique


def test_is_stale_true_when_observed_old() -> None:
    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    change = OverlayChange(
        overlay_id="ov-1",
        layer_type=SimLayerTaxonomy.WIND_ARROW.value,
        operation="created",
        observed_at=now - timedelta(seconds=400),
        category="weather",  # 300 s window
        latitude=-33.0,
        longitude=151.0,
    )
    assert is_stale(change, now=now) is True


def test_is_stale_false_when_within_window() -> None:
    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    change = OverlayChange(
        overlay_id="ov-1",
        layer_type=SimLayerTaxonomy.WIND_ARROW.value,
        operation="created",
        observed_at=now - timedelta(seconds=100),
        category="weather",
        latitude=-33.0,
        longitude=151.0,
    )
    assert is_stale(change, now=now) is False


def test_detect_clusters_emits_when_threshold_reached() -> None:
    base = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    changes = [
        OverlayChange(
            overlay_id=f"ov-{i}",
            layer_type=SimLayerTaxonomy.HAZARD_PERIMETER.value,
            operation="created",
            observed_at=base,
            category="fire-behaviour",
            latitude=-33.05 + (i * 0.001),
            longitude=151.05 + (i * 0.001),
        )
        for i in range(3)
    ]
    clusters = detect_clusters(changes)
    assert len(clusters) == 1
    assert clusters[0]["layer_type"] == "hazard-perimeter"
    assert clusters[0]["size"] == 3


def test_detect_clusters_below_threshold() -> None:
    base = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    changes = [
        OverlayChange(
            overlay_id=f"ov-{i}",
            layer_type=SimLayerTaxonomy.WIND_ARROW.value,
            operation="created",
            observed_at=base,
            category="weather",
            latitude=-33.0,
            longitude=151.0,
        )
        for i in range(2)
    ]
    assert detect_clusters(changes) == []


@pytest.mark.asyncio
async def test_publish_changes_emits_per_event_and_stale_when_old() -> None:
    sink: list[str] = []

    async def writer(chunk: str) -> None:
        sink.append(chunk)

    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    changes = [
        OverlayChange(
            overlay_id="ov-1",
            layer_type=SimLayerTaxonomy.WIND_ARROW.value,
            operation="created",
            observed_at=now,
            category="weather",
            latitude=-33.0,
            longitude=151.0,
        ),
        OverlayChange(
            overlay_id="ov-2",
            layer_type=SimLayerTaxonomy.HAZARD_PERIMETER.value,
            operation="updated",
            observed_at=now - timedelta(seconds=400),
            category="fire-behaviour",
            latitude=-33.0,
            longitude=151.0,
        ),
    ]
    counters = await publish_changes(changes=changes, sink=writer, now=now)
    assert counters["map.overlay.created"] == 1
    assert counters["map.overlay.updated"] == 1
    assert counters["map.overlay.stale"] == 1
    assert all(chunk.startswith("event: map.overlay.") for chunk in sink)


def test_overlay_change_rejects_unknown_layer_type_at_construction() -> None:
    """T-R02 — Pydantic validation rejects non-canonical layer_type values.

    The legacy warn-and-skip-on-publish behaviour is replaced by fail-fast
    construction so the change-feed projection observes the closed set in
    every materialised :class:`OverlayChange` it emits.
    """
    with pytest.raises(ValueError):
        OverlayChange(
            overlay_id="ov-X",
            layer_type="not-a-real-layer",
            operation="created",
            observed_at=datetime.now(UTC),
            category="weather",
            latitude=-33.0,
            longitude=151.0,
        )
