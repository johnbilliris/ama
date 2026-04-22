const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export interface SimulationSummary {
  tenant_id: string;
  scenario_type: string;
  status: string;
  created_at: string;
  participant_count: number;
  signal_count: number;
  storage_bytes: number;
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
  last_resumed_at: string | null;
  paused_at: string | null;
  current_elapsed_seconds: number;
}

export interface CreateSimulationPayload {
  scenario_type: string;
  jurisdictions: string[];
  participants: string[];
  scenario_template_id?: string;
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
}

export interface SimulationTimerResponse {
  tenant_id: string;
  status: string;
  elapsed_seconds: number;
  last_resumed_at: string | null;
  paused_at: string | null;
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
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/pause`, { method: "POST" });
}

export async function resumeSimulation(tenantId: string): Promise<SimulationTimerResponse> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/resume`, { method: "POST" });
}

export async function archiveSimulation(tenantId: string): Promise<{ tenant_id: string; status: string }> {
  return apiFetch(`/simulations/${encodeURIComponent(tenantId)}/archive`, { method: "POST" });
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
