/**
 * Spec-036 T-I06 — typed SSE map-overlay event surface.
 *
 * Mirrors the closed set defined in
 * `specs/036-sim-agent-extend/contracts/sse-map-overlay.md §2`:
 *   - 6 event types (`map.overlay.{created,updated,stale,cluster,removed,batch}`)
 *   - 16 layer types (the FR-027 closed enum)
 *
 * The discriminated union below keeps the web client compile-time exhaustive:
 * any new layer added to the contract will surface as a TS error in the
 * `assertNever` branch of consumer code (see `simulation-map.tsx`).
 *
 * NOTE: the 16-entry list is normative — when the contract ever changes,
 * the schema (apps/api) and these types MUST be updated together.
 */

/** Closed set of map-overlay SSE event types (FR-027 / spec-036 contract §2). */
export type MapOverlayEventType =
  | "map.overlay.created"
  | "map.overlay.updated"
  | "map.overlay.stale"
  | "map.overlay.cluster"
  | "map.overlay.removed"
  | "map.overlay.batch";

/** Closed set of map-overlay layer types (FR-027 / spec-036 contract §2). */
export type MapOverlayLayerType =
  | "wind-arrow"
  | "hazard-perimeter"
  | "evacuation-route"
  | "resource-pin"
  | "evac-centre-pin"
  | "utility-outage-zone"
  | "tc-track-and-cone"
  | "road-closure-and-alt-route"
  | "vessel-or-aircraft-position"
  | "airspace-restriction"
  | "maritime-exclusion"
  | "hospital-surge"
  | "remote-community-access"
  | "volunteer-staging"
  | "geohazard-zone"
  | "flood-polygon";

/**
 * The 16 layer types as a literal tuple — the LENGTH of this tuple is
 * type-checked against the closed set above so the count never drifts.
 *
 * @see specs/036-sim-agent-extend/contracts/sse-map-overlay.md §2
 */
export const MAP_OVERLAY_LAYER_TYPES = [
  "wind-arrow",
  "hazard-perimeter",
  "evacuation-route",
  "resource-pin",
  "evac-centre-pin",
  "utility-outage-zone",
  "tc-track-and-cone",
  "road-closure-and-alt-route",
  "vessel-or-aircraft-position",
  "airspace-restriction",
  "maritime-exclusion",
  "hospital-surge",
  "remote-community-access",
  "volunteer-staging",
  "geohazard-zone",
  "flood-polygon",
] as const satisfies readonly MapOverlayLayerType[];

// Compile-time guard — if the array goes out of sync with the union the
// `[number]` index lookup will widen and the assignment below will error.
type _LayerTypesAreClosed =
  (typeof MAP_OVERLAY_LAYER_TYPES)[number] extends MapOverlayLayerType
    ? MapOverlayLayerType extends (typeof MAP_OVERLAY_LAYER_TYPES)[number]
      ? true
      : false
    : false;
const _LAYER_TYPES_ARE_CLOSED: _LayerTypesAreClosed = true;
void _LAYER_TYPES_ARE_CLOSED;

export interface MapOverlayBaseEvent {
  /** Discriminator. */
  event_type: MapOverlayEventType;
  /** Simulation tenant scope. */
  sim_id: string;
  /** Stable identifier for the overlay across created/updated/removed. */
  overlay_id: string;
  /** Source synthetic signal that produced this overlay (FR-028). */
  signal_id?: string;
  /** [SIMULATION] watermark required by FR-058. */
  sim_badge: "[SIMULATION]";
  /** Render-time visual hint (e.g. dashed outline, half-opacity). */
  visual_modifier: string;
  /** ISO-8601 UTC. */
  timestamp: string;
  /** Origin cascade chain id for FR-031 affinity tracking. */
  origin_cascade_id?: string;
}

/* ------------------------------------------------------------------ */
/* Layer-typed payload bodies — one branch per FR-027 layer type.     */
/* Each branch carries the minimum geometry / property bag required by */
/* the deployed `simulation-map` layer renderer (T-I04).                */
/* ------------------------------------------------------------------ */

interface PointLike {
  lng: number;
  lat: number;
}

interface PolygonLike {
  rings: Array<Array<[number, number]>>;
}

interface PolylineLike {
  points: Array<[number, number]>;
}

export interface WindArrowPayload {
  layer_type: "wind-arrow";
  position: PointLike;
  bearing_deg: number;
  speed_kmh: number;
}

export interface HazardPerimeterPayload {
  layer_type: "hazard-perimeter";
  geometry: PolygonLike;
  hazard_class: string;
  severity: "low" | "moderate" | "high" | "extreme";
}

export interface EvacuationRoutePayload {
  layer_type: "evacuation-route";
  geometry: PolylineLike;
  status: "open" | "congested" | "closed";
}

export interface ResourcePinPayload {
  layer_type: "resource-pin";
  position: PointLike;
  resource_id: string;
  resource_kind: string;
  capability: string;
}

export interface EvacCentrePinPayload {
  layer_type: "evac-centre-pin";
  position: PointLike;
  centre_id: string;
  capacity: number;
  occupancy: number;
}

export interface UtilityOutageZonePayload {
  layer_type: "utility-outage-zone";
  geometry: PolygonLike;
  utility: "power" | "water" | "telecom" | "gas";
  affected_premises: number;
}

export interface TcTrackAndConePayload {
  layer_type: "tc-track-and-cone";
  track: PolylineLike;
  cone: PolygonLike;
  category: 1 | 2 | 3 | 4 | 5;
}

export interface RoadClosureAndAltRoutePayload {
  layer_type: "road-closure-and-alt-route";
  closure: PolylineLike;
  alt_route?: PolylineLike;
  reason: string;
}

export interface VesselOrAircraftPositionPayload {
  layer_type: "vessel-or-aircraft-position";
  position: PointLike;
  asset_id: string;
  kind: "vessel" | "fixed-wing" | "rotary-wing";
  heading_deg?: number;
}

export interface AirspaceRestrictionPayload {
  layer_type: "airspace-restriction";
  geometry: PolygonLike;
  altitude_m: number;
  effective_from: string;
  effective_to: string;
}

export interface MaritimeExclusionPayload {
  layer_type: "maritime-exclusion";
  geometry: PolygonLike;
  effective_from: string;
  effective_to: string;
}

export interface HospitalSurgePayload {
  layer_type: "hospital-surge";
  position: PointLike;
  hospital_id: string;
  surge_status: "green" | "amber" | "red";
}

export interface RemoteCommunityAccessPayload {
  layer_type: "remote-community-access";
  position: PointLike;
  community_id: string;
  access_status: "isolated" | "limited" | "open";
}

export interface VolunteerStagingPayload {
  layer_type: "volunteer-staging";
  position: PointLike;
  staging_id: string;
  current_volunteers: number;
}

export interface GeohazardZonePayload {
  layer_type: "geohazard-zone";
  geometry: PolygonLike;
  hazard: "landslide" | "rockfall" | "subsidence" | "tsunami";
}

export interface FloodPolygonPayload {
  layer_type: "flood-polygon";
  geometry: PolygonLike;
  depth_m_max: number;
}

export type MapOverlayLayerPayload =
  | WindArrowPayload
  | HazardPerimeterPayload
  | EvacuationRoutePayload
  | ResourcePinPayload
  | EvacCentrePinPayload
  | UtilityOutageZonePayload
  | TcTrackAndConePayload
  | RoadClosureAndAltRoutePayload
  | VesselOrAircraftPositionPayload
  | AirspaceRestrictionPayload
  | MaritimeExclusionPayload
  | HospitalSurgePayload
  | RemoteCommunityAccessPayload
  | VolunteerStagingPayload
  | GeohazardZonePayload
  | FloodPolygonPayload;

export type MapOverlayEvent = MapOverlayBaseEvent & MapOverlayLayerPayload;

/**
 * Exhaustiveness helper — placed at the end of `switch` / `if-else` chains
 * over `MapOverlayLayerType`. Adding a new layer to the closed set without
 * updating consumers will surface as a compile error here.
 */
export function assertNever(value: never): never {
  throw new Error(
    `Unreachable: unexpected value ${JSON.stringify(value)}. ` +
      `If you just added a new layer_type, update every consumer of MapOverlayLayerType.`,
  );
}
