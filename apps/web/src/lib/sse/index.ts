/**
 * Spec-036 T-I06 — typed SSE simulation event surface.
 *
 * Re-exports the map-overlay event union, plus the chat-turn / lifecycle /
 * sub-agent / signal SSE events that the simulation page consumes.
 *
 * Used by `simulation-chat-pane.tsx` (T-I01), `simulation-banner.tsx` (T-I07),
 * `simulation-map.tsx` (T-I04) and `useSseReconnect.ts` (T-I05).
 */

export {
  MAP_OVERLAY_LAYER_TYPES,
  type AirspaceRestrictionPayload,
  type EvacCentrePinPayload,
  type EvacuationRoutePayload,
  type FloodPolygonPayload,
  type GeohazardZonePayload,
  type HazardPerimeterPayload,
  type HospitalSurgePayload,
  type MapOverlayBaseEvent,
  type MapOverlayEvent,
  type MapOverlayEventType,
  type MapOverlayLayerPayload,
  type MapOverlayLayerType,
  type MaritimeExclusionPayload,
  type RemoteCommunityAccessPayload,
  type ResourcePinPayload,
  type RoadClosureAndAltRoutePayload,
  type TcTrackAndConePayload,
  type UtilityOutageZonePayload,
  type VesselOrAircraftPositionPayload,
  type VolunteerStagingPayload,
  type WindArrowPayload,
  assertNever,
} from "./map-overlay-events";

/* ----- chat / sub-agent / lifecycle events (FR-005, FR-007, FR-059) ----- */

export type ChatTurnEventType =
  | "turn.start"
  | "turn.delta"
  | "tool.call"
  | "tool.result"
  | "card.scenario"
  | "banner.throttle"
  | "turn.end";

/** Closed set of sub-agent role pills (FR-026). */
export type SubAgentRole =
  | "weather"
  | "logistics"
  | "communications"
  | "risk-assessment"
  | "resource-routing"
  | "decision-support";

export const SUB_AGENT_ROLES = [
  "weather",
  "logistics",
  "communications",
  "risk-assessment",
  "resource-routing",
  "decision-support",
] as const satisfies readonly SubAgentRole[];

export interface SubAgentReplyEvent {
  /** `sub_agent.reply` per FR-005 (T-B10 surface). */
  event_type: "sub_agent.reply";
  /** simulation tenant scope. */
  sim_id: string;
  /** thread id (stable per sub-agent role). */
  thread_id: string;
  /** Sub-agent role pill — closed set per FR-026 (6 roles). */
  role: SubAgentRole;
  /** Markdown body — must begin with `[SIMULATION] `. */
  reply_markdown: string;
  /** prompt-hash badge for governance review. */
  prompt_hash: string;
  /** ISO-8601 UTC. */
  timestamp: string;
}

export interface SubAgentThreadCapEvent {
  event_type: "sub_agent.thread_cap_exceeded";
  sim_id: string;
  attempted_role: string;
  active_threads: number;
  thread_cap: number;
  timestamp: string;
}

export type SubAgentEvent = SubAgentReplyEvent | SubAgentThreadCapEvent;

export type LifecycleEventType =
  | "lifecycle.scenario_started"
  | "lifecycle.scenario_paused"
  | "lifecycle.scenario_resumed"
  | "lifecycle.scenario_aborted"
  | "lifecycle.scenario_archived"
  | "lifecycle.scenario_completed";

export interface LifecycleEvent {
  event_type: LifecycleEventType;
  sim_id: string;
  reason?: string;
  actor?: string;
  timestamp: string;
}
