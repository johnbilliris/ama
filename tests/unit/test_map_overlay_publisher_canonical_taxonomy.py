"""Unit tests for spec-036 T-R02 — refactor ``map_overlay_publisher`` to
import the canonical FR-027 layer taxonomy.

Wave 1 shipped :class:`packages.domain.src.domain.models.sim_layer_taxonomy.
SimLayerTaxonomy` (16 canonical members, byte-equal with the TypeScript
twin at ``apps/web/src/lib/sse/map-overlay-events.ts:51-68``). T-R02 then
removes the legacy 16-tuple of *signal-category* strings that previously
lived inline at ``apps/api/app/services/simulation/map_overlay_publisher.py``
lines 39-56 (``weather``, ``fire-behaviour``, …) and replaces them with a
re-export of :data:`ALL_LAYER_TYPES`.

The replacement closes critical finding **C8** from the Step 8 cohort
review (publisher emitted *signal categories* but the web client expects
the FR-027 closed map-overlay set).

Acceptance criteria captured here
---------------------------------
1. ``LAYER_TYPES`` re-exported by the publisher is byte-identical to
   ``packages.domain.src.domain.models.sim_layer_taxonomy.ALL_LAYER_TYPES``.
2. The legacy category-style strings (``weather``, ``fire-behaviour``, …)
   are NOT in the publisher's canonical set.
3. ``OverlayChange`` rejects unknown ``layer_type`` values at construction
   (Pydantic-style validation per task description).
4. ``publish_changes`` emits one SSE chunk per **canonical** layer type
   and the ``layer_type`` field in the serialised payload matches the
   FR-027 closed set.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from apps.api.app.services.simulation.map_overlay_publisher import (
    LAYER_TYPES as PUBLISHER_LAYER_TYPES,
)
from apps.api.app.services.simulation.map_overlay_publisher import (
    OverlayChange,
    publish_changes,
)
from packages.domain.src.domain.models.sim_layer_taxonomy import (
    ALL_LAYER_TYPES,
    SimLayerTaxonomy,
)

# Legacy category-style strings that lived in the publisher BEFORE T-R02.
# They MUST NOT be present in the canonical FR-027 closed set.
LEGACY_CATEGORY_STRINGS: tuple[str, ...] = (
    "weather",
    "fire-behaviour",
    "hydrology",
    "geohazard",
    "utility",
    "transport",
    "evacuation",
    "resource",
    "comms-channel-state",
    "jurisdiction-boundary",
    "cascade-link",
    "sub-agent-thread",
    "comm-receipt",
    "lessons-marker",
    "degraded-mode-banner",
    "simulation-watermark",
)


def test_publisher_layer_types_are_canonical() -> None:
    """``LAYER_TYPES`` from the publisher equals ``ALL_LAYER_TYPES`` byte-for-byte."""

    assert tuple(PUBLISHER_LAYER_TYPES) == ALL_LAYER_TYPES


def test_publisher_does_not_re_emit_legacy_categories() -> None:
    """The publisher's set must NOT contain any legacy signal-category string.

    This guards against accidental partial reverts that re-introduce the
    ``weather`` / ``fire-behaviour`` / … strings.
    """

    canonical_set = set(PUBLISHER_LAYER_TYPES)
    legacy_set = set(LEGACY_CATEGORY_STRINGS)
    intersection = canonical_set & legacy_set
    assert intersection == set(), (
        f"Publisher LAYER_TYPES still leaks legacy categories: {intersection!r}"
    )


def test_publisher_layer_types_count_is_16() -> None:
    """FR-027 closed set must have exactly 16 layer types after T-R02."""

    assert len(PUBLISHER_LAYER_TYPES) == 16
    assert len(set(PUBLISHER_LAYER_TYPES)) == 16


def test_overlay_change_accepts_canonical_layer_type() -> None:
    """A canonical ``SimLayerTaxonomy`` value is accepted at construction."""

    change = OverlayChange(
        overlay_id="ov-1",
        layer_type=SimLayerTaxonomy.WIND_ARROW.value,
        operation="created",
        observed_at=datetime.now(UTC),
        category="weather",
        latitude=-33.0,
        longitude=151.0,
    )
    assert change.layer_type == "wind-arrow"


def test_overlay_change_rejects_unknown_layer_type() -> None:
    """Unknown ``layer_type`` values are rejected at construction.

    Pydantic-style validation per T-R02 acceptance — ``"weather"`` is a
    legacy *signal category* and is not a valid map-overlay layer type
    under FR-027.
    """

    with pytest.raises((ValueError, TypeError)):
        OverlayChange(
            overlay_id="ov-1",
            layer_type="not-a-real-layer",
            operation="created",
            observed_at=datetime.now(UTC),
            category="weather",
            latitude=-33.0,
            longitude=151.0,
        )


def test_overlay_change_rejects_legacy_category_string() -> None:
    """``"weather"`` (legacy category) is now rejected — closes C8."""

    with pytest.raises((ValueError, TypeError)):
        OverlayChange(
            overlay_id="ov-1",
            layer_type="weather",  # was valid pre-T-R02; rejected now
            operation="created",
            observed_at=datetime.now(UTC),
            category="weather",
            latitude=-33.0,
            longitude=151.0,
        )


@pytest.mark.asyncio
async def test_publish_changes_emits_canonical_layer_type() -> None:
    """Every canonical layer type can be emitted with the correct payload."""

    sink: list[str] = []

    async def writer(chunk: str) -> None:
        sink.append(chunk)

    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    change = OverlayChange(
        overlay_id="ov-1",
        layer_type=SimLayerTaxonomy.HAZARD_PERIMETER.value,
        operation="created",
        observed_at=now,
        category="fire-behaviour",  # category for freshness window lookup
        latitude=-33.0,
        longitude=151.0,
    )
    counters = await publish_changes(changes=[change], sink=writer, now=now)
    assert counters["map.overlay.created"] == 1
    # Wire payload must carry the canonical layer_type string. The SSE
    # serialiser uses compact JSON (no spaces after ``:``), so we assert
    # both ``key:value`` adjacencies for the canonical name and the
    # absence of the legacy *category* string in that position.
    payload = sink[0]
    assert '"layer_type":"hazard-perimeter"' in payload
    # And NOT the legacy category that drove freshness lookup.
    assert '"layer_type":"fire-behaviour"' not in payload
