/**
 * Typed API client for /api/eval/*.
 *
 * AMA convention: native fetch with `cache: "no-store"` (no SWR/React Query). Server
 * components call these helpers directly; client components receive their data via props.
 *
 * Stub for T005 — full implementation lands in T037.
 */

export type EvalRunStatus = "queued" | "provisioning" | "running" | "succeeded" | "failed" | "cancelling" | "cancelled";

export type EvalRunMode = "ad-hoc" | "scheduled-baseline" | "pr-fast-subset" | "progressive-delivery-full";

export type EvalRunSummary = {
  runId: string;
  status: EvalRunStatus;
  mode: EvalRunMode;
  datasetId: string;
  datasetVersion: string;
  models: { modelId: string; version: string }[];
  startedAt: string | null;
  completedAt: string | null;
  changeRef?: string;
};

export type Scorecard = {
  runId: string;
  perModel: Record<string, Record<string, { mean: number; pass: boolean; regression?: number }>>;
  winner: { byMetric: Record<string, string>; overall: string | null };
  costAttributionAud: number;
  datasetVersion: string;
  baselineRunId: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    throw new Error(`eval api ${path} failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function listRuns(params?: { status?: EvalRunStatus; dataset?: string; since?: string; changeRef?: string }) {
  const qs = new URLSearchParams(Object.entries(params ?? {}).filter(([, v]) => v != null) as [string, string][]);
  const query = qs.toString();
  return fetchJson<{ runs: EvalRunSummary[] }>(`/api/eval/runs${query ? `?${query}` : ""}`);
}

export async function getRun(runId: string) {
  return fetchJson<EvalRunSummary>(`/api/eval/runs/${runId}`);
}

export async function getScorecard(runId: string) {
  return fetchJson<Scorecard>(`/api/eval/scorecards/${runId}`);
}

export async function cancelRun(runId: string) {
  return fetchJson<{ runId: string; status: EvalRunStatus }>(`/api/eval/runs/${runId}/cancel`, { method: "POST" });
}

export async function postRun(body: {
  datasetId: string;
  datasetVersion: string;
  models: { modelId: string; version: string }[];
  mode?: EvalRunMode;
  changeRef?: string;
  metricSetVersion?: string;
}) {
  return fetchJson<EvalRunSummary>(`/api/eval/runs`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}
