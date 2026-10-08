import { getApiBaseUrl } from "@/lib/api/base-url";
/**
 * Workflow Runs API client (T052).
 *
 * Backed by `apps/api/app/api/routes/workflow_runs.py`. All requests use
 * `cache: "no-store"` per the AMA repo convention for operator data.
 */

const API_BASE_URL = getApiBaseUrl();

export type WorkflowRunStatus =
  | "Running"
  | "AwaitingApproval"
  | "NeedsOperatorDecision"
  | "Completed"
  | "Failed"
  | "Cancelled"
  | "Superseded";

export interface WorkflowRun {
  id: string;
  run_id: string;
  incident_id: string;
  status: WorkflowRunStatus;
  is_active: boolean;
  current_step: string;
  last_checkpoint_id: string | null;
  prior_run_id: string | null;
  pending_request_id: string | null;
  failure_reason: Record<string, unknown> | null;
  terminal_at: string | null;
  started_at: string;
  last_step_at: string;
  created_by: string;
  tenant_id: string;
}

export interface ListResponse {
  items: WorkflowRun[];
  continuation: string | null;
}

export interface ListFilters {
  incident_id?: string;
  status?: WorkflowRunStatus[];
  tenant_id?: string;
  limit?: number;
}

function _qs(filters: ListFilters): string {
  const p = new URLSearchParams();
  if (filters.incident_id) p.set("incident_id", filters.incident_id);
  if (filters.tenant_id) p.set("tenant_id", filters.tenant_id);
  if (filters.limit !== undefined) p.set("limit", String(filters.limit));
  for (const s of filters.status ?? []) p.append("status", s);
  return p.toString() ? `?${p.toString()}` : "";
}

export async function listRuns(filters: ListFilters = {}): Promise<ListResponse> {
  const r = await fetch(`${API_BASE_URL}/workflow_runs${_qs(filters)}`, {
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`listRuns failed: ${r.status}`);
  return r.json();
}

export async function getRun(runId: string): Promise<WorkflowRun> {
  const r = await fetch(`${API_BASE_URL}/workflow_runs/${runId}`, {
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`getRun failed: ${r.status}`);
  return r.json();
}

export interface CheckpointSummary {
  id: string;
  run_id: string;
  sequence: number;
  step_name: string;
  taken_at: string;
}

export async function listCheckpoints(runId: string): Promise<CheckpointSummary[]> {
  const r = await fetch(`${API_BASE_URL}/workflow_runs/${runId}/checkpoints`, {
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`listCheckpoints failed: ${r.status}`);
  const body = (await r.json()) as { items: CheckpointSummary[] };
  return body.items;
}

export interface AuditEntrySummary {
  id: string;
  agent_name: string;
  step_name: string;
  outcome: string;
  started_at: string;
  ended_at: string;
  failure_reason: string | null;
}

export async function listAudit(
  runId: string,
  opts: { agent?: string; outcome?: string; limit?: number } = {}
): Promise<AuditEntrySummary[]> {
  const p = new URLSearchParams();
  if (opts.agent) p.set("agent", opts.agent);
  if (opts.outcome) p.set("outcome", opts.outcome);
  if (opts.limit !== undefined) p.set("limit", String(opts.limit));
  const qs = p.toString() ? `?${p.toString()}` : "";
  const r = await fetch(`${API_BASE_URL}/workflow_runs/${runId}/audit${qs}`, {
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`listAudit failed: ${r.status}`);
  const body = (await r.json()) as { items: AuditEntrySummary[] };
  return body.items;
}

export async function cancelRun(
  runId: string,
  reason: string
): Promise<WorkflowRun> {
  const r = await fetch(`${API_BASE_URL}/workflow_runs/${runId}/cancel`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  if (!r.ok) throw new Error(`cancelRun failed: ${r.status}`);
  return r.json();
}

export interface ApprovalGateMetrics {
  window: string;
  mtta_seconds: number;
  approvals: number;
  modifications: number;
  rejections: number;
  escalations: number;
  timeouts: number;
}

export type ApprovalGateWindow = "1h" | "24h" | "7d" | "30d";

export async function getApprovalGateMetrics(
  window: ApprovalGateWindow = "24h"
): Promise<ApprovalGateMetrics> {
  const r = await fetch(
    `${API_BASE_URL}/workflow_runs/metrics/approval-gate?window=${window}`,
    { cache: "no-store" }
  );
  if (!r.ok) throw new Error(`getApprovalGateMetrics failed: ${r.status}`);
  return r.json();
}
