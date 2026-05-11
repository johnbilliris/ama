"""Canonical 16-layer map-overlay taxonomy (spec-036 T-R01, FR-027).

The :class:`SimLayerTaxonomy` ``StrEnum`` is the **single Python source of
truth** for the closed-set of map-overlay ``layer_type`` values defined by
``specs/036-sim-agent-extend/contracts/sse-map-overlay.md §2``. The
TypeScript twin lives at
``apps/web/src/lib/sse/map-overlay-events.ts`` and MUST stay byte-aligned
with this enum — the alignment is asserted by
``tests/unit/test_sim_layer_taxonomy.py`` and the contract test in T-R06
(Wave 2).

Migration plan
--------------
* T-R01 (this file) — define the canonical Python enum.
* T-R02 (Wave 2)   — refactor ``map_overlay_publisher.py`` to import from
  here, replacing the local ``LAYER_TYPES`` tuple at lines 39-56.
* T-R03 (Wave 2)   — regenerate ``map-overlay-events.ts`` via codegen
  step seeded from :func:`layer_taxonomy_json_schema`.
* T-D11 [AMEND]    — refactor ``map_overlay_publisher`` taxonomy publisher
  to use this enum once T-R02 has shipped.

Refs
----
- specs/036-sim-agent-extend/contracts/sse-map-overlay.md §2
- specs/036-sim-agent-extend/spec.md FR-027
- specs/036-sim-agent-extend/tasks.md §11 T-R01
- apps/web/src/lib/sse/map-overlay-events.ts (TS twin)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Final


class SimLayerTaxonomy(StrEnum):
    """The 16 canonical map-overlay layer types (FR-027).

    Order matches the TypeScript ``MAP_OVERLAY_LAYER_TYPES`` literal at
    ``apps/web/src/lib/sse/map-overlay-events.ts:51-68`` exactly. Adding,
    removing, or reordering values here MUST be paired with a matching
    update to that TS file (the contract test will fail otherwise).
    """

    WIND_ARROW = "wind-arrow"
    HAZARD_PERIMETER = "hazard-perimeter"
    EVACUATION_ROUTE = "evacuation-route"
    RESOURCE_PIN = "resource-pin"
    EVAC_CENTRE_PIN = "evac-centre-pin"
    UTILITY_OUTAGE_ZONE = "utility-outage-zone"
    TC_TRACK_AND_CONE = "tc-track-and-cone"
    ROAD_CLOSURE_AND_ALT_ROUTE = "road-closure-and-alt-route"
    VESSEL_OR_AIRCRAFT_POSITION = "vessel-or-aircraft-position"
    AIRSPACE_RESTRICTION = "airspace-restriction"
    MARITIME_EXCLUSION = "maritime-exclusion"
    HOSPITAL_SURGE = "hospital-surge"
    REMOTE_COMMUNITY_ACCESS = "remote-community-access"
    VOLUNTEER_STAGING = "volunteer-staging"
    GEOHAZARD_ZONE = "geohazard-zone"
    FLOOD_POLYGON = "flood-polygon"


#: Materialised tuple of every layer-type string in source order. Cheaper
#: than iterating the enum at runtime in publish hot paths.
ALL_LAYER_TYPES: Final[tuple[str, ...]] = tuple(member.value for member in SimLayerTaxonomy)

# Closed-set guard — the spec is normative on the cardinality.
assert len(ALL_LAYER_TYPES) == 16, (
    f"FR-027 requires exactly 16 layer types; got {len(ALL_LAYER_TYPES)}"
)


def layer_taxonomy_json_schema() -> dict[str, Any]:
    """Return a JSON Schema document describing the closed-set enum.

    Used by the codegen step in T-R03 to regenerate the TypeScript twin.
    The returned dict is intentionally a fresh shallow copy so callers may
    mutate it without contaminating subsequent calls.
    """

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ama.local/schemas/sim-layer-taxonomy.json",
        "title": "SimLayerTaxonomy",
        "description": (
            "Closed-set of 16 canonical map-overlay layer types per FR-027. "
            "Source of truth: packages/domain/src/domain/models/sim_layer_taxonomy.py."
        ),
        "type": "string",
        "enum": list(ALL_LAYER_TYPES),
    }


__all__ = [
    "ALL_LAYER_TYPES",
    "SimLayerTaxonomy",
    "layer_taxonomy_json_schema",
]
