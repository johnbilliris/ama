import { getApiBaseUrl } from "@/lib/api/base-url";
import { simulationAuthHeaders } from "./simulation-auth";

const API_BASE_URL = getApiBaseUrl();

export const ALLOWED_WARP_SPEEDS = [1, 2, 5, 10, 24, 60] as const;
export type WarpSpeed = typeof ALLOWED_WARP_SPEEDS[number];

/**
 * Curated scenario packs shipped in
 * packages/domain/src/domain/seed/scenario_templates_australia.json.
 * The API exposes no template-listing endpoint, so the IDs are mirrored here
 * and validated server-side on seed (unknown IDs return an error).
 */
export const SCENARIO_TEMPLATES = [
  {
    template_id: "nsw-bushfire-multi-agency",
    name: "NSW Blue Mountains Bushfire — Multi-Agency",
    scenario_type: "Bushfire",
  },
  {
    template_id: "qld-cyclone-multi-agency",
    name: "QLD Cyclone — Multi-Agency",
    scenario_type: "Cyclone",
  },
  {
    template_id: "nsw-flood-riverine",
    name: "NSW Hawkesbury-Nepean Riverine Flood",
    scenario_type: "Flood",
  },
  {
    template_id: "cross-jurisdiction-bushfire",
    name: "VIC/NSW Border Bushfire — Cross-jurisdiction",
    scenario_type: "Cross-jurisdiction",
  },
] as const;

export interface SimulationSummary {
  tenant_id: string;
  scenario_type: string;
  status: string;
  created_at: string;
  participant_count: number;
  signal_count: number;
  storage_bytes: number;
  current_warp_speed?: number;
  playback_status?: string;
  clock_paused?: boolean;
}

export interface SimulationListResponse {
  simulations: SimulationSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface SimulationParticipantAssignment {
  oid: string;
  persona_id?: string | null;
  organisation_id?: string | null;
  jurisdiction_id?: string | null;
  role?: string | null;
}

export interface SimulationDetail {
  tenant_id: string;
  scenario_id: string;
  scenario_run_id: string;
  scenario_type: string;
  status: string;
  created_by: string;
  created_at: string;
  ttl_hours: number;
  expires_at: string;
  participants: string[];
  participant_assignments?: SimulationParticipantAssignment[];
  jurisdictions: string[];
  resource_limits: { max_signals: number; max_recommendations: number; max_duration_hours: number };
  // `cache_keys` is optional because the API omits it on older documents and
  // never reports a measured namespace count — the UI must not imply one.
  resource_consumption: {
    signal_count: number;
    recommendation_count: number;
    storage_bytes: number;
    cache_keys?: number | null;
  };
  throttle_mode: string;
  throttle_quota_pct: number;
  throttle_notice?: string | null;
  throttle_changed_at?: string | null;
  exercise_report_id?: string | null;
  exercise_report_uri?: string | null;
  elapsed_seconds: number;
  // Feature 026 — server-owned clock
  warp_speed?: number;
  current_warp_speed?: number;
  accumulated_sim_seconds?: number;
  current_sim_seconds?: number;
  clock_paused?: boolean;
  playback_status?: string;
  last_resumed_at?: string | null;
}

export interface ExerciseReportData {
  report_id: string;
  tenant_id: string;
  scenario_type: string;
  generated_at: string;
  exercise_timeline: { event_type: string; wall_clock_time: string; payload: Record<string, unknown> }[];
  participating_organisations: string[];
  participating_personas: string[];
  signal_summary: { total: number; by_category: Record<string, number>; by_source: Record<string, number> };
  recommendation_summary: { total: number; approved: number; rejected: number; escalated: number; timed_out: number; pending: number };
  alert_summary: { total: number; published: number; blocked_simulation: number };
  coordination_gaps: string[];
  performance_metrics: { time_to_first_recommendation_s: number | null; time_to_alert_publication_s: number | null; coordination_coverage_pct: number | null };
  benchmark_comparison: { metric: string; target: number; actual: number | null; passed: boolean; prior_actual: number | null; delta_from_prior: number | null }[];
}

export interface CreateSimulationPayload {
  scenario_type: string;
  jurisdictions: string[];
  participants: string[];
  scenario_template_id?: string;
  warp_speed?: number;
  resource_limits?: {
    max_signals?: number;
    max_recommendations?: number;
    max_duration_hours?: number;
  };
}

export interface CreateSimulationResponse {
  tenant_id: string;
  scenario_run_id: string;
  status: string;
  created_at: string;
  current_warp_speed?: number;
}

export interface SimulationTimerResponse {
  tenant_id: string;
  status: string;
  elapsed_seconds: number;
  accumulated_sim_seconds?: number;
  current_sim_seconds?: number;
  current_warp_speed?: number;
  clock_paused?: boolean;
  playback_status?: string;
}

export interface SimulationClockResponse {
  tenant_id: string;
  current_warp_speed: number;
  accumulated_sim_seconds: number;
  current_sim_seconds: number;
  clock_paused: boolean;
  playback_status: string;
  last_resumed_at: string | null;
  server_timestamp: string;
  delivery_lag_seconds?: number;
  warp_speed_history?: {
    previous_speed: number;
    new_speed: number;
    sim_time_offset: number;
    wall_timestamp: string;
    changed_by: string;
  }[];
}

export interface ChangeWarpSpeedResponse extends SimulationClockResponse {
  previous_warp_speed: number;
}

/** Carries the HTTP status so callers can tell 403 from 404 from 409. */
export class SimulationApiError extends Error {
  constructor(readonly status: number, readonly body: string) {
    super(`API ${status}: ${body}`);
    this.name = "SimulationApiError";
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const auth = await simulationAuthHeaders();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...auth, ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new SimulationApiError(response.status, body);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function createSimulation(payload: CreateSimulationPayload): Promise<CreateSimulationResponse> {
  return apiFetch<CreateSimulationResponse>("/simulations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listSimulations(
  status?: string,
  limit = 20,
  offset = 0,
): Promise<SimulationListResponse> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  return apiFetch<SimulationListResponse>(`/simulations?${params}`);
}

export async function getSimulation(tenantId: string): Promise<SimulationDetail> {
  return apiFetch<SimulationDetail>(`/simulations/${encodeURIComponent(tenantId)}`);
}

export async function pauseSimulation(tenantId: string): Promise<SimulationTimerResponse> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/pause`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function resumeSimulation(tenantId: string): Promise<SimulationTimerResponse> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/resume`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function archiveSimulation(tenantId: string): Promise<SimulationTimerResponse> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/archive`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getSimulationClock(tenantId: string): Promise<SimulationClockResponse> {
  return apiFetch<SimulationClockResponse>(
    `/simulations/${encodeURIComponent(tenantId)}/clock`,
  );
}

export async function changeWarpSpeed(
  tenantId: string,
  warpSpeed: number,
): Promise<ChangeWarpSpeedResponse> {
  return apiFetch<ChangeWarpSpeedResponse>(
    `/simulations/${encodeURIComponent(tenantId)}/warp-speed`,
    {
      method: "POST",
      body: JSON.stringify({ warp_speed: warpSpeed }),
    },
  );
}

export async function getAllowedWarpSpeeds(): Promise<{
  warp_speeds: number[];
  playback_speeds: number[];
  default_warp_speed: number;
}> {
  return apiFetch(`/simulations/meta/warp-speeds`);
}

export async function deleteSimulation(tenantId: string): Promise<void> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}`, { method: "DELETE" });
}

export async function seedSimulation(tenantId: string, templateId: string): Promise<{ status: string }> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/seed`, {
    method: "POST",
    body: JSON.stringify({ template_id: templateId }),
  });
}

export async function seedReplay(
  tenantId: string,
  incidentId: string,
  start: string,
  end: string,
): Promise<{ status: string }> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/seed/replay`, {
    method: "POST",
    body: JSON.stringify({ incident_id: incidentId, start, end }),
  });
}

export interface ParticipantAssignment {
  oid: string;
  persona?: string;
  organisation_id?: string;
  jurisdiction_id?: string;
  role?: string;
}

export async function addParticipants(
  tenantId: string,
  participants: ParticipantAssignment[],
): Promise<{ tenant_id: string; participants: string[] }> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/participants`, {
    method: "POST",
    body: JSON.stringify({ participants }),
  });
}

export async function getReport(tenantId: string): Promise<Record<string, unknown>> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/report`);
}

export async function getReportById(reportId: string): Promise<ExerciseReportData> {
  return apiFetch(`/simulations/reports/${encodeURIComponent(reportId)}`);
}
