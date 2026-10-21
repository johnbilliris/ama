/**
 * Spec-036 T-I04 — `simulation-map` discriminated-union dispatch tests.
 *
 * The 16 layer types in `MAP_OVERLAY_LAYER_TYPES` are exercised one-by-one
 * to satisfy the FR-027 closed-set contract. The test fails at compile
 * time if any layer is missing because the helper relies on
 * `assertNever` for exhaustiveness.
 */
import { describe, expect, it } from "vitest";

import {
  applyMapOverlayEvents,
  renderMapOverlayEvent,
  type SimulationOverlayFeature,
} from "@/lib/sse/map-overlay-dispatch";
import {
  MAP_OVERLAY_LAYER_TYPES,
  type MapOverlayEvent,
  type MapOverlayLayerType,
} from "@/lib/sse/map-overlay-events";

function baseEvent(layerType: MapOverlayLayerType): MapOverlayEvent {
   
  const skeleton: any = {
    event_type: "map.overlay.created",
    sim_id: "sim-1",
    overlay_id: `over-${layerType}`,
    sim_badge: "[SIMULATION]",
    visual_modifier: "dashed",
    timestamp: "2026-05-08T00:00:00Z",
    layer_type: layerType,
  };
  switch (layerType) {
    case "wind-arrow":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.bearing_deg = 90;
      skeleton.speed_kmh = 30;
      break;
    case "hazard-perimeter":
      skeleton.geometry = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.hazard_class = "bushfire";
      skeleton.severity = "high";
      break;
    case "evacuation-route":
      skeleton.geometry = { points: [[1, 2], [3, 4]] };
      skeleton.status = "open";
      break;
    case "resource-pin":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.resource_id = "r1";
      skeleton.resource_kind = "fire-truck";
      skeleton.capability = "Type 3";
      break;
    case "evac-centre-pin":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.centre_id = "ec1";
      skeleton.capacity = 200;
      skeleton.occupancy = 50;
      break;
    case "utility-outage-zone":
      skeleton.geometry = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.utility = "power";
      skeleton.affected_premises = 1000;
      break;
    case "tc-track-and-cone":
      skeleton.track = { points: [[1, 2], [3, 4]] };
      skeleton.cone = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.category = 3;
      break;
    case "road-closure-and-alt-route":
      skeleton.closure = { points: [[1, 2], [3, 4]] };
      skeleton.reason = "flooding";
      break;
    case "vessel-or-aircraft-position":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.asset_id = "v1";
      skeleton.kind = "vessel";
      break;
    case "airspace-restriction":
      skeleton.geometry = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.altitude_m = 1000;
      skeleton.effective_from = "2026-05-08T00:00:00Z";
      skeleton.effective_to = "2026-05-09T00:00:00Z";
      break;
    case "maritime-exclusion":
      skeleton.geometry = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.effective_from = "2026-05-08T00:00:00Z";
      skeleton.effective_to = "2026-05-09T00:00:00Z";
      break;
    case "hospital-surge":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.hospital_id = "h1";
      skeleton.surge_status = "amber";
      break;
    case "remote-community-access":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.community_id = "c1";
      skeleton.access_status = "isolated";
      break;
    case "volunteer-staging":
      skeleton.position = { lng: 1, lat: 2 };
      skeleton.staging_id = "vs1";
      skeleton.current_volunteers = 12;
      break;
    case "geohazard-zone":
      skeleton.geometry = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.hazard = "landslide";
      break;
    case "flood-polygon":
      skeleton.geometry = { rings: [[[1, 2], [3, 4], [5, 6], [1, 2]]] };
      skeleton.depth_m_max = 1.5;
      break;
  }
  return skeleton as MapOverlayEvent;
}

describe("simulation-map dispatch (16 layer types)", () => {
  it("renders all 16 closed-set layer types without falling into assertNever", () => {
    expect(MAP_OVERLAY_LAYER_TYPES.length).toBe(16);
    for (const layer of MAP_OVERLAY_LAYER_TYPES) {
      const event = baseEvent(layer);
      const result = renderMapOverlayEvent(event);
      expect(result.feature).not.toBeNull();
      expect(result.layerType).toBe(layer);
      expect(result.feature!.properties.sim_badge).toBe("[SIMULATION]");
      expect(result.feature!.properties.title).toContain("[SIMULATION]");
    }
  });

  it("returns null feature for `map.overlay.removed`", () => {
    const event = { ...baseEvent("wind-arrow"), event_type: "map.overlay.removed" } as MapOverlayEvent;
    const result = renderMapOverlayEvent(event);
    expect(result.feature).toBeNull();
  });

  it("applyMapOverlayEvents drops removed overlays from the collection", () => {
    const created = baseEvent("hazard-perimeter");
    const removed = { ...created, event_type: "map.overlay.removed" } as MapOverlayEvent;
    const after = applyMapOverlayEvents(
      [] as SimulationOverlayFeature[],
      [created, removed],
    );
    expect(after).toEqual([]);
  });

  it("upserts overlays by overlay_id across created+updated", () => {
    const created = baseEvent("flood-polygon");
    const updated = { ...created, event_type: "map.overlay.updated" } as MapOverlayEvent;
    const after = applyMapOverlayEvents(
      [] as SimulationOverlayFeature[],
      [created, updated],
    );
    expect(after.length).toBe(1);
    expect(after[0].properties.layer_type).toBe("flood-polygon");
  });
});
