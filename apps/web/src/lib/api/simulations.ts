const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export const ALLOWED_WARP_SPEEDS = [1, 2, 5, 10, 24, 60] as const;
export type WarpSpeed = typeof ALLOWED_WARP_SPEEDS[number];

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
  jurisdictions: string[];
  resource_limits: { max_signals: number; max_recommendations: number; max_duration_hours: number };
  resource_consumption: { signal_count: number; recommendation_count: number; storage_bytes: number; cache_keys: number };
  throttle_mode: string;
  throttle_quota_pct: number;
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

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
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

export async function addParticipants(
  tenantId: string,
  participants: { oid: string; persona: string }[],
): Promise<{ tenant_id: string; participants: string[] }> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/participants`, {
    method: "POST",
    body: JSON.stringify({ participants }),
  });
}

export async function getReport(tenantId: string): Promise<Record<string, unknown>> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/report`);
}
