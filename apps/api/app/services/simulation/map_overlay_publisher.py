"""Map-overlay publisher (T-D11 / FR-027 / T-R02).

Listens on the ``simulation_synthetic_signals`` Cosmos change feed and emits
``map.overlay.{created,updated,stale,cluster,removed}`` SSE events keyed
by the **16 canonical layer types** from
``contracts/sse-map-overlay.md §2``.

Spec-036 amendment-cycle T-R02 (closes C8 — layer-taxonomy mismatch)
-------------------------------------------------------------------
Pre-amendment this module embedded its own 16-tuple of *signal-category*
strings (``weather``, ``fire-behaviour``, …) which collided with the FR-027
*map-overlay* closed set the web client expects (``wind-arrow``,
``hazard-perimeter``, …).  T-R01 introduced the canonical
:class:`packages.domain.src.domain.models.sim_layer_taxonomy.SimLayerTaxonomy`
StrEnum; this module now re-exports it via :data:`LAYER_TYPES` so existing
callers/tests remain source-compatible while the *values* migrate.

Stale overlays are detected by comparing
``now() - signal.observed_at`` to ``FRESHNESS_WINDOW_SECONDS[category]``
(see ``apps/api/app/config/signal_freshness.py``). Cluster events are
emitted when ``≥3`` overlays of the same ``layer_type`` fall within a
~5 km grid cell — implemented as a 0.05° equi-rectangular bucket which
is good enough for AU-mainland latitudes (the production geohash bucket
will be wired in Phase G alongside the STRtree builder).

Note that ``layer_type`` (canonical FR-027 enum) and ``category`` (signal
freshness key — still ``weather``/``fire-behaviour``/…) remain distinct
concerns: the former drives the wire format expected by the web client,
the latter drives the freshness-window lookup table.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from typing import Any

from app.config.signal_freshness import (
    FRESHNESS_WINDOW_SECONDS,
    is_signal_stale,
)
from app.services.simulation.sse_sub_agent_events import format_sse_event
from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.domain.src.domain.models.sim_layer_taxonomy import (
    ALL_LAYER_TYPES,
    SimLayerTaxonomy,
)

logger = logging.getLogger(__name__)


#: Re-export of the canonical FR-027 closed-set (16 members) for callers
#: that historically imported ``LAYER_TYPES`` from this module. The single
#: source of truth lives at
#: ``packages/domain/src/domain/models/sim_layer_taxonomy.py``.
LAYER_TYPES: tuple[str, ...] = ALL_LAYER_TYPES

# 16 layer types — must match contracts/sse-map-overlay.md §2 exactly.
assert len(LAYER_TYPES) == 16


CLUSTER_THRESHOLD = 3
CLUSTER_GRID_DEGREES = 0.05  # ≈ 5 km at AU-mainland latitudes


class OverlayChange(BaseModel):
    """Normalised view of a single change-feed mutation.

    Pydantic-validated per T-R02 acceptance: ``layer_type`` MUST be a
    member of :class:`SimLayerTaxonomy` (the FR-027 closed set). Unknown
    values raise :class:`pydantic.ValidationError` at construction time
    rather than being silently dropped on emit (the previous behaviour).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    overlay_id: str
    layer_type: str
    operation: str  # one of "created", "updated", "removed"
    observed_at: datetime
    category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    origin_cascade_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("layer_type")
    @classmethod
    def _validate_layer_type(cls, value: str) -> str:
        # Compare against the canonical taxonomy. We accept the raw string
        # (StrEnum value) rather than the enum member so callers can pass
        # either form.
        if value not in ALL_LAYER_TYPES:
            raise ValueError(
                f"layer_type {value!r} is not a member of the FR-027 "
                f"canonical taxonomy. Valid values: {ALL_LAYER_TYPES!r}."
            )
        return value


PublisherSink = Callable[[str], Awaitable[None]]
"""Sink that receives the formatted SSE chunk (``event: …\ndata: …\n\n``)."""


def _grid_cell(latitude: float, longitude: float) -> tuple[int, int]:
    """Project lat/lon into a deterministic ~5 km bucket."""
    return (
        int(latitude // CLUSTER_GRID_DEGREES),
        int(longitude // CLUSTER_GRID_DEGREES),
    )


def detect_clusters(
    changes: Iterable[OverlayChange],
) -> list[dict[str, Any]]:
    """Group overlays by layer-type + grid cell, return cluster summaries."""
    buckets: dict[tuple[str, tuple[int, int]], list[OverlayChange]] = defaultdict(list)
    for c in changes:
        if c.latitude is None or c.longitude is None:
            continue
        buckets[(c.layer_type, _grid_cell(c.latitude, c.longitude))].append(c)
    out: list[dict[str, Any]] = []
    for (layer_type, cell), members in buckets.items():
        if len(members) >= CLUSTER_THRESHOLD:
            out.append(
                {
                    "layer_type": layer_type,
                    "grid_cell": list(cell),
                    "member_overlay_ids": [m.overlay_id for m in members],
                    "size": len(members),
                }
            )
    return out


def is_stale(change: OverlayChange, *, now: datetime | None = None) -> bool:
    if change.category is None:
        return False
    return is_signal_stale(
        category=change.category,
        observed_at=change.observed_at,
        now=now,
    )


async def publish_changes(
    *,
    changes: Iterable[OverlayChange],
    sink: PublisherSink,
    now: datetime | None = None,
) -> dict[str, int]:
    """Emit one SSE chunk per relevant overlay state and return counters.

    All ``OverlayChange`` instances are guaranteed to carry a canonical
    ``layer_type`` (validated at construction). The legacy warn-and-skip
    branch for unknown values is therefore unreachable; we keep a defensive
    log entry as a belt-and-braces guard if the canonical set is ever
    mutated at runtime via monkey-patching.
    """
    now = now or datetime.now(UTC)
    counters: Counter[str] = Counter()

    materialised: list[OverlayChange] = list(changes)
    for change in materialised:
        if change.layer_type not in LAYER_TYPES:  # defensive — see docstring
            logger.warning("map_overlay.unknown_layer_type %s", change.layer_type)
            continue

        event_name = f"map.overlay.{change.operation}"
        payload = {
            "overlay_id": change.overlay_id,
            "layer_type": change.layer_type,
            "observed_at": change.observed_at.isoformat(),
            "origin_cascade_id": change.origin_cascade_id,
            **change.extra,
        }
        await sink(format_sse_event(event_name, payload))
        counters[event_name] += 1

        if is_stale(change, now=now):
            stale_payload = {
                "overlay_id": change.overlay_id,
                "layer_type": change.layer_type,
                "observed_at": change.observed_at.isoformat(),
                "freshness_window_seconds": FRESHNESS_WINDOW_SECONDS.get(change.category or "", None),
            }
            await sink(format_sse_event("map.overlay.stale", stale_payload))
            counters["map.overlay.stale"] += 1

    for cluster in detect_clusters(materialised):
        await sink(format_sse_event("map.overlay.cluster", cluster))
        counters["map.overlay.cluster"] += 1

    return dict(counters)


__all__ = [
    "ALL_LAYER_TYPES",
    "CLUSTER_GRID_DEGREES",
    "CLUSTER_THRESHOLD",
    "LAYER_TYPES",
    "OverlayChange",
    "SimLayerTaxonomy",
    "detect_clusters",
    "is_stale",
    "publish_changes",
]
