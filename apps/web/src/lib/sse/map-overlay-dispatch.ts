/**
 * Spec-036 T-I04 — typed dispatch for the 16 SSE map-overlay layer types.
 *
 * Stand-alone helper consumed by `simulation-map.tsx`. Given a
 * `MapOverlayEvent`, returns a renderable GeoJSON feature (or `null` for
 * `removed` events). The `switch` block uses `assertNever` so the
 * exhaustiveness check fires at compile time the moment a new layer is
 * added to the closed set.
 */
import {
  assertNever,
  type MapOverlayEvent,
  type MapOverlayLayerType,
} from "@/lib/sse/map-overlay-events";

/* eslint-disable @typescript-eslint/no-explicit-any */

/** Minimal GeoJSON feature shape — geometry differs per layer_type. */
export interface SimulationOverlayFeature {
  type: "Feature";
  id: string;
  geometry:
    | { type: "Point"; coordinates: [number, number] }
    | { type: "LineString"; coordinates: Array<[number, number]> }
    | { type: "Polygon"; coordinates: Array<Array<[number, number]>> };
  properties: {
    incident_id: string;
    title: string;
    incident_type: string;
    layer_type: MapOverlayLayerType;
    sim_badge: "[SIMULATION]";
    visual_modifier: string;
    status: string;
    severity: string;
    severity_tier: "emergency";
    started_at: string;
    pprr_phase: "response";
    incident_level: 3;
    /**
     * Spec-036 T-R07 — wind-arrow extras carried into the feature
     * properties so accessible UI surfaces (sim-overlay-wind-list)
     * can render the canonical "wind direction has changed" callout
     * with bearing and speed text. Other layers leave these
     * undefined; consumers MUST treat them as optional.
     */
    bearing_deg?: number;
    speed_kmh?: number;
  };
}

interface OverlayRenderResult {
  feature: SimulationOverlayFeature | null;
  layerType: MapOverlayLayerType;
  visualModifier: string;
}

/**
 * The category-key returned for each layer aligns with the PIN_DEFS in
 * packages/ui marker-cluster.tsx so the renderer can pick an icon. Values
 * that don't have a dedicated pin fall back to "other".
 */
function pinForLayer(layer: MapOverlayLayerType): string {
  switch (layer) {
    case "wind-arrow":
    case "tc-track-and-cone":
      return "cyclone";
    case "hazard-perimeter":
      return "bushfire";
    case "evacuation-route":
    case "evac-centre-pin":
      return "evacuation";
    case "resource-pin":
    case "volunteer-staging":
      return "resource";
    case "utility-outage-zone":
      return "utility";
    case "road-closure-and-alt-route":
    case "vessel-or-aircraft-position":
    case "airspace-restriction":
    case "maritime-exclusion":
    case "remote-community-access":
      return "transport";
    case "hospital-surge":
      return "health";
    case "geohazard-zone":
      return "landslide";
    case "flood-polygon":
      return "flood";
    default:
      return assertNever(layer);
  }
}

export function renderMapOverlayEvent(
  event: MapOverlayEvent,
): OverlayRenderResult {
  if (event.event_type === "map.overlay.removed") {
    return {
      feature: null,
      layerType: event.layer_type,
      visualModifier: event.visual_modifier,
    };
  }

  const id = `sim-overlay-${event.overlay_id}`;
  const baseProps: SimulationOverlayFeature["properties"] = {
    incident_id: id,
    title: `[SIMULATION] ${event.layer_type}`,
    incident_type: pinForLayer(event.layer_type),
    layer_type: event.layer_type,
    sim_badge: "[SIMULATION]",
    visual_modifier: event.visual_modifier,
    status:
      event.event_type === "map.overlay.stale" ? "closed" : "active",
    severity: "critical",
    severity_tier: "emergency",
    started_at: event.timestamp,
    pprr_phase: "response",
    incident_level: 3,
  };

  let feature: SimulationOverlayFeature;
  switch (event.layer_type) {
    case "wind-arrow":
    case "resource-pin":
    case "evac-centre-pin":
    case "vessel-or-aircraft-position":
    case "hospital-surge":
    case "remote-community-access":
    case "volunteer-staging": {
      const pos = (event as any).position as { lng: number; lat: number };
      // T-R07 — wind-arrow carries bearing + speed into properties so
      // accessible UI surfaces can describe wind change callouts.
      const layerExtras: Partial<SimulationOverlayFeature["properties"]> = {};
      if (event.layer_type === "wind-arrow") {
        layerExtras.bearing_deg = (event as any).bearing_deg;
        layerExtras.speed_kmh = (event as any).speed_kmh;
      }
      feature = {
        type: "Feature",
        id,
        geometry: { type: "Point", coordinates: [pos.lng, pos.lat] },
        properties: { ...baseProps, ...layerExtras },
      };
      break;
    }
    case "evacuation-route": {
      const points = (event as any).geometry.points as Array<[number, number]>;
      feature = {
        type: "Feature",
        id,
        geometry: { type: "LineString", coordinates: points },
        properties: baseProps,
      };
      break;
    }
    case "road-closure-and-alt-route": {
      const points = (event as any).closure.points as Array<[number, number]>;
      feature = {
        type: "Feature",
        id,
        geometry: { type: "LineString", coordinates: points },
        properties: baseProps,
      };
      break;
    }
    case "tc-track-and-cone": {
      const points = (event as any).track.points as Array<[number, number]>;
      feature = {
        type: "Feature",
        id,
        geometry: { type: "LineString", coordinates: points },
        properties: baseProps,
      };
      break;
    }
    case "hazard-perimeter":
    case "utility-outage-zone":
    case "airspace-restriction":
    case "maritime-exclusion":
    case "geohazard-zone":
    case "flood-polygon": {
      const rings = (event as any).geometry.rings as Array<
        Array<[number, number]>
      >;
      feature = {
        type: "Feature",
        id,
        geometry: { type: "Polygon", coordinates: rings },
        properties: baseProps,
      };
      break;
    }
    default:
      return assertNever(event);
  }

  return {
    feature,
    layerType: event.layer_type,
    visualModifier: event.visual_modifier,
  };
}

/** Apply a stream of overlay events to the existing local feature collection. */
export function applyMapOverlayEvents(
  current: SimulationOverlayFeature[],
  events: MapOverlayEvent[],
): SimulationOverlayFeature[] {
  const byId = new Map<string, SimulationOverlayFeature>();
  for (const f of current) byId.set(f.id, f);
  for (const event of events) {
    const id = `sim-overlay-${event.overlay_id}`;
    const result = renderMapOverlayEvent(event);
    if (result.feature === null) {
      byId.delete(id);
    } else {
      byId.set(id, result.feature);
    }
  }
  return Array.from(byId.values());
}
